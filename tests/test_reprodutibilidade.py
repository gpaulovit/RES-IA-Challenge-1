"""Testes automatizados de reprodutibilidade de treinamento (RNF-10).

Comprova que o treinamento com semente fixa produz métricas e previsões
estritamente idênticas quando executado múltiplas vezes.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline


def test_reprodutibilidade_treino_com_semente_fixa():
    # Amostra de treino
    textos_treino = [
        "URGENTE fraude confirmada nas urnas",
        "Eleições 2026 código secreto revelado",
        "TSE publica normas de votação oficial",
        "Tribunal Eleitoral divulga horários de atendimento",
    ]
    rotulos_treino = [1, 1, 0, 0]

    # Amostra de teste
    textos_teste = [
        "Urnas com fraude secreta revelada",
        "Tribunal divulga novo comunicado de votação",
    ]
    rotulos_teste = [1, 0]

    def _treinar(semente: int = 42):
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer()),
            ("clf", LogisticRegression(random_state=semente)),
        ])
        pipeline.fit(textos_treino, rotulos_treino)
        preds = pipeline.predict(textos_teste)
        probs = pipeline.predict_proba(textos_teste)
        f1 = f1_score(rotulos_teste, preds, average="macro")
        return f1, probs, pipeline.named_steps["clf"].coef_

    f1_rodada1, probs_rodada1, coefs_rodada1 = _treinar(42)
    f1_rodada2, probs_rodada2, coefs_rodada2 = _treinar(42)

    # Métricas idênticas
    assert f1_rodada1 == f1_rodada2
    # Probabilidades idênticas
    assert (probs_rodada1 == probs_rodada2).all()
    # Coeficientes do modelo idênticos
    assert (coefs_rodada1 == coefs_rodada2).all()
