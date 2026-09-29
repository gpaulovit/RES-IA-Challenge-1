import json
from pathlib import Path

import pytest

from checagens.avaliacao import avaliar, carregar_amostra


def test_amostra_realmente_expoe_acertos_e_limites():
    resultado = avaliar(carregar_amostra(Path("data/amostras/avaliacao-arquitetura.json")))
    assert resultado["quantidade_consultas"] == 9
    for metodo in resultado["metodos"].values():
        assert metodo["recall_1"] < 1
        negacao = next(item for item in metodo["resultados"] if item["tipo"] == "negacao")
        assert negacao["id_referencia"] is None
        assert negacao["primeira_pontuacao"] > 0.9


def test_referencia_inexistente_e_rejeitada(tmp_path):
    caminho = tmp_path / "amostra.json"
    caminho.write_text(json.dumps({"alegacoes": [{"id": "a", "texto": "abc"}], "consultas": [{"tipo": "parafrase", "texto": "abc", "id_referencia": "b"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="inexistente"):
        carregar_amostra(caminho)
