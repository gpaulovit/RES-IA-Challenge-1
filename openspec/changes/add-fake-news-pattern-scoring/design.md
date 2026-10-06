## Context

Ver `proposal.md` (Why). Estado atual que restringe a abordagem:

- **Evidência herdada** da change `add-recycled-claim-semantic-retrieval` (seções "Gate Result" e
  "Gate complementar: resultado" do design dela): a alegação específica raramente volta, a
  narrativa volta com frequência. A releitura por narrativa foi exploratória; aqui ela vira
  hipótese pré-registrada.
- **Dados disponíveis, por ano e classe** (contagens de 2026-10-06, lidas do zip do FactChecks.br
  v0.1 e de `experiments/data/com_texto_limpo.csv`):

| Fonte | Falsas | Verdadeiras | Anos com as duas classes |
|---|---|---|---|
| FactPolCheckBr (2022) | 1.815 | 9 | nenhum |
| Central de Fatos (2013–2021) | 10.286 | 141 | nenhum com volume útil |
| Fake.br | 3.600 | 3.600 | 2016 (1.586 / 80), 2017 (1.608 / 1.635), 2018 (169 / 772) |
| FakeRecogna | 5.822 | 5.951 | 2020 (2.519 / 3.980), 2021 (1.275 / 1.740) |
| Controles g1 (`data/testes_benchmark.json`) | 0 | 32 | 2022 |

- **Não existem notícias verdadeiras de 2022 em volume.** O período do bot (eleição de 2022) só
  pode ser medido do lado das falsas, mais os 32 controles do g1.
- **Vazamento de rótulo nos textos:** as falsas do FakeRecogna começam com "É #FAKE" (945) e "É
  falso" (130); as do Boatos.org têm "#boato" e "Boato –". A categoria `entretenimento` do
  FakeRecogna é 100% falsa. Sem limpeza, o modelo aprende o carimbo da agência, não a narrativa.
- **Gênero textual:** FactPolCheckBr e Central de Fatos são títulos de checagem; Fake.br são
  matérias completas; FakeRecogna mistura título e texto.

## Goals / Non-Goals

**Goals:**
- Testar se o padrão narrativo aprendido em um período separa falsas de verdadeiras em um período
  posterior, com critério escrito antes de rodar.
- Isolar o efeito do tempo do efeito de fonte e de gênero textual.
- Ter um score calibrado e explicável, ou um NO-GO registrado.

**Non-Goals:**
- Escolher o modelo final de produção nesta change: o gate decide se há produto; a escolha fina
  vem depois.
- Dizer a verdade de uma notícia, verificar fatos ou substituir agências.
- Medir efeito no comportamento de quem compartilha.

## Decisions

### 1. Unidade de análise: título ou 1ª linha, limpos

Todas as fontes entram como **título ou 1ª linha**, passando por `experiments/limpeza.py`
(`limpar_titulo` e `eh_multi_alegacao`), com dois acréscimos: remover os carimbos de agência
("É #FAKE", "Boato –", "#boato", nomes de agência no início) e descartar textos que fiquem vazios.
**Por quê:** é o formato do que chega no WhatsApp e o único comum a todas as fontes; a limpeza é a
defesa principal contra vazamento de rótulo. **Alternativa descartada:** usar o texto completo,
porque só Fake.br e FakeRecogna o têm e ele carrega o estilo do veículo.

### 2. Recorte temático: política

Treino e teste usam só o recorte político: categoria `política` no FakeRecogna e em Fake.br, e as
fontes de checagem política. **Por quê:** fora de política o rótulo se confunde com o tema
(entretenimento = 100% falso no FakeRecogna). **Custo:** reduz o volume, sobretudo de verdadeiras.

### 3. Desenho do gate: dois holdouts temporais

| Teste | Treino | Avaliação | O que isola |
|---|---|---|---|
| **A (decide)** | FakeRecogna política 2020 | FakeRecogna política 2021 | só o tempo: mesma fonte, mesmo gênero |
| **B (decide)** | Fake.br 2016–2018 + Central de Fatos ≤ 2018 | FakeRecogna política 2020–2021 + Central de Fatos 2020–2021 | tempo e fonte juntos: o caso mais duro |
| C (descritivo) | o melhor modelo de A/B, com todo o histórico ≤ 2021 | FactPolCheckBr 2022 (falsas) e 32 controles do g1 (verdadeiras) | o período do bot; n pequeno de verdadeiras |

2019 fica de fora do treino em B (quase sem verdadeiras) e serve de intervalo entre treino e teste.
**Por quê dois testes:** só A pode passar porque a fonte é a mesma; só B pode falhar porque a fonte
muda. Os dois juntos dizem se o padrão é de narrativa ou de veículo.

### 4. Critério pré-registrado do gate

Limites definidos pela frente de Modelos em 2026-10-06, **antes** de qualquer avaliação nos
períodos de teste; vale o commit deste arquivo como prova de ordem. Todas as métricas são medidas no
**período de avaliação** de cada teste (Decisão 3), nunca no conjunto onde a calibração é ajustada.

| Critério | GO | Inconclusivo | NO-GO |
|---|---|---|---|
| AUC-ROC no teste A (mesma fonte, ano seguinte) | ≥ 0,85 | 0,75 a < 0,85 | < 0,75 |
| AUC-ROC no teste B (outra fonte, anos depois) | ≥ 0,80 | 0,75 a < 0,80 | < 0,75 |
| ECE (10 faixas) | ≤ 0,05 | > 0,05 a ≤ 0,10 | > 0,10 |
| Brier skill score (ganho sobre prever a proporção de falsas) | > 0 | — | ≤ 0 |
| Ganho de AUC sobre a linha de base léxica (TF-IDF + regressão logística) | ≥ +0,05 | +0,02 a < +0,05 | < +0,02 |
| Atalho: AUC do modelo principal − AUC do modelo que só vê fonte e ano | ≥ +0,10 | +0,05 a < +0,10 | < +0,05 |
| Gíria e apelido: variação da probabilidade entre original e reescrita (falsas e verdadeiras) | média ≤ 0,10 **e** ≤ 5% dos pares com variação > 0,25 | média ≤ 0,15 **e** ≤ 10% dos pares com variação > 0,25 (sem ser GO) | média > 0,15 **ou** > 10% dos pares com variação > 0,25 |

**Agregação:** GO só se todos os critérios forem GO, em A e em B. Qualquer NO-GO → NO-GO.
O resto → inconclusivo, inclusive o caso "A passa e B não" (o padrão existe dentro da fonte, mas não
se transfere). Inconclusivo e NO-GO são registrados e rediscutidos antes da Seção 5 de `tasks.md`.

**Por que esses números:**

- **AUC por teste temporal:** A mede o tempo isolado e B mede tempo e fonte juntos; um limite por
  teste evita que um bom resultado em A esconda a falha de transferência em B. AUC abaixo de 0,75 é
  separação fraca demais para um score exposto ao público.
- **ECE e Brier skill score:** o produto mostra uma probabilidade; ela precisa significar o que
  diz para que as faixas não gerem falso alarme com alta confiança. O Brier entra como skill score
  (e não como valor absoluto) porque, com classes equilibradas, até um modelo perfeitamente
  calibrado com AUC 0,85 tem Brier ≈ 0,16 (simulação binormal, 2026-10-06); um limite absoluto de
  0,10 exigiria AUC ≈ 0,94 e contradiria os limites de AUC.
- **Linha de base léxica:** embeddings só se justificam se superarem um método léxico barato.
- **Atalho:** as verdadeiras e as falsas vêm de veículos diferentes até dentro do teste A
  (FakeRecogna: verdadeiras de UOL, Globo e gov.br; falsas de agências de checagem). Se fonte e ano
  sozinhos chegam perto do modelo, o que ele aprendeu é o veículo, não a narrativa.
- **Gíria e apelido:** o que circula em redes raramente segue a norma culta; a forma não pode
  decidir mais do que o conteúdo. No gate, a medida é a **variação da probabilidade** entre a
  notícia e a reescrita (|p_original − p_reescrita|), e não a mudança de faixa: o gate testa o
  modelo, e as faixas do produto só são definidas depois dele (Decisão 6). A média sozinha
  esconderia casos extremos, por isso há também um teto para a fração de pares com variação
  acima de 0,25. Os pares incluem reescritas de notícias verdadeiras, para medir também se a gíria
  **cria** falso alarme. A estabilidade de **faixa** (≥ 92% dos pares, as tolerâncias de 8% e 15%
  da proposta original) vira teste de produto, depois que as faixas existirem (Decisão 6).

**Teste C** é só descritivo: % das falsas de 2022 em cada faixa e quantos dos 32 controles do g1
caem em "compatível com narrativas falsas".

**Revisão (2026-10-06, antes de qualquer avaliação):** a primeira versão destes limites, colada
pela frente de Modelos, usava fatias por tema (política/geral × saúde/redes sociais), Recall@5,
Brier ≤ 0,10 medido no conjunto de validação e ganho de "+15%" sobre TF-IDF. Foi adaptada: as
fatias passaram aos testes temporais A e B (a hipótese é temporal e a base é só política), o
Recall@5 virou ganho de AUC e estabilidade de faixa (o produto devolve probabilidade, não lista),
o Brier virou skill score medido no período de avaliação, o ganho foi fixado em pontos de AUC e o
controle de atalho por fonte e ano, que tinha saído, voltou. Os limites de AUC (0,85 / 0,80 / 0,75),
de ECE (0,05 / 0,10) e as tolerâncias de 8% e 15% são os da proposta original. Na mesma data, ainda
antes de qualquer avaliação, o critério de gíria do gate passou de estabilidade de faixa para
variação da probabilidade (limites 0,10 / 0,15 / 0,25 / 5% / 10%, sugeridos na revisão e aceitos
pela frente de Modelos), e a estabilidade de faixa (≥ 92%) foi movida para depois da definição das
faixas (Decisão 6).

### 5. Modelos: linhas de base antes de qualquer coisa maior

1. Regressão logística sobre embeddings de frase (os candidatos e revisões do notebook
   `experiments/06_modelos.ipynb`).
2. Score por vizinhos: média ponderada dos rótulos dos k itens rotulados mais próximos. É também a
   fonte da explicação (Decisão 7).
3. Controle de atalho: modelo só com fonte e ano (ver critério).
4. Linha de base léxica: TF-IDF + regressão logística, com a mesma separação temporal. É a régua do
   critério "ganho de AUC" (Decisão 4).

Fine-tuning só se nenhuma linha de base passar no gate e houver indício de que falta capacidade,
não dados. **Por quê:** com milhares de exemplos e um risco alto de atalho, um modelo simples e
inspecionável mostra mais cedo se o sinal existe.

### 6. Calibração e faixas

Calibração por regressão isotônica ou Platt em um conjunto de validação separado, dentro do período
de treino. As faixas da spec (compatível / incerto / pouco compatível / fora dos padrões) usam
limites tirados das estimativas calibradas, não das probabilidades brutas. "Fora dos padrões" usa a
similaridade máxima com os itens de treino, com limite tirado dos controles do g1 e de itens fora
de política.

Depois de definidas as faixas, o teste de produto de robustez é a **estabilidade de faixa**: ≥ 92%
dos pares original × reescrita (falsas e verdadeiras, sem negação) mantêm a faixa; abaixo de 85%,
as faixas ou o modelo voltam para revisão antes do uso público. É a "tolerated rate" da spec.

### 7. Explicação por vizinhos

A resposta mostra os itens rotulados mais próximos (fonte, data e rótulo publicado pela agência),
reaproveitando a busca k-NN exata da change anterior (`src/checagens/retrieval.py`). A busca deixa
de ser o produto e passa a ser a explicação do score.

### 8. Robustez

O conjunto `experiments/results/teste_reescrita.csv` (534 consultas) é reaproveitado como teste de
estabilidade da faixa, **sem** a categoria `negacao`, que vai para um relatório à parte. Como ele só
tem boatos, é complementado por reescritas (apelido, gíria, erro de digitação) de notícias
**verdadeiras** do período de avaliação, geradas com `experiments/reescrita.py`, para medir também
se a gíria cria falso alarme. No gate, mede-se a variação da probabilidade (Decisão 4); depois das
faixas, a estabilidade de faixa (Decisão 6).

### 9. Normalização de rótulos

Mapeamento curado (como na change anterior), agora cobrindo também `is_fake` de Fake.br e
FakeRecogna e os vereditos de Central de Fatos. Itens sem mapeamento ficam fora, contados num
relatório de cobertura.

### 10. Canal: bot do Telegram

O produto chega ao usuário por um bot do Telegram criado pelo @BotFather (`/newbot` devolve o token
que autoriza o bot na Bot API). O bot recebe o texto, chama a API de score (tarefa 8.1) e responde
com a faixa, as narrativas próximas com link para cada checagem e o aviso de limitação. Ele não tem
lógica de decisão própria. Mensagens sem texto (foto, áudio, figurinha) recebem uma orientação para
enviar o texto. Na demonstração, o bot recebe mensagens por *long polling* (`getUpdates`), que não
exige servidor público; um *webhook* com HTTPS fica para quando houver servidor.
**Por quê:** criar um bot pelo @BotFather não exige aprovação nem conta empresarial, e a Bot API é
gratuita. **Alternativa descartada:** a API oficial do WhatsApp, que exige conta Business e
aprovação da Meta, burocracia incompatível com o prazo do projeto.
**Custo:** o boato circula no WhatsApp, então o usuário precisa copiar o texto de um aplicativo para
o outro (ver Riscos).

## Risks / Trade-offs

- **[Atalho por fonte ou época]** O modelo pode separar "veículo de checagem" de "veículo de
  notícia" em vez de narrativa falsa de verdadeira. → Limpeza de carimbos, recorte político,
  teste B com troca de fonte e o modelo-controle só com fonte e ano.
- **[Gênero textual]** Títulos de checagem são escritos como desmentido ("X não disse Y"), notícias
  verdadeiras como manchete. → Usar a forma do boato quando o título for desmentido
  (`experiments/reescrita.py`, `tirar_negacao`) e medir o efeito; registrar como limitação.
- **[Sem verdadeiras de 2022]** O período do bot não pode ser avaliado por inteiro. → Teste C
  descritivo; coletar verdadeiras de 2022 fica como tarefa recomendada antes do deploy.
- **[Dano por falso alarme]** Dizer "compatível com narrativas falsas" sobre uma notícia verdadeira
  prejudica o usuário e a fonte. → Faixa "incerto" larga, calibração medida, linguagem que nunca
  afirma veredito (spec) e explicação sempre visível.
- **[Viés político]** Se uma figura pública concentra boatos no treino, notícias verdadeiras sobre
  ela podem receber score alto. → Relatório de score por entidade mencionada nos controles.
- **[Canal diferente de onde o boato circula]** O público-alvo recebe boatos no WhatsApp e precisa
  copiar o texto para o Telegram, o que reduz o uso. → Registrar como limitação do MVP; integração
  com o WhatsApp fica para depois.
- **[Token do bot exposto]** Quem tem o token controla o bot. → Token fora do repositório (variável
  de ambiente ou segredo) e troca pelo @BotFather se vazar.
- **[Dados do usuário no Telegram]** O bot recebe o identificador de quem escreve. → Não persistir
  identificador de usuário nem de chat; registrar só metadados.
- **[Licenças]** Fake.br, FakeRecogna e Central de Fatos têm origem própria; o HF declara MIT para
  o pacote. → Conferir antes do deploy; FactPolCheckBr segue não comercial.
- **[Um anotador por rodada]** Os pares de narrativa herdados não têm medida de concordância. →
  Não decidem nada aqui; servem só como motivação.

## Migration Plan

Não há sistema em produção. A change anterior fica como histórico; o protótipo em `src/checagens/`
troca o contrato `POST /buscar` por um endpoint de score depois do gate (tarefa da Seção 8 de
`tasks.md`).

## Open Questions

- Vale coletar um conjunto pequeno de manchetes verdadeiras de 2022 para o teste C? Decisão de
  custo, que não muda o desenho do gate.
