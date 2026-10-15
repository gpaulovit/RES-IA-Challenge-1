# Engenharia do bot

Guia técnico do bot: como rodar, como testar, onde está cada parte e o que ainda falta. Para o que o bot faz, veja [Funcionalidades do bot](funcionalidades-bot.md). Para os termos, veja o [Glossário](glossario.md).

## Mapa do código

| Arquivo | O que faz |
| --- | --- |
| `src/checagens/bot.py` | Recebe as mensagens do Telegram, decide o tipo, chama a busca e o classificador e monta a resposta. |
| `src/inteligencia/busca.py` | Camada 1: função `buscar(texto, k=3)`, que devolve as checagens mais parecidas. |
| `src/inteligencia/classificador.py` | Camada 2: função `classificar(texto)`, que devolve a faixa de sinais de fake news. |
| `src/checagens/registros.py` | Registro anônimo das consultas e dos votos. |
| `scripts/testar_bot_terminal.py` | Simulador no terminal: mostra a resposta que apareceria no Telegram, sem precisar do token. |
| `tests/test_bot.py` | Testes automatizados do bot. |

## Como rodar localmente

1. Instale as dependências, a partir da raiz do projeto:

   ```bash
   make install
   ```

2. Crie o arquivo `.env` a partir de `.env.example` e preencha, pelo menos:

   ```
   TELEGRAM_BOT_TOKEN=<token do BotFather>
   ```

3. Rode o bot:

   ```bash
   python -m checagens.bot
   ```

   O terminal mostra o que está ligado, por exemplo `camada 1: ligada · camada 2: desligada`.

**Só um computador pode rodar o bot por vez.** Dois programas com o mesmo token disputam as mensagens.

## Variáveis de ambiente

| Variável | Uso | Observação |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Token do bot. Obrigatória. | Também aceita `TELEGRAM_TOKEN`. |
| `MODO_TESTE` | `1` liga o modo de teste, com resultados inventados. | Use só para ver as respostas. |
| `CAMADA2_LIGADA` | `1` liga o classificador de sinais. | Fica desligada até Produto aprovar o relatório da camada 2. |
| `CHECK_LOGS_PATH` | Onde guardar os registros anônimos. | Padrão: `data/registros/consultas.jsonl`. |
| `BOT_MODE` | Consta no `.env.example`. | O código atual não lê essa variável. O bot usa só `polling`. |

Nunca envie o `.env` preenchido para o GitHub.

## Como testar

- **Testes automatizados:**

  ```bash
  make test
  ```

  Os testes do bot ficam em `tests/test_bot.py`. Eles não precisam de internet nem de token.

- **Simulador no terminal:** `python scripts/testar_bot_terminal.py` mostra a resposta para uma mensagem, como o usuário veria no Telegram.

## Como as camadas se conectam

1. Se `MODO_TESTE=1`, o bot usa um modelo de mentira, só para ver as respostas.
2. Senão, o bot tenta importar `buscar` e `classificar` do pacote `inteligencia`.
3. Se o pacote não puder ser importado, o bot roda sem camadas e responde "sem correspondência".
4. A busca devolve resultados já ordenados por semelhança. O bot usa só o primeiro.
5. O classificador só é chamado se `CAMADA2_LIGADA=1`, e não quando a busca acha uma checagem já conferida. Ele roda nas faixas "relacionada" e "sem correspondência".

## Pendências técnicas

- **Texto das respostas:** os textos são de Produto (Ana Júlia). A versão de referência está em [textos-bot.md](engenharia-eduarda/textos-bot.md), e as frases fixas já batem com `src/checagens/bot.py`. Os comentários do `bot.py` já apontam para esse arquivo.
- **Modelo de mentira:** o trecho "MODELO DE MENTIRA" em `bot.py` deve ser apagado quando a busca real estiver ligada em todos os ambientes.
- **Link no meio do texto:** ainda não é reconhecido.
- **Números da base:** a base da busca tem **12.245 checagens** (2013 a 2026), conforme o relatório `data/relatorios/checagens.json` e a confirmação da frente de Dados. Ela inclui o FactPolCheckBr (1.804 checagens, de 1.882 lidas) e o Google Fact Check Tools (1.803 checagens recentes). Por isso, "1.882" não é o total do bot. A página [Dados do bot](dados.md) ainda mostra 10.442, que é o número anterior.
- **`BOT_MODE`:** remover do `.env.example` ou passar a ser lida pelo código.
- **Índice da busca (camada 1):** a busca precisa de um índice de vetores, que fica no DVC (veja [Infraestrutura e MLOps](devops-mlops.md)) e não no Git. Se o índice não existe ou está desatualizado, a busca dá erro. O bot registra o erro no log e responde "nenhum site de checagem conferiu essa notícia ainda". Nesse caso, o terminal continua mostrando "camada 1: ligada", porque o bot só confere se o código da busca foi encontrado, e não se o índice carregou. A busca e o índice são de Modelos. O status mostrado pelo bot é da Engenharia.

## Decisões de quem

| Decisão | Responsável |
| --- | --- |
| Textos das respostas e regras de exibição | Produto |
| Base de checagens e de treino | Dados |
| Modelo, limiares e relatório Go/No-Go da camada 2 | Modelos de IA |
| Código do bot, testes e registros | Engenharia |
| Infraestrutura, deploy e monitoramento | DevOps e MLOps |
