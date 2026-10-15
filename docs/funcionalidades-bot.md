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
