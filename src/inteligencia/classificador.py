"""Camada 2 do bot: classificador de sinais de alerta (RF-08).

Contrato com o bot: `classificar(texto)` devolve `{"faixa": ..., "sinais": [...]}`.
- faixa: `muitos_sinais` / `incerto` / `poucos_sinais`. Nunca expõe probabilidade (RNF-06).
- sinais: 2 ou 3 termos do próprio texto que mais pesaram na direção da faixa.

Modelo, divisão, faixas e critério de go/no-go seguem o protocolo pré-registrado em
docs/relatorio-camada2.md. O treino fica em treino.py (python -m inteligencia.treino).
"""
import re
from functools import cache
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, strip_accents_unicode
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

RAIZ = Path(__file__).resolve().parents[2]
MODELO_PADRAO = RAIZ / "models" / "classificador.joblib"
FAIXAS = ("muitos_sinais", "incerto", "poucos_sinais")

# Só para a EXIBIÇÃO dos sinais: o modelo e as métricas continuam usando todas as palavras.
# Palavras vazias ("no", "vai", "das") não explicam nada ao usuário.
PALAVRAS_VAZIAS = frozenset("""
a ao aos as com como da das de dela dele do dos e ela ele em entre era essa esse esta este eu foi
for ha isso isto ja la lhe mais mas me mesmo meu muito na nas nem no nos o os ou para pela pelo
por qual quando que quem se sem ser seu sua sao so tambem tem ter um uma umas uns vai vao voce
""".split())


def criar_pipeline(params: dict) -> Pipeline:
    """TF-IDF + regressão logística (protocolo, seção "Modelo"). Classe positiva: notícia falsa."""
    c2 = params["camada2"]
    return Pipeline([
        ("tfidf", TfidfVectorizer(strip_accents="unicode", lowercase=True,
                                  ngram_range=tuple(c2["ngram_range"]), min_df=c2["min_df"])),
        ("lr", LogisticRegression(class_weight="balanced", C=c2["C"], max_iter=c2["max_iter"],
                                  random_state=params["semente"])),
    ])


def probabilidades_fora_da_amostra(textos: list[str], y: np.ndarray, params: dict) -> np.ndarray:
    """P(falsa) de cada item do treino, prevista por um modelo que não o viu (validação cruzada)."""
    cv = StratifiedKFold(n_splits=params["camada2"]["folds"], shuffle=True, random_state=params["semente"])
    return cross_val_predict(criar_pipeline(params), textos, y, cv=cv, method="predict_proba")[:, 1]


def escolher_cortes(p: np.ndarray, y: np.ndarray, margem: float) -> tuple[float, float]:
    """Cortes das faixas a partir das probabilidades fora da amostra (protocolo, seção "Faixas").

    corte_alto: menor limiar com no máximo `margem` das verdadeiras em p ≥ limiar.
    corte_baixo: maior limiar com no máximo `margem` das falsas em p ≤ limiar.
    """
    verdadeiras = np.sort(p[y == 0])[::-1]           # decrescente
    falsas = np.sort(p[y == 1])                       # crescente
    m_v, m_f = int(margem * len(verdadeiras)), int(margem * len(falsas))
    # logo acima da (m+1)-ésima maior: só as m maiores ficam ≥ corte (empates só reduzem a contagem)
    alto = float(np.nextafter(verdadeiras[m_v], np.inf)) if m_v < len(verdadeiras) else 0.0
    baixo = float(np.nextafter(falsas[m_f], -np.inf)) if m_f < len(falsas) else 1.0
    return alto, baixo


def faixa(p: float, corte_alto: float, corte_baixo: float) -> str:
    if p >= corte_alto:
        return "muitos_sinais"
    return "poucos_sinais" if p <= corte_baixo else "incerto"


def sinais(pipeline: Pipeline, texto: str, faixa_: str, n: int = 3) -> list[str]:
    """Termos do texto com maior contribuição (TF-IDF × coeficiente) na direção da faixa (RF-08).

    Palavras vazias (PALAVRAS_VAZIAS) não são exibidas.

    muitos_sinais → os que mais empurram para "falsa"; poucos_sinais → os que mais empurram para
    "verdadeira"; incerto → os de maior peso absoluto. Se faltarem termos na direção da faixa, completa
    com os de maior peso absoluto, para chegar a 2 ou 3 quando o texto tiver vocabulário suficiente.
    """
    tfidf, lr = pipeline.named_steps["tfidf"], pipeline.named_steps["lr"]
    x = tfidf.transform([texto]).tocoo()
    if x.nnz == 0:
        return []
    termos = tfidf.get_feature_names_out()[x.col]
    contrib = x.data * lr.coef_[0][x.col]
    # termo exibível: tem ao menos uma palavra que não é vazia ("das eleicoes" sim, "no" não)
    exibivel = np.array([any(w not in PALAVRAS_VAZIAS for w in t.split()) for t in termos])
    sentido = {"muitos_sinais": contrib, "poucos_sinais": -contrib}.get(faixa_, np.abs(contrib))
    escolhidos = [i for i in np.argsort(-sentido, kind="stable") if sentido[i] > 0 and exibivel[i]][:n]
    for i in np.argsort(-np.abs(contrib), kind="stable"):
        if len(escolhidos) >= 2:
            break
        if i not in escolhidos and exibivel[i]:
            escolhidos.append(i)
    return [_forma_original(str(termos[i]), texto) for i in escolhidos]


def _forma_original(termo: str, texto: str) -> str:
    """O vocabulário é sem acento e minúsculo ("eleicoes"); o bot mostra como o usuário escreveu ("eleições")."""
    palavras = re.findall(r"(?u)\b\w\w+\b", texto)        # mesmo padrão de tokens do TfidfVectorizer
    normais = [strip_accents_unicode(w.lower()) for w in palavras]
    n = len(termo.split())
    for i in range(len(palavras) - n + 1):
        if " ".join(normais[i:i + n]) == termo:
            return " ".join(palavras[i:i + n])
    return termo


class Classificador:
    def __init__(self, pipeline: Pipeline, corte_alto: float, corte_baixo: float):
        self.pipeline, self.corte_alto, self.corte_baixo = pipeline, corte_alto, corte_baixo

    def probabilidade(self, textos: list[str]) -> np.ndarray:
        """Uso interno (métricas). O bot nunca recebe este número (RNF-06)."""
        return self.pipeline.predict_proba(textos)[:, 1]

    def classificar(self, texto: str) -> dict:
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("Informe um texto com conteúdo para classificar.")
        f = faixa(float(self.probabilidade([texto.strip()])[0]), self.corte_alto, self.corte_baixo)
        return {"faixa": f, "sinais": sinais(self.pipeline, texto.strip(), f)}

    def salvar(self, caminho: Path = MODELO_PADRAO) -> None:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"pipeline": self.pipeline, "corte_alto": self.corte_alto,
                     "corte_baixo": self.corte_baixo}, caminho)

    @classmethod
    def carregar(cls, caminho: Path = MODELO_PADRAO) -> "Classificador":
        try:
            d = joblib.load(caminho)
        except OSError as erro:
            raise ValueError(f"Modelo não encontrado em {caminho}. Rode o treino (dvc repro treinar).") from erro
        return cls(d["pipeline"], d["corte_alto"], d["corte_baixo"])


@cache
def _classificador_padrao() -> Classificador:
    return Classificador.carregar()


def classificar(texto: str) -> dict:
    """Contrato com o bot (RF-08). Mudou a assinatura? Avise a Engenharia.

    Só deve ser exibido se docs/relatorio-camada2.md registrar `go` (RN-04).
    """
    return _classificador_padrao().classificar(texto)
