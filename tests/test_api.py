import pytest


def test_saude(cliente):
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "modo": "demonstracao"}


def test_caminho_completo_e_evidencias(cliente, exemplos):
    resposta = cliente.post("/buscar", json={"texto": exemplos[0].alegacao})
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["modo"] == "demonstracao"
    assert dados["metodo"] == "tfidf_cosseno"
    assert dados["status"] == "candidatos_encontrados"
    assert "não a verdade" in dados["aviso"]
    primeiro = dados["candidatos"][0]
    assert primeiro["pontuacao"] == pytest.approx(1)
    assert {campo: primeiro[campo] for campo in exemplos[0].model_dump()} == exemplos[0].model_dump()
    for candidato in dados["candidatos"]:
        assert set(candidato) == {
            "id", "alegacao", "checagem", "agencia", "veredito_original", "pontuacao"
        }


def test_sem_resultado(cliente):
    dados = cliente.post("/buscar", json={"texto": "abacaxi telescópio submarino"}).json()
    assert dados["status"] == "nao_encontrada"
    assert dados["candidatos"] == []


def test_limite_pela_api(cliente):
    dados = cliente.post(
        "/buscar", json={"texto": "eleição transporte orçamento", "top_k": 1}
    ).json()
    assert len(dados["candidatos"]) == 1


@pytest.mark.parametrize(
    "entrada",
    [
        {}, {"texto": ""}, {"texto": " \n "}, {"texto": None}, {"texto": 12},
        *[{"texto": "eleição", "top_k": valor} for valor in [0, 11, 1.5, True, "3", None]],
        {"texto": "eleição", "campo_desconhecido": 1},
    ],
)
def test_entrada_invalida_em_portugues(cliente, entrada):
    resposta = cliente.post("/buscar", json=entrada)
    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["mensagem"]


def test_json_malformado(cliente):
    resposta = cliente.post("/buscar", content="{", headers={"Content-Type": "application/json"})
    assert resposta.status_code == 422
    assert "JSON válido" in resposta.json()["detail"][0]["mensagem"]


def test_documentacao_interativa(cliente):
    assert cliente.get("/docs").status_code == 200
    contrato = cliente.get("/openapi.json").json()
    assert "/buscar" in contrato["paths"]
    assert "/health" in contrato["paths"]
