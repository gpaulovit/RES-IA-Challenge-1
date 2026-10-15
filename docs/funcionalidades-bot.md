# Funcionalidades do bot

Este documento explica **o que o bot faz** quando alguém conversa com ele no Telegram. Ele não traz os textos das mensagens: quem define os textos é a frente de Produto (veja [Requisitos](requisitos.md)).

## Comandos

| Comando | O que acontece |
| --- | --- |
| `/start` | O bot se apresenta e pede para colar o link ou a mensagem recebida. |
| `/ajuda` | O bot explica como usar, como ele confere, o que não faz e o que não guarda. |

## O que a pessoa pode mandar

| Tipo de mensagem | O que o bot faz |
| --- | --- |
| **Só um link** | Abre a página e pega o título, a descrição e os primeiros parágrafos. Se a página não abrir, pede para colar o texto. |
| **Texto com 5 palavras ou mais** | Confere o texto. |
| **Texto com menos de 5 palavras** | Não confere e pede a mensagem inteira. |
| **Foto ou vídeo com legenda** | Usa a legenda como texto. |
| **Foto, vídeo, áudio ou print sem legenda** | Avisa que só lê texto e link. |

Um link que aparece **no meio** de uma frase ainda não é aberto. Nesse caso, o bot trata a mensagem como texto comum.

## Como o bot responde

Ele confere nesta ordem:

1. **Procura uma checagem parecida** (camada 1). O resultado cai em uma destas faixas:
   - **Já conferida:** mostra a agência, a notícia, o veredito, a data e o link da explicação.
   - **Relacionada:** mostra a mesma informação, com o aviso de que pode não ser exatamente a mesma notícia.
   - **Sem correspondência:** nenhuma checagem parecida foi encontrada.
2. **Olha os sinais do texto** (camada 2), se ela estiver ligada. Essa camada fica desligada até Produto aprovar o relatório. Quando está ligada, o bot pode indicar:
   - muitos sinais de fake news;
   - não dá para saber só pelo texto;
   - poucos sinais de fake news.
3. **Sempre** termina com o aviso de que o bot pode errar e com a lista de sites de checagem para conferir.

O bot **nunca dá veredito próprio** de verdade ou mentira. Se nada for encontrado, ele diz isso, sem concluir nada.

## Votação

Toda resposta com resultado traz os botões 👍 e 👎. O voto é guardado de forma anônima e o bot agradece.

## Privacidade

- O bot não guarda nome, usuário, número de telefone nem ID do Telegram.
- Cada consulta vira um registro anônimo, com data, tipo da mensagem, faixa e semelhança.
- Detalhes técnicos estão em `src/checagens/registros.py`.

## Limites conhecidos

- Não lê áudio, foto, vídeo nem print, a não ser pela legenda.
- Não reconhece link no meio do texto.
- Os resultados dependem das checagens disponíveis. Notícia nova ou fora da base aparece como "sem correspondência".

## Requisitos (RF) e como testar cada um

Os requisitos completos estão em [Requisitos](requisitos.md). Aqui está o que o bot faz para cada RF, e como conferir.

**Situação:**
- **Feito:** implementado e com teste automático.
- **Feito, sem teste automático:** implementado; conferido na mão com o simulador.
- **Aguarda decisão:** código pronto, mas só funciona depois de uma decisão de outra frente.
- **Fora do bot:** responsabilidade de outra frente.

| RF | O que o bot faz | Situação | Como testar |
| --- | --- | --- | --- |
| RF-01 | Recebe texto, inclusive encaminhado, e responde. | Feito, sem teste automático | Simulador: `python scripts/testar_bot_terminal.py` |
| RF-02 | `/start` e `/ajuda` explicam o uso e os limites. | Feito, sem teste automático | Simulador ou Telegram (`/start`, `/ajuda`) |
| RF-03 | Abre o link e extrai título e texto principal. | Feito | `pytest tests/test_bot.py -k extrai_titulo` |
| RF-04 | Se o link não abre, pede para colar o texto. | Feito (o teste confere o `None`; a mensagem é enviada pelo bot) | `pytest tests/test_bot.py -k "erro_http or sem_internet"` |
| RF-05 | Limpa e normaliza o texto antes da busca. | Feito (dentro da busca) | `pytest tests/test_normalizacao.py` |
| RF-06 | Busca as 3 checagens mais parecidas. | Código integrado ao bot. A busca só devolve resultados com o índice disponível. | `pytest tests/test_busca.py -k contrato_k_padrao` |
| RF-07 | Mostra "já checado" ou "relacionada", com agência, data e link. | Feito, testado com o modo de teste do bot | `pytest tests/test_bot.py -k "ja_conferida or relacionada or negacao"` |
| RF-08 | Sem checagem parecida, mostra a faixa de alerta com os sinais. | Aguarda decisão (go/no-go do Paulo; liga com `CAMADA2_LIGADA=1`) | `pytest tests/test_classificador.py` |
| RF-09 | Toda resposta traz aviso e links das agências e do TSE. | Feito | `pytest tests/test_bot.py -k aviso_de_robo` |
| RF-10 | Áudio, foto, vídeo ou figurinha recebe a resposta "só texto e link". | Feito, sem teste automático | Simulador, com uma mensagem de mídia |
| RF-11 | Texto com menos de 5 palavras pede mais contexto. | Feito | `pytest tests/test_bot.py -k "menos_de_cinco or cinco_palavras"` |
| RF-12 | Botões 👍/👎 e registro do voto. | Feito (o registro do voto é testado; o botão não) | `pytest tests/test_registros.py -k voto` |
| RF-13 | Registro anônimo de cada consulta. | Feito | `pytest tests/test_registros.py` |
| RF-14 | Treino gera modelo e métricas com um comando. | Fora do bot (Modelos) | `pytest tests/test_classificador.py -k semente` |

**Para rodar todos os testes do bot de uma vez:** `python -m pytest tests/test_bot.py`.
