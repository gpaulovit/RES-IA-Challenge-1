"""Módulo de registros anônimos de consultas e votos (MLOps / C9).

Atende:
- RF-12: Registro de votos 👍/👎.
- RF-13: Registro anônimo de cada consulta (data, tipo, camada, faixa, semelhança, voto).
- RN-03: Nenhum dado pessoal (nome, usuário, telefone, ID do Telegram) é guardado.
- RNF-08: Privacidade e conformidade estrita com LGPD.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CAMINHO_REGISTROS_PADRAO = Path(
    os.getenv("CHECK_LOGS_PATH", "data/registros/consultas.jsonl")
)

CAMPOS_PROIBIDOS_LGPD = {
    "user_id",
    "chat_id",
    "username",
    "telefone",
    "phone",
    "first_name",
    "last_name",
    "nome",
    "ip",
}


def _sanitizar_metadados(metadados: dict[str, Any] | None) -> dict[str, Any]:
    """Verifica e remove preventivamente quaisquer campos pessoais proibidos pela LGPD."""
    if not metadados:
        return {}
    sanitizado = {}
    for chave, valor in metadados.items():
        chave_lower = chave.lower()
        if chave_lower in CAMPOS_PROIBIDOS_LGPD:
            raise ValueError(
                f"Violação de privacidade (RN-03/RNF-08): campo pessoal proibido detectado: '{chave}'"
            )
        sanitizado[chave] = valor
    return sanitizado


def registrar_consulta(
    tipo_entrada: str,
    camada: int,
    faixa: str | None = None,
    semelhanca: float | None = None,
    id_consulta: str | None = None,
    metadados_adicionais: dict[str, Any] | None = None,
    caminho_arquivo: Path | None = None,
) -> dict[str, Any]:
    """Registra uma consulta anonimizada no arquivo JSONL.

    Args:
        tipo_entrada: 'texto' ou 'link'.
        camada: 1 (busca em agências) ou 2 (classificador de alertas).
        faixa: 'muitos_sinais', 'incerto', 'poucos_sinais' ou None se camada 1.
        semelhanca: Similaridade de cosseno máxima encontrada (0.0 a 1.0) ou None.
        id_consulta: Identificador único gerado (UUID), ou gerado automaticamente.
        metadados_adicionais: Dicionário sem dados pessoais para métricas (ex: latência).
        caminho_arquivo: Caminho do arquivo JSONL (opcional).

    Returns:
        Dicionário do registro gerado.
    """
    tipo_norm = str(tipo_entrada).strip().lower()
    if tipo_norm not in {"texto", "link"}:
        raise ValueError(f"Tipo de entrada inválido: '{tipo_entrada}'. Esperado: 'texto' ou 'link'.")

    if camada not in {1, 2}:
        raise ValueError(f"Camada inválida: {camada}. Esperado: 1 ou 2.")

    extra = _sanitizar_metadados(metadados_adicionais)

    cid = id_consulta or uuid.uuid4().hex
    data_utc = datetime.now(timezone.utc).isoformat()
    sem_arredondada = round(float(semelhanca), 4) if semelhanca is not None else None

    registro: dict[str, Any] = {
        "id_consulta": cid,
        "data_hora_utc": data_utc,
        "tipo_entrada": tipo_norm,
        "camada": camada,
        "faixa": faixa,
        "semelhanca": sem_arredondada,
        "voto": None,
    }

    if extra:
        registro["extra"] = extra

    caminho = caminho_arquivo or CAMINHO_REGISTROS_PADRAO
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")

    return registro


def registrar_voto(
    id_consulta: str,
    voto: str,
    caminho_arquivo: Path | None = None,
) -> bool:
    """Atualiza o registro anônimo de uma consulta com o voto 👍 ou 👎 do usuário (RF-12).

    Args:
        id_consulta: ID retornado no momento da resposta da consulta.
        voto: 'positivo', 'negativo', '👍' ou '👎'.
        caminho_arquivo: Caminho do arquivo JSONL.

    Returns:
        True se o registro foi localizado e atualizado, False caso contrário.
    """
    if not id_consulta:
        raise ValueError("id_consulta não pode ser vazio.")

    voto_str = str(voto).strip().lower()
    if voto_str in {"positivo", "👍", "+1", "like"}:
        voto_norm = "positivo"
    elif voto_str in {"negativo", "👎", "-1", "dislike"}:
        voto_norm = "negativo"
    else:
        raise ValueError(f"Voto inválido: '{voto}'. Esperado: positivo/👍 ou negativo/👎.")

    caminho = caminho_arquivo or CAMINHO_REGISTROS_PADRAO
    if not caminho.exists():
        return False

    linhas = caminho.read_text(encoding="utf-8").splitlines()
    atualizado = False
    novas_linhas = []

    for linha in linhas:
        if not linha.strip():
            continue
        try:
            reg = json.loads(linha)
            if reg.get("id_consulta") == id_consulta:
                reg["voto"] = voto_norm
                reg["data_hora_voto_utc"] = datetime.now(timezone.utc).isoformat()
                atualizado = True
            novas_linhas.append(json.dumps(reg, ensure_ascii=False))
        except json.JSONDecodeError:
            novas_linhas.append(linha)

    if atualizado:
        caminho.write_text("\n".join(novas_linhas) + "\n", encoding="utf-8")

    return atualizado


def carregar_registros(caminho_arquivo: Path | None = None) -> list[dict[str, Any]]:
    """Carrega todos os registros anônimos salvos."""
    caminho = caminho_arquivo or CAMINHO_REGISTROS_PADRAO
    if not caminho.exists():
        return []

    registros = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if linha.strip():
            try:
                registros.append(json.loads(linha))
            except json.JSONDecodeError:
                continue
    return registros


def obter_metricas_monitoramento(caminho_arquivo: Path | None = None) -> dict[str, Any]:
    """Calcula estatísticas agregadas de uso e feedback para o componente C9 (Monitoramento)."""
    registros = carregar_registros(caminho_arquivo)
    total = len(registros)
    if total == 0:
        return {
            "total_consultas": 0,
            "camada_1_total": 0,
            "camada_2_total": 0,
            "votos_positivos": 0,
            "votos_negativos": 0,
        }

    c1 = sum(1 for r in registros if r.get("camada") == 1)
    c2 = sum(1 for r in registros if r.get("camada") == 2)
    v_pos = sum(1 for r in registros if r.get("voto") == "positivo")
    v_neg = sum(1 for r in registros if r.get("voto") == "negativo")

    semelhancas = [r["semelhanca"] for r in registros if r.get("semelhanca") is not None]
    media_semelhanca = round(sum(semelhancas) / len(semelhancas), 4) if semelhancas else None

    faixas: dict[str, int] = {}
    for r in registros:
        f = r.get("faixa")
        if f:
            faixas[f] = faixas.get(f, 0) + 1

    return {
        "total_consultas": total,
        "camada_1_total": c1,
        "camada_2_total": c2,
        "proporcao_camada_1": round(c1 / total, 3),
        "proporcao_camada_2": round(c2 / total, 3),
        "distribuicao_faixas": faixas,
        "media_semelhanca": media_semelhanca,
        "votos_positivos": v_pos,
        "votos_negativos": v_neg,
        "taxa_satisfacao": round(v_pos / (v_pos + v_neg), 3) if (v_pos + v_neg) > 0 else None,
    }
