# Histórias de usuário

> Responsável: Ana Júlia (`papel: produto-decisao`). Atualizado em 07/10/2026.
> Requisitos ligados a cada história em [Requisitos](requisitos.md).

**Usuário direto:** o eleitor que recebeu algo num grupo e decide conferir. Quem cai no boato é o
beneficiário; quem manda a mensagem ao bot é o usuário. **Usuários internos:** a equipe que mantém
o bot.

Modelo: *"Eu como [tipo de usuário], quero [ação], para que [benefício]"*. Cada história tem
critérios de aceitação (CA) verificáveis.

## Eleitor

### US-01 — Conferir uma mensagem

Eu como eleitor, quero encaminhar ao bot uma mensagem que recebi num grupo, para que eu saiba se
devo confiar nela antes de repassar.

- CA1: texto encaminhado ou colado recebe resposta em até 5 s.
- CA2: a resposta é uma checagem existente ou uma faixa de alerta, nunca "verdadeiro/falso".

### US-02 — Conferir um link

Eu como eleitor, quero mandar o link de uma notícia, para que eu não precise copiar o texto.

- CA1: o bot extrai título e texto da página e segue o fluxo da US-01.
- CA2: se não conseguir abrir a página, pede para colar o texto.

### US-03 — Ver a checagem que já existe

Eu como eleitor, quero ver se uma agência já checou essa informação, para que eu tenha uma fonte
confiável para mostrar no grupo.

- CA1: mostra alegação, veredito da agência, agência, data e link.
- CA2: só mostra como "já checado" se a semelhança estiver na faixa alta (RN-05).

### US-04 — Receber um alerta quando não há checagem

Eu como eleitor, quero um sinal de alerta quando ninguém checou ainda, para que eu tenha cautela
com o conteúdo.

- CA1: resposta em uma de três faixas, com 2 ou 3 sinais que pesaram no texto.
- CA2: a resposta traz aviso de limitação e links das agências.

### US-05 — Entender o bot

Eu como eleitor que acabou de abrir o bot, quero saber o que ele faz e o que não faz, para que eu
não leia o resultado como sentença.

- CA1: /start e /ajuda explicam em até 5 linhas como usar e os limites.

### US-06 — Saber o que fazer depois

Eu como eleitor, quero dicas de como conferir por conta própria, para que eu não dependa só do
bot.

- CA1: toda resposta termina com links para agências e para o canal do TSE.

### US-07 — Avaliar a resposta

Eu como eleitor, quero dizer se a resposta ajudou, para que o bot melhore.

- CA1: botões 👍/👎 abaixo da resposta; o voto é registrado.

## Equipe

### US-08 — Saber se o modelo pode ir ao ar

Eu como membro da equipe, quero um relatório de métricas do classificador, para que a gente só
mostre a faixa se ela tiver qualidade mínima.

- CA1: relatório com F1, matriz de confusão e falsos alarmes no conjunto de teste (fonte ou época
  diferente do treino), versionado junto com o modelo.
- CA2: o relatório diz `go` ou `no-go` para a camada 2 (RN-04), pelo critério escrito antes de
  rodar.

### US-09 — Acompanhar o uso

Eu como membro da equipe, quero registros anônimos das consultas, para que a gente veja erros e
ajuste limiar e modelo.

- CA1: registro com data, tipo de entrada, camada usada, faixa, semelhança e voto, sem dados
  pessoais.

## Em uma linha

| US | Quem | Quer | Para que |
| --- | --- | --- | --- |
| 01 | eleitor | conferir uma mensagem encaminhada | saber se confia antes de repassar |
| 02 | eleitor | mandar um link | não precisar copiar o texto |
| 03 | eleitor | ver a checagem que já existe | ter fonte para mostrar no grupo |
| 04 | eleitor | receber alerta quando não há checagem | ter cautela |
| 05 | eleitor | entender o que o bot faz | não ler o resultado como sentença |
| 06 | eleitor | dicas de como conferir | não depender só do bot |
| 07 | eleitor | avaliar a resposta | o bot melhorar |
| 08 | equipe | relatório de métricas | só expor a faixa com qualidade mínima |
| 09 | equipe | registros anônimos | ver erros e ajustar |

## O que aconteceu com as histórias anteriores

| História anterior (pattern scoring) | Agora |
| --- | --- |
| US-01 gate de generalização temporal | US-08 CA2 e RN-04 |
| US-02 cobertura da base e atalho de fonte/época | US-08 CA1 (teste com fonte ou época diferente) |
| US-03 score calibrado (ECE, Brier) | fora do MVP: o bot não mostra porcentagem (RNF-06) |
| US-04 falso alarme em notícias verdadeiras | RNF-03 |
| US-05 "fora dos padrões conhecidos" | fora do MVP |
| US-06 mostrar as checagens mais parecidas | US-03 |
| US-07 nunca dar veredito | RN-01 e RNF-07 |
| US-08 gíria não muda a resposta | RNF-04 (benchmark) |
| US-09 não condenar figura muito citada | fora do MVP |
| US-10 rótulos normalizados | RN-02 |
