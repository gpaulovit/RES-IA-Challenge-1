"""Normalização da consulta (RF-05): apelidos e internetês por dicionário."""
import pytest

from inteligencia.normalizacao import normalizar_consulta


@pytest.mark.parametrize("entrada, saida", [
    ("Xandão recebeu dinheiro do Molusco", "Alexandre de Moraes recebeu dinheiro do Lula"),
    ("xandao e o luladrão", "Alexandre de Moraes e o Lula"),            # sem acento e minúsculo
    ("vc viu q o gov mentiu", "você viu que o governo mentiu"),
    ("Lula ñ disse isso", "Lula não disse isso"),
    ("naum foi assim", "não foi assim"),
])
def test_desfaz_apelidos_e_internetes(entrada, saida):
    assert normalizar_consulta(entrada) == saida


def test_nao_mexe_em_pedaco_de_palavra_nem_em_palavra_ambigua():
    assert normalizar_consulta("Mitologia grega") == "Mitologia grega"   # "Mito" é apelido, "Mitologia" não
    assert normalizar_consulta("foi tão bom") == "foi tão bom"           # "tão" não vira "estão"


def test_apelido_ambiguo_fica_de_fora():
    assert normalizar_consulta("o Barba falou") == "o Barba falou"       # no_normalizador = nao
