"""Bot do Telegram do projeto: recebe a mensagem, chama as camadas e responde com os textos de produto.

Quem roda o bot é a Ana (só um computador pode rodar o bot por vez). O token fica no .env da raiz,
que não vai para o GitHub. Para rodar: python -m checagens.bot

============================================================================================
VER TODAS AS RESPOSTAS (modo de teste)
============================================================================================

Enquanto a busca e o classificador não existem, o bot responde "Nenhum site de checagem
conferiu essa notícia ainda" para tudo. Para ver as outras respostas, acrescente no .env:
       MODO_TESTE=1
O bot passa a usar o MODELO DE MENTIRA (no fim deste arquivo) e toda resposta começa com
"(Bot em teste: resultado inventado...)". Mande textos com 5 palavras ou mais:
       fala de "pix" ou "banqueiros"           -> Essa notícia já foi conferida
       fala de "pix" e tem "não"               -> Achei uma notícia parecida (filtro de negação)
       fala de "anitta"                        -> Achei uma notícia parecida + alerta curto
       tem "urgente", "compartilhe" ou "!!!"   -> Muitos sinais de fake news
       termina com "?"                         -> Não dá para saber só pelo texto
       qualquer outro                          -> Poucos sinais de fake news
Para voltar ao normal, apague a linha ou troque por MODO_TESTE=0.

============================================================================================
PARA QUEM VAI CONECTAR AS CAMADAS (spec openspec/changes/add-bot-intelligence-layers)
============================================================================================

Não precisa mexer neste arquivo: basta criar os arquivos abaixo com estes nomes e assinaturas.
   Camada 1 (busca):  src/checagens/busca.py
       buscar(texto: str, k: int = 3) -> list[dict]
       O bot usa do primeiro item: faixa ("ja_checado", "relacionada" ou "baixa"), semelhanca,
       alegacao, veredito_original, agencia, data (AAAA-MM-DD) e link.
   Camada 2 (alerta): src/checagens/classificador.py
       classificar(texto: str) -> dict
       O bot usa: faixa ("muitos_sinais", "incerto" ou "poucos_sinais") e sinais (2 ou 3 termos).
- A camada 1 liga sozinha quando busca.py existir.
- A camada 2 só liga com CAMADA2_LIGADA=1 no .env. Produto põe essa linha DEPOIS do "go" no
  relatório da camada 2 (RN-04). Sem ela, o bot responde só com a camada 1.
- Ao rodar, o terminal diz o que está ligado: "camada 1: ligada · camada 2: desligada".
- Quando as duas camadas reais existirem, apague a seção MODELO DE MENTIRA no fim do arquivo.
- Os textos das respostas estão logo abaixo e seguem docs/textos-bot.md. Mudança de texto
  passa por Produto.
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import re
import unicodedata
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

log = logging.getLogger("checagens.bot")

# ---------------------------------------------------------------------------
# Textos (fonte: docs/textos-bot.md). Mudou lá, mude aqui.
# ---------------------------------------------------------------------------

START = (
    "Olá! Eu te ajudo a conferir se uma notícia pode ser fake news.\n"
    "Cole aqui o link da notícia ou a mensagem que você recebeu."
)

AJUDA = (
    "<b>Como usar:</b> cole o link ou a mensagem. Também pode encaminhar direto do grupo.\n"
    "<b>Como eu confiro:</b> vejo se um site de checagem já conferiu essa notícia. "
    "Se não achar, vejo se o texto tem sinais de fake news.\n"
    "<b>Importante:</b> eu não dou a palavra final. Quem confere os fatos são os sites de checagem.\n"
    "<b>Não leio</b> áudio, foto, vídeo nem print. Só texto e link.\n"
    "<b>Não guardo</b> seu nome, seu número nem seu usuário."
)

JA_CHECADO = (
    "🔎 <b>Essa notícia já foi conferida.</b>\n"
    "O site {agencia} conferiu uma notícia igual a essa{em_data}.\n"
    "Notícia: “{alegacao}”\n"
    "Resultado: <b>{veredito}</b>\n"
    "Veja a explicação completa: {link}"
)

RELACIONADA = (
    "🔎 <b>Achei uma notícia parecida que já foi conferida.</b>\n"
    "Atenção: pode não ser exatamente a mesma coisa que você recebeu.\n"
    "Notícia: “{alegacao}”\n"
    "Resultado do site {agencia}: <b>{veredito}</b>\n"
    "Veja a explicação: {link}"
)

FAIXAS = {
    "muitos_sinais": (
        "⚠️ <b>Atenção: essa mensagem tem muitos sinais de fake news.</b>\n"
        "Nenhum site de checagem conferiu essa notícia ainda, mas o jeito que ela foi escrita "
        "lembra outras fake news.\n"
        "{linha_sinais}"
        "Antes de repassar, veja se algum jornal conhecido deu a mesma notícia."
    ),
    "incerto": (
        "❔ <b>Não dá para saber só pelo texto.</b>\n"
        "Nenhum site de checagem conferiu essa notícia ainda, e o jeito que ela foi escrita "
        "não ajuda a decidir.\n"
        "{linha_sinais}"
        "Na dúvida, não repasse antes de conferir."
    ),
    "poucos_sinais": (
        "🟦 <b>Poucos sinais de fake news.</b>\n"
        "Nenhum site de checagem conferiu essa notícia ainda, e o jeito que ela foi escrita "
        "não lembra fake news.\n"
        "Mas isso não garante que ela seja verdade.\n"
        "Se for repassar, veja se algum jornal conhecido deu a mesma notícia."
    ),
}

FAIXA_CURTA = {
    "muitos_sinais": "tem muitos sinais de fake news.",
    "incerto": "não dá para saber só pelo texto.",
    "poucos_sinais": "tem poucos sinais de fake news.",
}

NAO_ENCONTREI = (
    "🔎 <b>Nenhum site de checagem conferiu essa notícia ainda.</b>\n"
    "Isso não quer dizer que ela é verdade nem mentira. Pode ser um assunto novo.\n"
    "Antes de repassar, veja se algum jornal conhecido deu a mesma notícia."
)

AVISO_E_LINKS = (
    "ℹ️ Sou um robô e posso errar. Quem confere os fatos são os sites de checagem.\n"
    "<b>Confira você também:</b>\n"
    "• Fato ou Boato, da Justiça Eleitoral: https://www.justicaeleitoral.jus.br/fato-ou-boato\n"
    "• Aos Fatos: https://www.aosfatos.org\n"
    "• Agência Lupa: https://www.agencialupa.org\n"
    "• Comprova: https://projetocomprova.com.br\n"
    "• Fato ou Fake, do g1: https://g1.globo.com/fato-ou-fake/"
)

ERRO_LINK = (
    "Não consegui abrir esse link. 😕\n"
    "Pode copiar e colar aqui o texto da notícia? Só o título e o começo já ajudam."
)
ERRO_MIDIA = (
    "Por enquanto eu só leio texto e link. Não consigo ouvir áudio nem ver foto, vídeo ou print.\n"
    "Se a mensagem tinha texto, cole aqui. Se for um vídeo da internet, mande o link."
)
ERRO_CURTO = (
    "Essa mensagem é muito curta para eu conferir.\n"
    "Pode mandar a mensagem inteira, do jeito que ela chegou para você?"
)
ERRO_INTERNO = "Deu um problema aqui e não consegui conferir agora. Tente de novo daqui a pouco."
OBRIGADO = "Obrigado! Sua resposta ajuda a melhorar o bot."

AVISO_TESTE = "<i>(Bot em teste: a busca de checagens ainda não está ligada.)</i>"
AVISO_MODELO_FALSO = "<i>(Bot em teste: resultado inventado, só para ver as respostas.)</i>"

MIN_PALAVRAS = 5          # RF-11
MAX_ALEGACAO = 160        # cabe no limite de 600 caracteres (RNF-06)
PADRAO_LINK = re.compile(r"https?://\S+", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Configuração: lê o .env da raiz do projeto
# ---------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[2]


def carregar_env(caminho: Path = RAIZ / ".env") -> None:
    """Lê linhas CHAVE=valor (ou export CHAVE=valor) sem sobrescrever o que já está definido."""
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.removeprefix("export ").split("=", 1)
        valor = valor.strip().strip('"').strip("'")
        os.environ.setdefault(chave.strip(), valor)


def ligado(nome: str) -> bool:
    return os.getenv(nome, "").strip().lower() in {"1", "true", "sim", "yes"}


# ---------------------------------------------------------------------------
# Conexão com as camadas
# ---------------------------------------------------------------------------

def carregar_camadas():
    """Devolve (buscar, classificar, modo). Cada função pode ser None se ainda não existir."""
    if ligado("MODO_TESTE"):
        return buscar_falso, classificar_falso, "falso"

    try:
        from checagens.busca import buscar
    except ImportError:
        buscar = None
    classificar = None
    if ligado("CAMADA2_LIGADA"):  # RN-04: só depois do "go" no relatório da camada 2
        try:
            from checagens.classificador import classificar
        except ImportError:
            log.warning("CAMADA2_LIGADA=1, mas checagens.classificador não existe ainda.")
    return buscar, classificar, "real"


# ---------------------------------------------------------------------------
# Entrada: tipo, link e extração de texto (RF-03, RF-04, RF-11)
# ---------------------------------------------------------------------------

def tipo_de_texto(texto: str) -> str:
    texto = (texto or "").strip()
    if PADRAO_LINK.fullmatch(texto):
        return "link"
    if len(re.findall(r"\w+", texto)) < MIN_PALAVRAS:
        return "curto"
    return "texto"


class _ExtratorHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.titulo, self.descricao, self.paragrafos = "", "", []
        self._em_titulo = self._em_p = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._em_titulo = True
        elif tag == "p":
            self._em_p = True
            self.paragrafos.append("")
        elif tag == "meta" and a.get("property") in {"og:title", "og:description"}:
            if a["property"] == "og:title" and a.get("content"):
                self.titulo = self.titulo or a["content"]
            elif a.get("content"):
                self.descricao = a["content"]

    def handle_endtag(self, tag):
        if tag == "title":
            self._em_titulo = False
        elif tag == "p":
            self._em_p = False

    def handle_data(self, data):
        if self._em_titulo and not self.titulo:
            self.titulo = data.strip()
        elif self._em_p and self.paragrafos:
            self.paragrafos[-1] += data


def extrair_texto_do_link(url: str) -> str | None:
    """RF-03: título + descrição + primeiros parágrafos. None se a página não abrir (RF-04)."""
    try:
        pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(pedido, timeout=8) as resposta:
            if resposta.status != 200 or "html" not in resposta.headers.get("Content-Type", ""):
                return None
            pagina = resposta.read(2_000_000).decode(resposta.headers.get_content_charset() or "utf-8", "replace")
    except Exception:
        return None
    extrator = _ExtratorHTML()
    extrator.feed(pagina)
    partes = [extrator.titulo, extrator.descricao]
    partes += [p.strip() for p in extrator.paragrafos if len(p.strip()) > 40][:3]
    texto = " ".join(p for p in partes if p).strip()
    return texto[:2000] if len(re.findall(r"\w+", texto)) >= MIN_PALAVRAS else None


# ---------------------------------------------------------------------------
# Montagem da resposta (tabela "Como uma resposta é montada" em docs/textos-bot.md)
# ---------------------------------------------------------------------------

def _data_br(data: str | None) -> str:
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", data or "")
    return f" em {m.group(3)}/{m.group(2)}/{m.group(1)}" if m else ""


def _cortar(texto: str, limite: int = MAX_ALEGACAO) -> str:
    texto = " ".join((texto or "").split())
    return texto if len(texto) <= limite else texto[: limite - 1].rstrip() + "…"


def _checagem(modelo: str, c: dict) -> str:
    e = html.escape
    return modelo.format(
        agencia=e(c.get("agencia") or "de checagem"),
        em_data=_data_br(c.get("data")),
        alegacao=e(_cortar(c.get("alegacao", ""))),
        veredito=e(c.get("veredito_original") or "ver no site"),
        link=e(c.get("link") or ""),
    )


def _linha_sinais(sinais) -> str:
    sinais = [s for s in (sinais or []) if s][:3]
    if not sinais:
        return ""
    return "Palavras que chamaram atenção: " + ", ".join(f"“{html.escape(s)}”" for s in sinais) + "\n"


def montar_resposta(texto: str, buscar, classificar, modo: str) -> tuple[str, dict]:
    """Devolve (mensagem, dados para o registro anônimo)."""
    partes: list[str] = []
    registro = {"camada": 1, "faixa": None, "semelhanca": None}

    if modo == "falso":
        partes.append(AVISO_MODELO_FALSO)
    elif buscar is None:
        partes.append(AVISO_TESTE)

    melhor = None
    if buscar is not None:
        resultados = buscar(texto, k=3)
        melhor = resultados[0] if resultados else None
    if melhor:
        registro["semelhanca"] = melhor.get("semelhanca")

    faixa_busca = melhor.get("faixa") if melhor else "baixa"

    if faixa_busca == "ja_checado":
        partes.append(_checagem(JA_CHECADO, melhor))
    elif faixa_busca == "relacionada":
        partes.append(_checagem(RELACIONADA, melhor))
        if classificar is not None:
            alerta = classificar(texto)
            registro.update(camada=2, faixa=alerta["faixa"])
            curta = f"Sobre a sua mensagem: <b>{FAIXA_CURTA[alerta['faixa']]}</b>"
            if alerta["faixa"] != "poucos_sinais" and alerta.get("sinais"):
                curta += "\n" + _linha_sinais(alerta["sinais"]).rstrip("\n")
            partes.append(curta)
    elif classificar is not None:
        alerta = classificar(texto)
        registro.update(camada=2, faixa=alerta["faixa"])
        sinais = "" if alerta["faixa"] == "poucos_sinais" else _linha_sinais(alerta.get("sinais"))
        partes.append(FAIXAS[alerta["faixa"]].format(linha_sinais=sinais))
    else:
        partes.append(NAO_ENCONTREI)

    partes.append(AVISO_E_LINKS)
    return "\n\n".join(partes), registro


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def botoes_avaliacao(id_consulta: str | None) -> InlineKeyboardMarkup:
    ref = id_consulta or "-"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("👍", callback_data=f"voto:{ref}:positivo"),
        InlineKeyboardButton("👎", callback_data=f"voto:{ref}:negativo"),
    ]])


async def enviar(update: Update, texto: str, botoes: InlineKeyboardMarkup | None = None) -> None:
    await update.effective_message.reply_text(
        texto, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=botoes,
    )


def registrar(tipo_entrada: str, dados: dict) -> str | None:
    """RF-13: registro anônimo. Se falhar, o bot responde mesmo assim."""
    try:
        from checagens.registros import registrar_consulta
        return registrar_consulta(tipo_entrada=tipo_entrada, **dados)["id_consulta"]
    except Exception:
        log.exception("Não foi possível registrar a consulta")
        return None


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await enviar(update, START)


async def cmd_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await enviar(update, AJUDA)


async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE, texto: str) -> None:
    tipo = tipo_de_texto(texto)
    if tipo == "curto":
        await enviar(update, ERRO_CURTO)
        return
    if tipo == "link":
        extraido = await asyncio.to_thread(extrair_texto_do_link, texto.strip())
        if extraido is None:
            await enviar(update, ERRO_LINK)
            return
        texto = extraido

    buscar, classificar, modo = context.bot_data["camadas"]
    resposta, dados = await asyncio.to_thread(montar_resposta, texto, buscar, classificar, modo)
    id_consulta = registrar(tipo, dados)
    await enviar(update, resposta, botoes_avaliacao(id_consulta))


async def msg_texto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await responder_texto(update, context, update.effective_message.text)


async def msg_midia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    legenda = update.effective_message.caption
    if legenda:  # foto ou vídeo com legenda: usa a legenda como texto
        await responder_texto(update, context, legenda)
    else:
        await enviar(update, ERRO_MIDIA)


async def voto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    consulta = update.callback_query
    await consulta.answer()
    await consulta.edit_message_reply_markup(reply_markup=None)
    _, id_consulta, valor = (consulta.data.split(":") + ["", ""])[:3]
    if id_consulta and id_consulta != "-":
        try:
            from checagens.registros import registrar_voto
            registrar_voto(id_consulta, valor)
        except Exception:
            log.exception("Não foi possível registrar o voto")
    await consulta.message.reply_text(OBRIGADO)


async def erro(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Erro ao responder", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(ERRO_INTERNO)


# ---------------------------------------------------------------------------
# MODELO DE MENTIRA (só com MODO_TESTE=1). Apague esta seção quando busca.py e
# classificador.py existirem. As três checagens são reais (FactPolCheckBr), mas a
# semelhança é inventada por palavras-chave. Ver "VER TODAS AS RESPOSTAS" no topo.
# ---------------------------------------------------------------------------

def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.split())


def _palavras(texto: str) -> set[str]:
    return set(re.findall(r"\w+", _normalizar(texto)))


CHECAGENS_FALSAS = [
    {
        "id": "falso-001",
        "alegacao": "Banqueiros definem apoio a Lula em troca da revogação do Pix",
        "veredito_original": "Falso",
        "veredito_normalizado": "falso",
        "agencia": "Boatos.org",
        "data": "2022-08-01",
        "link": "https://www.boatos.org/politica/banqueiros-definem-apoio-lula-troca-revogacao-pix.html",
        "fonte_dataset": "FactPolCheckBr",
        "gatilhos": {"pix", "banqueiros", "banqueiro"},
    },
    {
        "id": "falso-002",
        "alegacao": "Anitta retira apoio à candidatura de Lula e pula do barco",
        "veredito_original": "Falso",
        "veredito_normalizado": "falso",
        "agencia": "Boatos.org",
        "data": "2022-10-17",
        "link": "https://www.boatos.org/politica/anitta-retira-apoio-a-candidatura-de-lula-e-pula-do-barco.html",
        "fonte_dataset": "FactPolCheckBr",
        "gatilhos": {"anitta"},
    },
    {
        "id": "falso-003",
        "alegacao": "Renner declara apoio a Lula e fecha parceria com o PT",
        "veredito_original": "Falso",
        "veredito_normalizado": "falso",
        "agencia": "Boatos.org",
        "data": "2022-08-05",
        "link": "https://www.boatos.org/politica/renner-declara-apoio-a-lula-e-fecha-parceria-com-o-pt.html",
        "fonte_dataset": "FactPolCheckBr",
        "gatilhos": {"renner"},
    },
]

NEGACAO_FALSA = {"nao", "nunca", "nem", "jamais"}
ALERTA_FALSO = ["urgente", "compartilhe", "repasse", "divulguem", "midia esconde", "absurdo", "!!!"]


def buscar_falso(texto: str, k: int = 3) -> list[dict]:
    if not texto or not texto.strip():
        raise ValueError("Informe um texto com conteúdo para buscar.")
    palavras = _palavras(texto)
    resultados = []
    for c in CHECAGENS_FALSAS:
        if c["gatilhos"] & palavras:
            semelhanca = 0.72 if c["id"] == "falso-002" else 0.91
        else:
            semelhanca = 0.30
        faixa = "ja_checado" if semelhanca >= 0.85 else "relacionada" if semelhanca >= 0.60 else "baixa"
        if faixa == "ja_checado" and bool(palavras & NEGACAO_FALSA) != bool(_palavras(c["alegacao"]) & NEGACAO_FALSA):
            faixa = "relacionada"  # RN-06
        item = {chave: valor for chave, valor in c.items() if chave != "gatilhos"}
        resultados.append({**item, "semelhanca": semelhanca, "faixa": faixa})
    resultados.sort(key=lambda r: -r["semelhanca"])
    return resultados[:k]


def classificar_falso(texto: str) -> dict:
    normal = _normalizar(texto)
    sinais = [termo for termo in ALERTA_FALSO if termo in normal]
    if sinais:
        return {"faixa": "muitos_sinais", "sinais": sinais[:3]}
    if texto.strip().endswith("?"):
        longas = sorted(_palavras(texto), key=len, reverse=True)
        return {"faixa": "incerto", "sinais": longas[:2]}
    return {"faixa": "poucos_sinais", "sinais": []}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # não imprimir o token nos logs
    carregar_env()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token == "seu_token_aqui":
        raise SystemExit("Coloque o token do BotFather no arquivo .env na raiz do projeto.")

    buscar, classificar, modo = carregar_camadas()
    app = Application.builder().token(token).build()
    app.bot_data["camadas"] = (buscar, classificar, modo)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ajuda", cmd_ajuda))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_texto))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND & ~filters.StatusUpdate.ALL, msg_midia))
    app.add_handler(CallbackQueryHandler(voto, pattern=r"^voto:"))
    app.add_error_handler(erro)

    situacao = {
        "falso": "MODO DE TESTE: respostas com resultado inventado",
        "real": f"camada 1: {'ligada' if buscar else 'ainda não existe'} · "
                f"camada 2: {'ligada' if classificar else 'desligada'}",
    }[modo]
    print(f"Bot rodando ({situacao}). Abra o Telegram e mande /start. Ctrl+C para parar.")
    app.run_polling()


if __name__ == "__main__":
    main()