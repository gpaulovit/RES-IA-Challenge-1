# Requisitos

> Responsável: Ana Júlia (`papel: produto-decisao`). Atualizado em 07/10/2026.
> Histórias ligadas a cada requisito em [Histórias de usuário](historias.md); contexto do problema
> e dos dados em [Perguntas](perguntas.md).

## O produto

Um bot no Telegram para quem recebeu uma mensagem ou link sobre as eleições de 2026 e quer saber,
antes de repassar, se aquilo já foi desmentido ou se tem cara de desinformação. **O bot nunca dá
veredito próprio de "verdade" ou "mentira".**

```
mensagem ou link
      │
      ▼
extrai e limpa o texto ──(link quebrado)──► pede para colar o texto
      │
      ▼
CAMADA 1 · busca checagens de agências parecidas
      │
      ├── semelhança alta ──► "Já foi checado": alegação, veredito da agência, data, link
      ├── semelhança média ─► "Checagem relacionada" + segue para a camada 2
      └── semelhança baixa ─► segue para a camada 2
                                   │
                                   ▼
                    CAMADA 2 · classificador de sinais de alerta
                    muitos sinais / incerto / poucos sinais
                                   │
                                   ▼
            toda resposta: aviso de limitação + links das agências e do TSE
```

A camada 1 é factual (o veredito é de uma agência) e reaproveita a busca já construída
(`busca.py`, `embeddings.py`, `retrieval.py`). A camada 2 responde ao desafio ("é fake ou não?")
sem prometer o que um modelo de estilo de texto não garante.

### Decisões

| Decisão | Escolha |
| --- | --- |
| Canal | Telegram, conversa privada com o bot |
| Entradas aceitas | texto (inclusive mensagem encaminhada de grupo) e link de notícia |
| Saída | checagem existente **ou** faixa de alerta, nunca "verdadeiro/falso" |
| Modelo de reincidência | descartado; a busca do repositório vira a camada 1 |
| Classificador | baseline simples (TF-IDF + regressão logística); algo mais complexo só se sobrar tempo |
| Idioma | português; FakeNewsNet sai por ser em inglês |
| Entrega | 13/10/2026 |

**Fora de escopo:** imagem, áudio, vídeo e prints; WhatsApp; checar fatos inéditos em tempo real;
LLM gerando veredito; retreino automático.

## Requisito de negócio

**RNeg-01:** reduzir a circulação de desinformação eleitoral nas eleições de 2026, ajudando
eleitores a conferir uma mensagem antes de repassá-la.

## Requisitos funcionais

| ID | Requisito | História |
| --- | --- | --- |
| RF-01 | O bot recebe mensagens de texto em conversa privada, inclusive mensagens encaminhadas de grupos, e responde a cada uma. | US-01 |
| RF-02 | Os comandos /start e /ajuda explicam como usar o bot e o que ele não faz. | US-05 |
| RF-03 | Ao receber um link, o bot extrai o título e o texto principal da página. | US-02 |
| RF-04 | Se a extração do link falhar, o bot pede para o usuário colar o texto. | US-02 |
| RF-05 | O texto passa por limpeza e normalização antes da busca e do classificador. | US-01 |
| RF-06 | O bot busca as 3 checagens mais parecidas na base de agências. | US-03 |
| RF-07 | Conforme a faixa de semelhança (RN-05), o bot mostra a checagem como "já checado" ou "relacionada", com alegação, veredito da agência, agência, data e link. | US-03 |
| RF-08 | Se nenhuma checagem tiver semelhança alta, o classificador devolve uma de três faixas de alerta com 2 ou 3 sinais que pesaram no texto. | US-04 |
| RF-09 | Toda resposta termina com aviso de limitação e links de agências de checagem e do TSE. | US-04, US-06 |
| RF-10 | Áudio, imagem, vídeo e figurinha recebem resposta dizendo que o bot só aceita texto e link. | US-01 |
| RF-11 | Textos com menos de 5 palavras recebem pedido de mais contexto. | US-01 |
| RF-12 | Cada resposta traz botões 👍/👎 e o voto é registrado. | US-07 |
| RF-13 | Cada consulta gera um registro anônimo (data, tipo de entrada, camada, faixa, semelhança, voto). | US-09 |
| RF-14 | O treino gera modelo, métricas e parâmetros versionados juntos, por um único comando. | US-08 |

## Regras de negócio

- **RN-01:** o bot nunca afirma que algo é verdadeiro ou falso; vereditos só vêm de agências e
  são atribuídos a elas.
- **RN-02:** vereditos das agências são normalizados para *falso*, *enganoso*, *verdadeiro* ou
  *outro*, mantendo o rótulo original.
- **RN-03:** nenhum dado pessoal (nome, usuário, telefone, ID do Telegram) é guardado.
- **RN-04:** a camada 2 só aparece para o usuário se o classificador passar no critério escrito
  antes de rodar (RNF-02 e RNF-03), testado com fonte ou época diferente do treino. Sem isso, o
  bot responde só com a camada 1 e, quando não houver checagem, diz que não encontrou e indica as
  agências.
- **RN-05:** faixas de semelhança da camada 1 (ponto de partida; recalibrar com o benchmark):

  | Semelhança com a checagem mais próxima | O bot diz | O bot faz |
  | --- | --- | --- |
  | alta (≥ 0,85) | "Essa informação já foi checada" | mostra a checagem |
  | média (0,60 a 0,85) | "Encontrei uma checagem relacionada" | mostra a checagem com ressalva e roda a camada 2 |
  | baixa (< 0,60) | — | roda a camada 2 |

- **RN-06:** se a consulta e a checagem divergirem em negação ("fez" × "NÃO fez"), a resposta
  cai para "relacionada". Embeddings dão semelhança alta para frases de sentido oposto.
- **RN-07:** formato fixo da resposta: situação da consulta → resumo da alegação checada →
  veredito da agência → link e data → aviso de limitação → links das agências.

## Restrições

- **R-01:** Python, Telegram e as bases listadas em [Perguntas](perguntas.md).
- **R-02:** custo zero de infraestrutura.
- **R-03:** entrega em 13/10/2026.

## Requisitos não funcionais

Os alvos numéricos são provisórios: a equipe confirma ou ajusta na sexta (09/10), com o primeiro
resultado em mãos, e registra o motivo aqui.

| ID | Atributo | Requisito | Como medir |
| --- | --- | --- | --- |
| RNF-01 | Desempenho | Resposta em até 5 s para texto e 10 s para link. | 30 mensagens de teste; 90% dentro do tempo |
| RNF-02 | Qualidade do classificador | F1 macro ≥ 0,75 no teste com fonte ou época diferente do treino. | relatório de métricas (RF-14) |
| RNF-03 | Falso alarme | No máximo 15% das notícias verdadeiras caem em *muitos sinais de alerta*. | mesmo relatório |
| RNF-04 | Qualidade da busca | A checagem certa aparece entre as 3 primeiras em ≥ 70% dos 24 casos de gíria, apelido, erro ortográfico e recorrência temporal. | [`data/testes_benchmark.json`](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/data/testes_benchmark.json) |
| RNF-05 | Falso positivo da busca | No máximo 2 dos 32 controles (notícias reais) aparecem como "já checado"; os 6 casos de negação são relatados à parte. | mesmo benchmark |
| RNF-06 | Clareza | Respostas em português simples, sem número de probabilidade, com até 600 caracteres antes dos links. | revisão de Produto nas 30 mensagens |
| RNF-07 | Transparência | 100% das respostas com fonte (camada 1) ou aviso de limitação (camada 2). | testes automáticos |
| RNF-08 | Privacidade (LGPD) | Nenhum dado pessoal nos registros. | inspeção do arquivo de registro |
| RNF-09 | Robustez | Nenhuma entrada (vazia, longa, mídia, link quebrado) derruba o bot. | testes automáticos com entradas ruins |
| RNF-10 | Reprodutibilidade | Treino com semente fixa; mesmos dados e código geram as mesmas métricas. | rodar o treino duas vezes |
| RNF-11 | Manutenção | Novas checagens entram na base sem retreinar o classificador. | reindexar e consultar uma checagem nova |
| RNF-12 | Disponibilidade | Bot no ar durante a apresentação; vídeo gravado como plano B. | ensaio de 13/10 |

## Priorização (MoSCoW)

Se o prazo apertar, corta-se de baixo para cima: primeiro Could, depois Should. Must é o mínimo
para apresentar.

| Prioridade | Requisitos | Por quê |
| --- | --- | --- |
| **Must** | RF-01 a RF-10; RNF-01, RNF-02, RNF-06, RNF-07, RNF-09, RNF-12 | fluxo completo do bot e o mínimo de honestidade e estabilidade para a demo |
| **Should** | RF-11, RF-14; RNF-03, RNF-04, RNF-05, RNF-08, RNF-10 | sustentam as métricas e a defesa técnica |
| **Could** | RF-12, RF-13; RNF-11 | fecham o ciclo de feedback, mas a demo funciona sem eles |
| **Won't (agora)** | imagem, áudio e vídeo; WhatsApp; checagem de fato inédito; LLM gerando veredito; retreino automático | inviáveis no prazo ou contrários à RN-01 |

## Em uma linha

| ID | Resumo |
| --- | --- |
| RF-01 | Recebe texto (inclusive encaminhado) e responde |
| RF-02 | /start e /ajuda explicam uso e limites |
| RF-03 | Recebe link e extrai título + texto |
| RF-04 | Se o link falhar, pede para colar o texto |
| RF-05 | Limpa e normaliza o texto |
| RF-06 | Busca as 3 checagens mais parecidas |
| RF-07 | Mostra checagem "já checada" ou "relacionada" com veredito, agência, data e link |
| RF-08 | Sem checagem parecida: classificador dá faixa + 2 ou 3 sinais |
| RF-09 | Toda resposta tem aviso + links das agências e do TSE |
| RF-10 | Áudio, imagem, vídeo: avisa que só aceita texto e link |
| RF-11 | Texto com menos de 5 palavras: pede mais contexto |
| RF-12 | Botões 👍/👎 em cada resposta |
| RF-13 | Registro anônimo de cada consulta |
| RF-14 | Treino gera modelo + métricas versionados com 1 comando |
| RNF-01 | Responde em até 5 s (texto) e 10 s (link) |
| RNF-02 | Classificador com F1 ≥ 0,75 em teste de outra fonte ou época |
| RNF-03 | No máximo 15% de notícias verdadeiras com alerta alto |
| RNF-04 | Checagem certa no top-3 em ≥ 70% das reescritas do benchmark |
| RNF-05 | No máximo 2 de 32 notícias reais aparecem como "já checado" |
| RNF-06 | Português simples, sem porcentagem, até 600 caracteres |
| RNF-07 | 100% das respostas com fonte ou aviso |
| RNF-08 | Nenhum dado pessoal guardado (LGPD) |
| RNF-09 | Nenhuma entrada derruba o bot |
| RNF-10 | Treino reproduzível (semente fixa) |
| RNF-11 | Checagens novas entram sem retreinar |
| RNF-12 | Bot no ar na apresentação + vídeo de plano B |
