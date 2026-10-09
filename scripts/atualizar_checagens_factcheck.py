"""Baixa as checagens recentes das agências brasileiras (Google Fact Check Tools) para data/externos/.

Usa a API pública claims:search do Google. Cada checagem vira um registro no formato da base de
checagens: id, alegacao, veredito_original, veredito_normalizado, agencia, data, link,
fonte_dataset. O arquivo gerado é uma fonte bruta, versionada no git (dados públicos, sem chave):
quem junta com as outras bases, normaliza o veredito, deduplica e valida é o estágio `checagens`
do DVC (src/checagens/bases/checagens.py). Rodar de novo só acrescenta checagens novas.

Precisa de uma chave gratuita do Google Cloud com a "Fact Check Tools API" ativada, na variável
FACTCHECK_API_KEY (no ambiente ou no .env da raiz). Nunca coloque a chave no código ou no GitHub.

Uso (na raiz do repositório):
    python scripts/atualizar_checagens_factcheck.py            # últimos 365 dias
    python scripts/atualizar_checagens_factcheck.py --dias 730
Depois: dvc repro checagens indice calibrar
"""
import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "data" / "externos" / "google_factcheck.json"
API = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

# Sites das agências brasileiras (filtro reviewPublisherSiteFilter da API)
AGENCIAS = {
    "aosfatos.org": "Aos Fatos",
    "lupa.uol.com.br": "Agência Lupa",
    "agencialupa.org": "Agência Lupa",
    "lupa.news": "Agência Lupa",
    "piaui.folha.uol.com.br": "Agência Lupa",
    "g1.globo.com": "Fato ou Fake",
    "estadao.com.br": "Estadão Verifica",
    "politica.estadao.com.br": "Estadão Verifica",
    "noticias.uol.com.br": "UOL Confere",
    "checamos.afp.com": "AFP Checamos",
    "projetocomprova.com.br": "Projeto Comprova",
    "boatos.org": "Boatos.org",
    "e-farsas.com": "E-farsas",
    "apublica.org": "Agência Pública",
}

# RN-02: rótulo da agência -> rótulo normalizado (o rótulo original é mantido)
NORMALIZACAO = [
    (r"falso|fake|mentira|boato|golpe|não é verdade", "falso"),
    (r"engan|distorc|sem contexto|fora de contexto|exager|imprecis|parcial|montagem|manipul|insustent", "enganoso"),
    (r"verdad|correto|^fato$|confirmad", "verdadeiro"),
]
CARIMBOS = re.compile(r"(?i)(é\s*#?\s*fake\s*que|#\s*fake|#\s*boato|é\s*falso\s*que|é\s*mentira\s*que)")


def chave_api() -> str:
    chave = os.getenv("FACTCHECK_API_KEY", "").strip()
    env = RAIZ / ".env"
    if not chave and env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.strip().removeprefix("export ").startswith("FACTCHECK_API_KEY="):
                chave = linha.split("=", 1)[1].strip().strip('"').strip("'")
    if not chave:
        raise SystemExit("Coloque FACTCHECK_API_KEY=<sua chave> no .env da raiz do projeto.")
    return chave


def normalizar_veredito(rotulo: str) -> str:
    r = (rotulo or "").strip().lower()
    for padrao, normal in NORMALIZACAO:
        if re.search(padrao, r):
            return normal
    return "outro"


def _pedir(url: str, abrir, tentativas: int = 4) -> dict:
    """GET com nova tentativa e pausa crescente quando o Google responde 429/500/503."""
    for i in range(tentativas):
        try:
            with abrir(url, timeout=30) as resposta:
                return json.loads(resposta.read().decode("utf-8"))
        except urllib.error.HTTPError as erro:
            if erro.code not in (429, 500, 503) or i == tentativas - 1:
                raise
            time.sleep(5 * 2 ** i)   # 5, 10, 20 s


def buscar_site(site: str, dias: int, chave: str, abrir=urllib.request.urlopen) -> list[dict]:
    """Todas as páginas de resultado da API para um site de agência."""
    claims, token = [], None
    while True:
        params = {"reviewPublisherSiteFilter": site, "languageCode": "pt", "maxAgeDays": dias,
                  "pageSize": 100, "key": chave}
        if token:
            params["pageToken"] = token
        dados = _pedir(f"{API}?{urllib.parse.urlencode(params)}", abrir)
        claims += dados.get("claims", [])
        token = dados.get("nextPageToken")
        if not token:
            return claims
        time.sleep(0.2)


def para_registros(claims: list[dict], site: str) -> list[dict]:
    """Uma linha por revisão de agência. A alegação é o texto checado, sem carimbo."""
    registros = []
    for c in claims:
        alegacao = " ".join(CARIMBOS.sub(" ", c.get("text", "")).split())
        for r in c.get("claimReview", []):
            data = (r.get("reviewDate") or c.get("claimDate") or "")[:10]
            link = r.get("url", "").strip()
            if not (alegacao and link and re.fullmatch(r"\d{4}-\d{2}-\d{2}", data)):
                continue
            rotulo = r.get("textualRating", "").strip()
            registros.append({
                "id": "gfc-" + re.sub(r"\W+", "-", link.split("//")[-1])[:120],
                "alegacao": alegacao,
                "veredito_original": rotulo or "ver no site",
                "veredito_normalizado": normalizar_veredito(rotulo),
                "agencia": AGENCIAS.get(site) or r.get("publisher", {}).get("name") or site,
                "data": data,
                "link": link,
                "fonte_dataset": "Google Fact Check Tools",
            })
    return registros


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dias", type=int, default=365, help="idade máxima das checagens (padrão: 365)")
    p.add_argument("--saida", type=Path, default=SAIDA)
    a = p.parse_args()

    chave = chave_api()
    registros = json.loads(a.saida.read_text(encoding="utf-8")) if a.saida.exists() else []
    links, por_agencia, antes = {r["link"] for r in registros}, Counter(), len(registros)
    for site in AGENCIAS:
        try:
            recebidos = para_registros(buscar_site(site, a.dias, chave), site)
        except Exception as erro:  # um site com problema não derruba os outros
            print(f"  {site}: erro ({erro})")
            continue
        for r in recebidos:
            if r["link"] not in links:
                links.add(r["link"])
                registros.append(r)
                por_agencia[r["agencia"]] += 1
        print(f"  {site}: {len(recebidos)} checagens recebidas")
        time.sleep(2)

    a.saida.parent.mkdir(parents=True, exist_ok=True)
    a.saida.write_text(json.dumps(registros, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"\n{len(registros) - antes} checagens novas | {len(registros)} no total em {a.saida}")
    for agencia, n in por_agencia.most_common():
        print(f"  {agencia}: {n}")
    print("Rótulos das agências (os 10 mais comuns):",
          Counter(r["veredito_original"] for r in registros).most_common(10))
    print("\nPróximo passo: dvc repro checagens indice calibrar")

if __name__ == "__main__":
    main()