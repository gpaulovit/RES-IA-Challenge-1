"""Calibra os limites da RN-05 no benchmark (RNF-04, RNF-05) e relata os casos de negação (RN-06).

Regra de escolha (fixada antes de rodar com a base real):
1. Restrições:
   a. no máximo 2 dos 32 controles caem em `ja_checado` (RNF-05);
   b. no máximo 8 dos 32 controles (25%) recebem alguma checagem (`ja_checado` + `relacionada`).
      Contar só `relacionada` deixaria a regra "cumprir" o teto empurrando controles para
      `ja_checado`, que é pior. Esse é um critério interno da
      frente de Modelos, não um requisito: sem ele, o limite médio desce até o bot mostrar uma
      checagem sem relação para quase toda notícia real (26 de 32 no teste de fumaça com o
      FactPolCheckBr). Impacto: o limite médio sobe, e menos reescritas têm a checagem certa
      mostrada. O custo aparece na coluna `reescritas_mostradas`.
2. Maximiza: reescritas (gíria, apelido, erro ortográfico, recorrência temporal) em que a checagem
   certa aparece no top-3 **e é mostrada** ao usuário (faixa `ja_checado` ou `relacionada`).
3. Desempates, nesta ordem: mais casos `match_confirmado` em `ja_checado`; limite alto maior;
   limite médio maior (na dúvida, o mais conservador).

O top-3 (RNF-04) não depende dos limites: é relatado à parte. A checagem certa é achada pelo
texto da alegação, normalizado (sem "#boato", caixa, acento e pontuação). Uma alegação de
referência que não está na base é relatada como "alvo ausente" e conta como erro.

Saídas:
- results/calibracao_camada1.csv: uma linha por par de limites da grade.
- results/calibracao_camada1_casos.csv: os 62 casos com o par escolhido, para revisão linha a linha.
- com --gravar, o par escolhido vai para params.yaml.

Uso (a partir da raiz):  .venv/bin/python experiments/calibrar_limiares.py [--gravar]
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

import camada1
from reescrita import tirar_acento

RAIZ = camada1.RAIZ
BENCHMARK = RAIZ / "data" / "testes_benchmark.json"
RESULTADOS = Path(__file__).resolve().parent / "results"
REESCRITAS = {"giria", "apelido", "erro_ortografico", "recorrencia_temporal"}
MAX_CONTROLES_JA_CHECADO = 2   # RNF-05
MAX_CONTROLES_MOSTRADOS = 8    # critério interno (25% dos 32 controles); ver regra 1b no topo
META_TOP3 = 0.70               # RNF-04
K = 3


def chave(texto: str) -> str:
    t = tirar_acento(re.sub(r"#\w+", " ", texto)).lower()
    return " ".join(re.sub(r"[^\w\s]", " ", t).split())


def preparar(buscador: camada1.Buscador, casos: list[dict]) -> pd.DataFrame:
    """Uma linha por caso: semelhança do 1º colocado, posição e semelhança da checagem certa."""
    S = buscador.semelhancas([c["texto_testado"] for c in casos])
    chaves = np.array([chave(r["alegacao"]) for r in buscador.registros])
    linhas = []
    for c, s in zip(casos, S):
        topo = int(np.argmax(s))
        linha = {"id_teste": c["id_teste"], "tipo": c["tipo"], "esperado": c["resultado_esperado"],
                 "texto": c["texto_testado"], "s_topo": float(s[topo]),
                 "alegacao_topo": buscador.registros[topo]["alegacao"],
                 "negacao_diverge_topo": camada1.tem_negacao(c["texto_testado"])
                                         != camada1.tem_negacao(buscador.registros[topo]["alegacao"]),
                 "posicao_certa": np.nan, "s_certa": np.nan, "alvo_ausente": False}
        if c["alegacao_ref_original"]:
            certas = np.flatnonzero(chaves == chave(c["alegacao_ref_original"]))
            if len(certas):
                melhor = certas[np.argmax(s[certas])]
                linha["posicao_certa"] = int((s > s[melhor]).sum()) + 1
                linha["s_certa"] = float(s[melhor])
            else:
                linha["alvo_ausente"] = True
        linhas.append(linha)
    return pd.DataFrame(linhas)


def avaliar(d: pd.DataFrame, alta: float, media: float) -> dict:
    controles = d[d["tipo"] == "controle_falso_positivo"]
    reescritas = d[d["tipo"].isin(REESCRITAS)]
    negacao = d[d["tipo"] == "negacao"]
    ja_checado = (d["s_topo"] >= alta) & ~d["negacao_diverge_topo"]
    top3 = reescritas["posicao_certa"] <= K
    mostrada = top3 & (reescritas["s_certa"] >= media)
    confirmados = reescritas["esperado"] == "match_confirmado"
    certa_ja_checado = top3 & (reescritas["s_certa"] >= alta) & (reescritas["posicao_certa"] == 1)
    return {
        "limite_alta": round(alta, 2), "limite_media": round(media, 2),
        "controles_ja_checado": int(ja_checado[controles.index].sum()),
        "controles_relacionada": int(((controles["s_topo"] >= media) & ~ja_checado[controles.index]).sum()),
        "controles_mostrados": int((controles["s_topo"] >= media).sum()),
        "reescritas_top3": round(float(top3.mean()), 4),
        "reescritas_mostradas": round(float(mostrada.mean()), 4),
        "confirmados_ja_checado": int((certa_ja_checado & confirmados).sum()),
        "negacao_ja_checado": int(ja_checado[negacao.index].sum()),
    }


def grade(d: pd.DataFrame) -> pd.DataFrame:
    pares = [(a / 100, m / 100) for a in range(60, 100) for m in range(40, a + 1)]
    return pd.DataFrame([avaliar(d, a, m) for a, m in pares])


def escolher(g: pd.DataFrame, max_mostrados: int | None = MAX_CONTROLES_MOSTRADOS) -> pd.Series | None:
    """Regra do topo do arquivo. `max_mostrados=None` tira o teto da regra 1b (só para comparação)."""
    validos = g[g["controles_ja_checado"] <= MAX_CONTROLES_JA_CHECADO]
    if max_mostrados is not None:
        validos = validos[validos["controles_mostrados"] <= max_mostrados]
    if validos.empty:
        return None
    ordem = ["reescritas_mostradas", "confirmados_ja_checado", "limite_alta", "limite_media"]
    return validos.sort_values(ordem, ascending=False).iloc[0]


def casos_com_faixa(d: pd.DataFrame, alta: float, media: float) -> pd.DataFrame:
    """Mesma regra de camada1.faixa(), aplicada ao 1º colocado de cada caso."""
    d = d.copy()
    ja = (d["s_topo"] >= alta) & ~d["negacao_diverge_topo"]
    d["faixa_topo"] = np.select([ja, d["s_topo"] >= media], ["ja_checado", "relacionada"], "baixa")
    return d


def gravar_params(alta: float, media: float, caminho: Path = camada1.PARAMS_PADRAO) -> None:
    texto = caminho.read_text(encoding="utf-8")
    texto = re.sub(r"(limite_alta:\s*)[\d.]+", rf"\g<1>{alta:.2f}", texto)
    texto = re.sub(r"(limite_media:\s*)[\d.]+", rf"\g<1>{media:.2f}", texto)
    caminho.write_text(texto, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--indice", type=Path, default=camada1.INDICE_PADRAO)
    parser.add_argument("--saida", type=Path, default=RESULTADOS)
    parser.add_argument("--gravar", action="store_true", help="grava o par escolhido em params.yaml")
    a = parser.parse_args()

    casos = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    vetores, registros = camada1.carregar_indice(a.indice)
    d = preparar(camada1.Buscador(vetores, registros, 1.0, 0.0), casos)
    g = grade(d)
    a.saida.mkdir(parents=True, exist_ok=True)
    g.to_csv(a.saida / "calibracao_camada1.csv", index=False)

    ausentes = d.loc[d["alvo_ausente"], "id_teste"].tolist()
    top3 = g["reescritas_top3"].iloc[0]
    print(f"Base: {len(registros)} checagens. Alvos ausentes da base: {ausentes or 'nenhum'}")
    print(f"RNF-04 top-3 nas {d['tipo'].isin(REESCRITAS).sum()} reescritas: {top3:.0%} "
          f"(meta ≥ {META_TOP3:.0%}) → {'atende' if top3 >= META_TOP3 else 'NÃO atende'}")
    par = escolher(g)
    if par is None:
        print(f"Nenhum par de limites deixa ≤ {MAX_CONTROLES_JA_CHECADO} controles em 'ja_checado' (RNF-05) "
              f"e ≤ {MAX_CONTROLES_MOSTRADOS} com alguma checagem mostrada (critério interno).")
        return
    alta, media = float(par["limite_alta"]), float(par["limite_media"])
    casos_com_faixa(d, alta, media).to_csv(a.saida / "calibracao_camada1_casos.csv", index=False)
    print(f"Par escolhido: alta {alta:.2f}, média {media:.2f}")
    print(par.to_string())
    # Custo do teto: o melhor par só com a RNF-05, para comparação
    sem_teto = escolher(g, max_mostrados=None)
    print(f"Sem o teto: {sem_teto['reescritas_mostradas']:.0%} das reescritas com a checagem certa mostrada, "
          f"{int(sem_teto['controles_mostrados'])} de 32 notícias reais com checagem sem relação. "
          f"Com o teto: {par['reescritas_mostradas']:.0%} e {int(par['controles_mostrados'])}.")
    if a.gravar:
        gravar_params(alta, media)
        print("params.yaml atualizado.")


if __name__ == "__main__":
    main()
