#Lista os 7 arquivos brutos dos 6 datasets, com a URL fixada por commit e o sha256 esperado. Define as pastas data/brutos, data/processados e data/relatorios.

"""Datasets brutos: URL fixada por commit (ou release) e sha256 conferido no download."""

from dataclasses import dataclass
from pathlib import Path

BRUTOS = Path("data/brutos")
PROCESSADOS = Path("data/processados")
RELATORIOS = Path("data/relatorios")


@dataclass(frozen=True)
class Fonte:
    nome: str
    url: str
    destino: Path
    sha256: str
    # True: o sha256 é do conteúdo extraído (o zip que o GitHub gera para um commit não tem bytes
    # estáveis), calculado por `baixar.hash_conteudo_zip`.
    hash_do_conteudo: bool = False


_RAW = "https://raw.githubusercontent.com"

FONTES = [
    Fonte("FactPolCheckBr",
          f"{_RAW}/Interfaces-UFSCAR/Dataset-FactPolCheckBr/e4b4feafce9b83789a517f649abb39ad4645f1b3/dados/com_texto.csv",
          BRUTOS / "factpolcheckbr" / "com_texto.csv",
          "7f0c9443dcf2d7fb15ef3320eb1bfeb8b0d67f4689a13757b33809f200e84681"),
    Fonte("FACTCK.BR",
          f"{_RAW}/jghm-f/FACTCK.BR/57e25d742ea14cb912069d3f6e9a0333477bc9c3/FACTCKBR.tsv",
          BRUTOS / "factckbr" / "FACTCKBR.tsv",
          "1e90fe8b67af22d0f756a7f831b6a2f66072b5d0d66fb1172f3bda1e748201db"),
    Fonte("FactChecks.br",
          "https://github.com/fake-news-UFG/FactChecks.br/releases/download/v0.1/FactChecksbr.zip",
          BRUTOS / "factchecksbr" / "FactChecksbr.zip",
          "035faf96dcb851e166c330af4636689669b5ff032c46bec109178669317c31b3"),
    Fonte("Fake.br-Corpus",
          "https://github.com/roneysco/Fake.br-Corpus/archive/780f5516c4ae070761632d98ac3368f3ded09d35.zip",
          BRUTOS / "fakebr" / "Fake.br-Corpus.zip",
          "23b86ad49d64ce9164adc5e6874a6931706c452d9dbfb35af6d9185483883a07",
          hash_do_conteudo=True),
    Fonte("FakeWhatsApp.Br",
          f"{_RAW}/cabrau/FakeWhatsApp.Br/9c6bf19b2a8a24c9ed6db4afdb3fbd9f2f971b94/data/2018/fakeWhatsApp.BR_2018.csv",
          BRUTOS / "fakewhatsappbr" / "fakeWhatsApp.BR_2018.csv",
          "e8127d0e0d69792e672085ff81728489d15ad40c0a80e22b036b2ffd75f60716"),
    Fonte("FakeTweet.Br",
          f"{_RAW}/prc992/FakeTweet.Br/6c349a0cd69dc381625b7fc456b8049c977f6c5d/FakeTweetBr.csv",
          BRUTOS / "faketweetbr" / "FakeTweetBr.csv",
          "ec3224abfa83296229b8a00e29af5444237919c269ab1c7841eb88b327b96883"),
    Fonte("FakeTweet.Br (teste)",
          f"{_RAW}/prc992/FakeTweet.Br/6c349a0cd69dc381625b7fc456b8049c977f6c5d/FakeTweetBr-Test.csv",
          BRUTOS / "faketweetbr" / "FakeTweetBr-Test.csv",
          "057520d86eb878d4a66f9de19a60b0f3c7e420ae98d52d14de491bf53f899a91"),
]
