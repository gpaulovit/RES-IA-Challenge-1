# ChecaAÍ: bot de checagem para as eleições de 2026

Bot no Telegram para quem recebeu uma mensagem ou link sobre as eleições de 2026 e quer saber,
antes de repassar, se aquilo já foi conferido por uma agência de checagem. O bot nunca dá
veredito próprio de "verdade" ou "mentira": ele mostra o que uma agência apurou.

**Bot:** [@checaai_bot](https://t.me/checaai_bot) · **Documentação:** [gpaulovit.github.io/RES-IA-Challenge-1](https://gpaulovit.github.io/RES-IA-Challenge-1/)

## O produto

Abra o [@checaai_bot](https://t.me/checaai_bot), mande `/start` e cole (ou encaminhe) a mensagem ou o link.

| Situação | Resposta do bot |
|---|---|
| Uma agência já checou essa alegação | **Já checado:** veredito da agência e link da checagem |
| Há uma checagem sobre assunto parecido | **Notícia parecida:** a checagem, com o aviso de que pode não ser a mesma coisa |
| Nenhuma agência checou | **Não encontrei:** isso não quer dizer que é verdade nem mentira; indica onde conferir |

Toda resposta traz os links do Fato ou Boato (Justiça Eleitoral) e das agências, e botões 👍/👎.
O bot lê texto e link (não lê áudio, foto, vídeo nem print) e não guarda nome, número nem
usuário do Telegram.

## Como a IA funciona

- **Camada 1, busca de checagens (no ar):** compara a mensagem com 12.245 checagens de agências
  brasileiras (2013 a 2026). Usa embeddings multilíngues (MiniLM), busca por nomes e palavras
  raras e um reranker que relê mensagem e checagem juntas. Se só um dos textos tem negação, a
  resposta nunca é "já checado".
- **Camada 2, sinais de alerta (fora do ar):** classificador TF-IDF + regressão logística.
  **Não passou** no critério definido antes do teste (F1 0,67 e falso alarme de 31%; metas 0,75
  e 15%): aprendeu o estilo da fonte, não sinais de desinformação. Por isso não é exibida (RN-04).

Detalhes, métricas e aprendizados: [relatório técnico](docs/relatorio-tecnico.md) ·
[relatório da camada 2](docs/relatorio-camada2.md).

## Entrega final

| Item | Onde está |
|---|---|
| Descrição do produto | esta página |
| Requisitos funcionais e não funcionais | [docs/requisitos.md](docs/requisitos.md) · [histórias de usuário](docs/historias.md) |
| Guiding Questions | [docs/perguntas.md](docs/perguntas.md) |
| Datasets e análise exploratória | [docs/dados.md](docs/dados.md) (bases regeneradas com `dvc repro`) |
| Modelo de IA e relatório técnico | [src/inteligencia/](src/inteligencia/README.md) · [relatório técnico](docs/relatorio-tecnico.md) |
| Organização e papéis | [Equipe](#equipe) |
| Infraestrutura e MLOps | [docs/devops-mlops.md](docs/devops-mlops.md) |

## Equipe

| Integrante | Frente | Responsável por |
|---|---|---|
| Ana Júlia | Produto e Decisão | requisitos, textos e fluxo do bot, decisões go/no-go |
| Cibelly Lourenço | Domínio de Dados | bases de checagens e de treino |
| Eduarda | Engenharia de Software | bot no Telegram e leitura de links |
| Paulo | Modelos de IA | busca (camada 1), classificador (camada 2) e relatório go/no-go |
| Ingrid Soares | DevOps e MLOps | Azure, CI/CD, DVC, MLflow, Docker e testes |

## Como rodar

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[busca,test]' dvc
dvc repro indice            # monta a base de checagens e o índice da busca
python -m pytest -q         # testes
python -m checagens.bot     # precisa de TELEGRAM_BOT_TOKEN no .env (copie o .env.example)
```

Sem Telegram, para ver as respostas no terminal: `python scripts/testar_bot_terminal.py`.
Só um computador pode rodar o bot por vez. Mais detalhes: [engenharia do bot](docs/engenharia-bot.md).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| [src/checagens/](src/checagens/) | bot, mensagens, registros anônimos e montagem das bases |
| [src/inteligencia/](src/inteligencia/README.md) | camadas 1 e 2 (`buscar()` e `classificar()`) |
| [experiments/](experiments/README.md) | notebooks de análise e comparação de modelos |
| [scripts/](scripts/) | atualização de checagens (Google Fact Check), latência, deploy |
| [tests/](tests/) | testes automáticos (rodam no CI) |
| [docs/](docs/) | documentação publicada no GitHub Pages |
| [archive/](archive/README.md) | produtos descartados; não usar como referência |
