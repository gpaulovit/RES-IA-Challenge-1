"""Avaliação automatizada e reproduzível do benchmark de recuperação semântica (MLOps)."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

from checagens.embeddings import criar_gerador
from checagens.retrieval import carregar_indice

BENCHMARK_PADRAO = Path("data/testes_benchmark.json")
INDICE_PADRAO = Path("data/indices/experimental")
RELATORIO_PADRAO = Path("data/relatorios/avaliacao-benchmark.json")


def _calcular_hash(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def carregar_benchmark(caminho: Path) -> list[dict]:
    """Lê e valida o conjunto de testes de benchmark."""
    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    except OSError as erro:
        raise ValueError(f"Não foi possível ler o arquivo de benchmark: {caminho}") from erro
    except (json.JSONDecodeError, UnicodeError) as erro:
        raise ValueError("O benchmark deve ser um JSON válido em UTF-8.") from erro

    if not isinstance(conteudo, list) or not conteudo:
        raise ValueError("O benchmark deve ser uma lista não vazia de casos de teste.")

    ids = set()
    for item in conteudo:
        if not isinstance(item, dict):
            raise ValueError("Cada caso de teste deve ser um objeto JSON.")
        id_teste = item.get("id_teste")
        if id_teste is None or id_teste in ids:
            raise ValueError(f"id_teste inválido ou repetido: {id_teste}")
        ids.add(id_teste)

        texto = item.get("texto_testado")
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError(f"Caso {id_teste} não contém 'texto_testado' válido.")

        tipo = item.get("tipo")
        if not isinstance(tipo, str) or not tipo.strip():
            raise ValueError(f"Caso {id_teste} não contém 'tipo' válido.")

        esperado = item.get("resultado_esperado")
        if esperado not in ("sem_match", "match_confirmado", "match_provavel"):
            raise ValueError(f"Caso {id_teste} contém 'resultado_esperado' inválido: {esperado}")

        ref = item.get("alegacao_ref_original")
        if ref is not None and (not isinstance(ref, str) or not ref.strip()):
            raise ValueError(f"Caso {id_teste} contém 'alegacao_ref_original' em formato inválido.")

    return conteudo


def avaliar_benchmark(
    benchmark: list[dict],
    vetores,
    metadados: list[dict],
    gerador,
    manifesto: dict,
    top_k: int = 5,
    benchmark_hash: str | None = None,
) -> dict:
    """Executa o benchmark sobre os vetores do índice e calcula métricas de recuperação."""
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    inicio_total = perf_counter()
    resultados = []
    tempos_ms = []

    for caso in benchmark:
        inicio_caso = perf_counter()
        texto = caso["texto_testado"].strip()
        ref = caso.get("alegacao_ref_original")

        consulta = np.asarray(gerador.gerar([texto]), dtype="float32")
        pontuacoes = cosine_similarity(consulta, vetores)[0]
        ordem = sorted(
            range(len(metadados)),
            key=lambda i: (-float(pontuacoes[i]), metadados[i]["id"]),
        )

        duracao_caso_ms = (perf_counter() - inicio_caso) * 1000
        tempos_ms.append(duracao_caso_ms)

        primeiro_idx = ordem[0]
        primeiro = {
            "id": metadados[primeiro_idx]["id"],
            "texto_indexado": metadados[primeiro_idx]["texto_indexado"],
            "pontuacao": round(float(pontuacoes[primeiro_idx]), 4),
        }

        posicao_ref = None
        pontuacao_ref = None
        if ref:
            for rank, idx in enumerate(ordem[:top_k], start=1):
                if metadados[idx]["texto_indexado"] == ref:
                    posicao_ref = rank
                    pontuacao_ref = round(float(pontuacoes[idx]), 4)
                    break

        resultados.append({
            "id_teste": caso["id_teste"],
            "tipo": caso["tipo"],
            "texto_testado": texto,
            "alegacao_ref_original": ref,
            "resultado_esperado": caso["resultado_esperado"],
            "posicao_referencia": posicao_ref,
            "pontuacao_referencia": pontuacao_ref,
            "primeiro_candidato": primeiro,
            "acertou_top_1": posicao_ref == 1,
            "acertou_top_k": posicao_ref is not None and posicao_ref <= top_k,
        })

    # Métricas para casos positivos (que possuem referência esperada)
    positivos = [r for r in resultados if r["alegacao_ref_original"] is not None]
    negativos = [r for r in resultados if r["alegacao_ref_original"] is None]

    recall_1 = round(mean(1 if r["posicao_referencia"] == 1 else 0 for r in positivos), 4) if positivos else None
    recall_3 = round(mean(1 if r["posicao_referencia"] and r["posicao_referencia"] <= 3 else 0 for r in positivos), 4) if positivos else None
    recall_5 = round(mean(1 if r["posicao_referencia"] and r["posicao_referencia"] <= 5 else 0 for r in positivos), 4) if positivos else None
    mrr = round(mean(1 / r["posicao_referencia"] if r["posicao_referencia"] else 0 for r in positivos), 4) if positivos else None

    # Métricas agrupadas por tipo/categoria
    tipos = sorted({r["tipo"] for r in resultados})
    metricas_por_tipo = {}

    for tipo in tipos:
        grupo = [r for r in resultados if r["tipo"] == tipo]
        grupo_pos = [r for r in grupo if r["alegacao_ref_original"] is not None]
        pontuacoes_topo = [r["primeiro_candidato"]["pontuacao"] for r in grupo]

        metricas_tipo = {
            "total_casos": len(grupo),
            "pontuacao_topo_media": round(mean(pontuacoes_topo), 4) if pontuacoes_topo else 0.0,
        }

        if grupo_pos:
            metricas_tipo["recall_1"] = round(mean(1 if r["posicao_referencia"] == 1 else 0 for r in grupo_pos), 4)
            metricas_tipo["recall_3"] = round(mean(1 if r["posicao_referencia"] and r["posicao_referencia"] <= 3 else 0 for r in grupo_pos), 4)
            metricas_tipo["recall_5"] = round(mean(1 if r["posicao_referencia"] and r["posicao_referencia"] <= 5 else 0 for r in grupo_pos), 4)
            metricas_tipo["mrr"] = round(mean(1 / r["posicao_referencia"] if r["posicao_referencia"] else 0 for r in grupo_pos), 4)

        metricas_por_tipo[tipo] = metricas_tipo

    tempo_total_segundos = round(perf_counter() - inicio_total, 3)

    return {
        "metadata_mlops": {
            "data_execucao_utc": datetime.now(timezone.utc).isoformat(),
            "modelo": manifesto.get("modelo"),
            "dimensoes": manifesto.get("dimensoes"),
            "quantidade_vetores_indice": len(metadados),
            "hashes_arquivos_indice": manifesto.get("arquivos"),
            "hash_benchmark": benchmark_hash,
            "tempo_total_segundos": tempo_total_segundos,
            "latencia_media_consulta_ms": round(mean(tempos_ms), 3) if tempos_ms else 0.0,
        },
        "resumo_geral": {
            "total_casos_testados": len(resultados),
            "casos_com_referencia": len(positivos),
            "casos_controle_negativo": len(negativos),
            "recall_1": recall_1,
            "recall_3": recall_3,
            "recall_5": recall_5,
            "mrr": mrr,
        },
        "metricas_por_tipo": metricas_por_tipo,
        "detalhes": resultados,
    }


def formatar_tabela_resumo(resultado: dict) -> str:
    """Gera uma visualização tabular amigável no terminal."""
    resumo = resultado["resumo_geral"]
    meta = resultado["metadata_mlops"]
    linhas = [
        "=" * 70,
        " RELATÓRIO DE AVALIAÇÃO DE MLOPS - BENCHMARK DE RECUPERAÇÃO",
        "=" * 70,
        f" Modelo avaliado:           {meta.get('modelo')}",
        f" Total de casos testados:   {resumo['total_casos_testados']}",
        f" Casos com referência:      {resumo['casos_com_referencia']}",
        f" Casos controle negativo:   {resumo['casos_controle_negativo']}",
        f" Latência média / consulta: {meta['latencia_media_consulta_ms']} ms",
        "-" * 70,
        f" Recall@1 geral:  {resumo['recall_1']}",
        f" Recall@3 geral:  {resumo['recall_3']}",
        f" Recall@5 geral:  {resumo['recall_5']}",
        f" MRR geral:       {resumo['mrr']}",
        "=" * 70,
        f" {'Categoria / Tipo':<25} | {'Casos':<6} | {'Rec@1':<7} | {'Rec@5':<7} | {'MRR':<7} | {'Score Top':<8}",
        "-" * 70,
    ]

    for tipo, m in resultado["metricas_por_tipo"].items():
        r1 = str(m.get("recall_1", "-"))
        r5 = str(m.get("recall_5", "-"))
        mrr = str(m.get("mrr", "-"))
        score = str(m.get("pontuacao_topo_media", "-"))
        linhas.append(f" {tipo:<25} | {m['total_casos']:<6} | {r1:<7} | {r5:<7} | {mrr:<7} | {score:<8}")

    linhas.append("=" * 70)
    return "\n".join(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=BENCHMARK_PADRAO)
    parser.add_argument("--indice", type=Path, default=INDICE_PADRAO)
    parser.add_argument("--modelo", default="baseline-hashing")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--saida", type=Path, default=RELATORIO_PADRAO)
    parser.add_argument("--silencioso", action="store_true", help="Não imprime a tabela no terminal")
    args = parser.parse_args()

    try:
        benchmark = carregar_benchmark(args.benchmark)
        hash_benchmark = _calcular_hash(args.benchmark)
        gerador = criar_gerador(args.modelo)
        vetores, metadados, manifesto = carregar_indice(args.indice, gerador.nome)

        resultado = avaliar_benchmark(
            benchmark=benchmark,
            vetores=vetores,
            metadados=metadados,
            gerador=gerador,
            manifesto=manifesto,
            top_k=args.top_k,
            benchmark_hash=hash_benchmark,
        )

        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

        if not args.silencioso:
            print(formatar_tabela_resumo(resultado))
            print(f"\nRelatório completo salvo em: {args.saida}\n")

    except ValueError as erro:
        parser.exit(1, f"Erro na avaliação do benchmark: {erro}\n")


if __name__ == "__main__":
    main()
