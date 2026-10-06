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

**1ª rodada do gate (2026-10-06, antes de qualquer avaliação).** Corte de esforço para o gate rodar
logo; **nenhum limite da Decisão 4 muda** e a regra de agregação é a mesma.

- **Roda agora:** testes A e B; modelo principal = regressão logística sobre embeddings do
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revisão
  `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` (o modelo dos gates anteriores); linha de base léxica
  (item 4); controle de atalho (item 3). Os sete critérios são medidos sobre esse modelo principal.
- **Adiado:** os demais modelos do notebook 06, o score por vizinhos (item 2) e o teste C. Um GO
  nesta rodada já basta para seguir à Seção 5; os adiados entram antes da escolha final do modelo.
- **Regras operacionais**, fixadas aqui porque o desenho não as definia:
  - *Ano:* primeiro `20[0-2]\d` encontrado no campo de data (as datas misturam vários formatos).
    Sem ano, o item sai. Com essa leitura, as contagens de Fake.br e FakeRecogna por ano diferem da
    tabela do Context (que perdeu as datas fora de `dd/mm/aaaa`); valem as impressas pelo
    `experiments/gate.py`, com o hash de cada conjunto.
  - *Unidade de texto (Decisão 1):* FakeRecogna e Central de Fatos, 1ª linha do texto; Fake.br não
    tem título separado, então vale o trecho antes da 1ª quebra de linha, tabulação ou `..` e,
    dentro dele, só a 1ª frase. Depois, `limpar_titulo()` e descarte de `eh_multi_alegacao()` e de
    textos vazios.
  - *Carimbos (Decisão 1):* além dos já previstos, a limpeza passa a tirar "É verdadeiro/a", "É
    falsa", "É enganosa", "É #FATO", e corrige o padrão que cortava "É verdade" no meio de "É
    verdadeiro" (deixava "iro que…").
  - *Recorte político (Decisão 2):* Fake.br `politica`; FakeRecogna `política`; Central de Fatos
    `política`, `eleições`, `eleições 2018`, `eleições 2020` e `políticas públicas` (as linhas sem
    categoria, todas do UOL, ficam fora).
  - *Rótulo (Decisão 9):* `is_fake` 1 → falsa, −1 → verdadeira; 0 (34 itens da Central de Fatos)
    fica fora e é contado.
  - *Fonte (controle de atalho):* domínio do veículo (`review_domain`; no Fake.br, o domínio de
    `claim_url`, sem subdomínio). O controle é uma regressão logística sobre fonte (one-hot,
    categoria nova → zeros) e ano.
  - *Probabilidades:* as do modelo, sem recalibração (a calibração é a Seção 5, depois do gate). O
    Brier skill score usa como referência a proporção de falsas do **período de treino**.
  - *Gíria e apelido:* pares gerados por `experiments/reescrita.py` (`trocar_apelido`, `internetes`,
    `erro_digitacao`; semente 50) sobre até 200 falsas e 200 verdadeiras do período de avaliação de
    cada teste, mais as categorias `apelido`, `girias`, `apelido+girias` e `digitacao` de
    `experiments/results/teste_reescrita.csv`.
  - *Separação temporal:* `assert` de que nenhum ano e nenhum texto (após limpeza, sem diferenciar
    caixa) do período de avaliação aparece no treino; textos repetidos entre os períodos saem da
    avaliação.
  - *Pontuação final:* o ponto final do texto é tirado em todas as fontes (só o Fake.br termina em
    ponto; seria pista de fonte).
  - *Hiperparâmetros:* nenhum ajuste. Regressão logística padrão do scikit-learn (`C = 1`); TF-IDF
    com `strip_accents="unicode"`, unigramas e bigramas, `min_df = 2`, `sublinear_tf`.
  - *Critério de gíria por classe:* média e fração > 0,25 são medidas separadamente em falsas e em
    verdadeiras, e vale a pior das duas (um falso alarme criado pela gíria e um boato escondido por
    ela pesam igual).
  - *Implementação:* `experiments/gate.py`; resultados em `experiments/results/gate_*.csv`.

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
com busca k-NN exata (`Q @ E.T` sobre embeddings normalizados, como em `experiments/avaliacao.py`;
o protótipo `src/checagens/retrieval.py` foi removido e está na tag `legado-busca`). A busca deixa
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
- **[Licenças]** Fake.br, FakeRecogna e Central de Fatos têm origem própria; o HF declara MIT para
  o pacote. → Conferir antes do deploy; FactPolCheckBr segue não comercial.
- **[Um anotador por rodada]** Os pares de narrativa herdados não têm medida de concordância. →
  Não decidem nada aqui; servem só como motivação.

## Migration Plan

Não há sistema em produção. A change anterior fica como histórico; o protótipo de busca
(`src/checagens/`) foi removido e está na tag `legado-busca`. A API do score é criada só depois do
GO (tarefa da Seção 8 de `tasks.md`).

## Open Questions

- Vale coletar um conjunto pequeno de manchetes verdadeiras de 2022 para o teste C? Decisão de
  custo, que não muda o desenho do gate.
