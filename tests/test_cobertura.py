import pytest

from checagens import cobertura


def registro(numero, titulo, veredito="Falsa", agencia="Agência A",
             data="2022-08-10", link=None, status="padronizada", possibilidades=None):
    return {
        "numero_origem": numero,
        "organizado": {
            "titulo_checagem": titulo, "veredito_original": veredito, "agencia": agencia,
            "link": link, "candidatos_favorecidos": "Pessoa",
            "data": {"padronizada": data if status == "padronizada" else None,
                     "status": status, "possibilidades": possibilidades or []},
        },
    }


def corpus(*registros):
    return {"metadados": {"fonte": "ficticia"}, "registros": list(registros)}


def test_mapeia_vereditos_e_lista_os_que_nao_sao_falsos():
    relatorio = cobertura.analisar(corpus(
        registro(1, "É falso que urna troca voto"),
        registro(2, "Veja o que é #FATO ou #FAKE no debate", veredito=None),
        registro(3, "Voto vale como prova de vida", veredito="Verdadeira", agencia="Agência B"),
    ))

    assert relatorio["vereditos_normalizados"] == {"falso": 1, "sem_veredito": 1, "verdadeiro": 1}
    assert [item["registro"] for item in relatorio["registros_nao_falsos"]] == [2, 3]
    assert relatorio["marcadores_no_titulo"]["Agência A"]["falso"] == 1
    assert relatorio["temas_exploratorios"]["contagem"]["urnas_sistema_eleitoral"] == 2


def test_rotulo_fora_da_taxonomia_interrompe():
    with pytest.raises(ValueError, match="Enganoso"):
        cobertura.analisar(corpus(registro(1, "Título", veredito="Enganoso")))


def test_confirma_data_ambigua_pelo_link_sem_alterar_o_corpus():
    ambigua = [{"formato": "mes_dia_ano", "data": "2022-10-03"},
               {"formato": "dia_mes_ano", "data": "2022-03-10"}]
    entrada = corpus(
        registro(1, "Urna eletrônica troca voto", status="ambigua", possibilidades=ambigua,
                 link="https://example.org/2022/10/03/a"),
        registro(2, "Mesário anula votação", status="ambigua", possibilidades=ambigua,
                 link="https://example.org/2022/11/03/b"),
        registro(3, "Vídeo de apuração editado", status="ambigua", possibilidades=ambigua,
                 link="https://example.org/c"),
    )
    relatorio = cobertura.analisar(entrada)

    confirmacao = relatorio["cobertura_temporal"]["confirmacao_ambiguas_pelo_link"]
    assert confirmacao == {"contagem": {"mes_dia_ano": 1, "nenhum": 1, "sem_data_no_link": 1},
                           "registros_sem_correspondencia": [2]}
    assert relatorio["cobertura_temporal"]["por_mes"] == {"2022-10": 3}
    assert entrada["registros"][0]["organizado"]["data"]["padronizada"] is None


def test_sobreposicao_conta_reescritas_entre_agencias_e_intervalo():
    relatorio = cobertura.analisar(corpus(
        registro(1, "Banqueiros apoiam Lula em troca da revogação do Pix", data="2022-08-01"),
        registro(2, "É falso que banqueiros apoiam Lula em troca da revogação do Pix",
                 agencia="Agência B", data="2022-10-29"),
        registro(3, "Vídeo antigo de enchente circula como atual", data="2022-09-01"),
    ))

    sobreposicao = relatorio["sobreposicao_lexical_titulos"]
    assert sobreposicao["registros_com_par"] == 2
    assert sobreposicao["registros_com_par_outra_agencia"] == 2
    assert sobreposicao["pares_com_intervalo_minimo_30_dias"] == 1
