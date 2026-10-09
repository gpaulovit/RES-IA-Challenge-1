#Baixa os brutos, tenta até 3 vezes, confere o sha256 e não baixa de novo o que já está certo.

"""Baixa os datasets brutos para data/brutos/ e confere o sha256 de cada um.

    python -m checagens.bases.baixar

Idempotente: arquivo já presente com o hash certo não é baixado de novo.
"""

import hashlib
from pathlib import Path
import sys
import urllib.request
import zipfile

from checagens.bases.fontes import FONTES, Fonte

# Do zip do Fake.br só interessam os textos de tamanho igualado e os metadados (data).
PASTAS_FAKEBR = ("size_normalized_texts/", "-meta-information/")
TENTATIVAS = 3


def hash_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def hash_conteudo_zip(caminho: Path) -> str:
    """sha256 dos arquivos usados do zip (nome sem a pasta raiz + bytes), em ordem de nome."""
    h = hashlib.sha256()
    with zipfile.ZipFile(caminho) as z:
        nomes = sorted(n for n in z.namelist() if not n.endswith("/") and any(p in n for p in PASTAS_FAKEBR))
        for nome in nomes:
            h.update(nome.split("/", 1)[1].encode())
            h.update(z.read(nome))
    return h.hexdigest()


def _hash(fonte: Fonte) -> str:
    return hash_conteudo_zip(fonte.destino) if fonte.hash_do_conteudo else hash_arquivo(fonte.destino)


def baixar(fonte: Fonte) -> None:
    if fonte.destino.exists() and _hash(fonte) == fonte.sha256:
        print(f"ok (já presente)  {fonte.nome}")
        return
    fonte.destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = fonte.destino.with_suffix(fonte.destino.suffix + ".part")
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            with urllib.request.urlopen(fonte.url, timeout=300) as resposta, temporario.open("wb") as f:
                while bloco := resposta.read(1 << 20):
                    f.write(bloco)
            break
        except OSError as erro:
            temporario.unlink(missing_ok=True)
            if tentativa == TENTATIVAS:
                sys.exit(f"falha ao baixar {fonte.nome} após {TENTATIVAS} tentativas: {erro}")
            print(f"tentativa {tentativa} falhou para {fonte.nome} ({erro}); tentando de novo")
    temporario.replace(fonte.destino)
    obtido = _hash(fonte)
    if obtido != fonte.sha256:
        sys.exit(f"sha256 diferente para {fonte.nome}: esperado {fonte.sha256}, obtido {obtido}")
    print(f"ok (baixado)      {fonte.nome}")


def main() -> None:
    for fonte in FONTES:
        baixar(fonte)


if __name__ == "__main__":
    main()
