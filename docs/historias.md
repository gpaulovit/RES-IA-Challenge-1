# Histórias de usuário

O [protótipo de Engenharia](funcionalidades.md) demonstra a integração com dados
fictícios. Seus testes não concluem as histórias nem os alvos do produto real abaixo.

Cada história segue o padrão **quero** / **para que**: alguém quer fazer X, para conseguir Y.

No SDD deste projeto, “usuário” da história é quem **usa o software**. Isso não é a mesma coisa que o público que **sofre o problema** (por exemplo, pessoas 40+ que recebem e encaminham boato no WhatsApp). Quem cai no boato é o beneficiário; quem cola o texto e lê o resultado é o usuário. Os dois só coincidem se essa pessoa decidir conferir.

Nesta fase, as duas primeiras histórias são da equipe de pesquisa. As demais são de quem consulta o sistema — checador(a) agora; no futuro, a pessoa que decidiu conferir o recado.

Os critérios de aceitação são requisitos não funcionais: uma **métrica** com alvo numérico e uma **entrega** (relatório, conjunto de teste ou comportamento mensurável). Uma **classificação auxiliar** complementa a métrica para não virar um número cego.

Alvos numéricos desta página são **provisórios da fase de concepção**. Podem ser recalibrados no conjunto de teste, mas a história só fecha com número publicado — não com impressão.

## Classificações auxiliares

| Classificação | Faixas |
|---|---|
| Decisão do gate | `go` / `no-go` |
| Adequação de cobertura | `suficiente` / `limitada` / `insuficiente` (por tema, tempo e agência) |
| Tipo de reescrita | `original` / `paráfrase` / `gíria ou apelido` / `erro proposital` / `inversão de negação` / `reincidência temporal` |
| Faixa de confiança | `confirmado` / `provável` / `sem match` / `inédito` |
| Cobertura da alegação | `catalogada` / `não verificada` / `mista` |
| Acordo entre agências | `convergente` / `divergente` / `única fonte` |
| Veredito normalizado | `falsa` / `enganosa` / `verdadeira` / `inconclusiva` / `sem mapeamento` |
| Completude da evidência | `completa` / `parcial` / `ausente` |

`k = 5` é o tamanho padrão do top-k. `Recall@5` = fração dos casos de teste em que a checagem correta aparece entre os 5 primeiros.

---

## Pesquisa — sem isso, o resto não justifica o sistema

### US-01 — O boato volta de verdade?

Como pesquisador(a), **quero** medir se alegações semanticamente equivalentes reaparecem em períodos diferentes no FactPolCheckBr, **para que** só montemos o buscador se a reciclagem for um fenômeno mensurável.

**Critério de aceitação**

| | |
|---|---|
| Métrica | Taxa de recorrência temporal `R` = % de alegações com pelo menos um vizinho semântico (mesmo cluster) a ≥ 180 dias de distância |
| Alvo | `R ≥ 10%` **e** pelo menos 3 clusters com ocorrências em ≥ 2 períodos → classificação `go`; abaixo disso → `no-go` |
| Entrega | Relatório de gate com `R`, número/tamanho dos clusters e decisão `go` / `no-go` escrita **antes** de qualquer indexação de retrieval |
| Classificação auxiliar | Decisão do gate (`go` / `no-go`) |

### US-02 — A base é boa o bastante?

Como pesquisador(a), **quero** classificar a cobertura do corpus por tema, tempo e agência, **para que** não tratemos buraco nos dados como se fosse reciclagem.

**Critério de aceitação**

| | |
|---|---|
| Métrica | Completude de registro + amplitude: (a) % de registros com texto, veredito, data e agência; (b) anos distintos cobertos; (c) agências com ≥ 1 registro |
| Alvo | (a) ≥ 95% dos ~1.882 registros completos; (b) ≥ 2 anos distintos; (c) as 10 agências listadas ou lacuna nomeada. Cobertura geral `suficiente` só se as três dimensões forem `suficiente` ou `limitada` — nunca se alguma for `insuficiente` sem plano de suplemento |
| Entrega | Relatório de cobertura com classificação por dimensão (tema, tempo, agência), publicado junto com o gate |
| Classificação auxiliar | Adequação de cobertura (`suficiente` / `limitada` / `insuficiente`) |

---

## O buscador funcionando

### US-03 — Achei um texto parecido com um boato velho

Como quem consulta o sistema, **quero** colar uma alegação reescrita (gíria, apelido, erro de digitação ou inversão) e receber a checagem catalogada equivalente, **para que** não precise da palavra exata para achar o que já foi verificado.

**Critério de aceitação**

| | |
|---|---|
| Métrica | `Recall@5` no conjunto de teste rotulado, global e por tipo de reescrita |
| Alvo | `Recall@5 ≥ 70%` no total; nenhuma classe de reescrita com `Recall@5 < 50%`; queda frente a consultas `original` ≤ 15 pontos percentuais |
| Entrega | Conjunto de teste com as 5 classes de reescrita (além de `original`) e tabela de `Recall@5` por classe, **antes** de uso público |
| Classificação auxiliar | Tipo de reescrita |

### US-04 — Isso já foi desmentido há anos

Como quem consulta o sistema, **quero** que um boato antigo reaparecendo com nova roupagem seja reconhecido como o mesmo caso, **para que** eu não trate reincidência histórica como alegação inédita.

**Critério de aceitação**

| | |
|---|---|
| Métrica | `Recall@5` só nos pares cuja data da checagem original e da consulta distam ≥ 180 dias |
| Alvo | `Recall@5 ≥ 60%` nesses pares; 0% desses casos classificados como `inédito` quando o original está no top-5 |
| Entrega | Subconjunto de teste de reincidência temporal e tabela de `Recall@5` (depende de US-01 = `go`) |
| Classificação auxiliar | Tipo de reescrita = `reincidência temporal` |

### US-05 — Isso é inédito

Como quem consulta o sistema, **quero** um “não achei” confiável quando nada no corpus corresponde, **para que** o sistema não invente uma checagem que não existe.

**Critério de aceitação**

| | |
|---|---|
| Métrica | Taxa de falso-positivo em `confirmado` (`FPR_confirmado`) em alegações legítimas fora do corpus |
| Alvo | `FPR_confirmado ≤ 5%`; ≥ 90% dessas consultas caem em `sem match` ou `inédito` |
| Entrega | Conjunto de alegações fora da base + matriz de classificação nas 4 faixas de confiança |
| Classificação auxiliar | Faixa de confiança |

### US-06 — Me mostra o porquê

Como quem consulta o sistema, **quero** ver o top-5 com o texto-fonte comparado em cada candidato, **para que** eu decida — e não o modelo sozinho.

**Critério de aceitação**

| | |
|---|---|
| Métrica | Completude da evidência: % de candidatos do top-5 que trazem texto da alegação de origem + veredito + agência |
| Alvo | 100% dos candidatos com evidência `completa`; 0% `ausente` |
| Entrega | Checagem automática no conjunto de teste: cada resultado top-5 passa na lista de campos obrigatórios |
| Classificação auxiliar | Completude da evidência (`completa` / `parcial` / `ausente`) |

---

## O sistema não mentir nem simplificar demais

### US-07 — Diga o quanto você tem certeza

Como quem consulta o sistema, **quero** receber uma faixa de confiança em vez de sim/não, **para que** match duvidoso vá a revisão humana e o sistema não fale com certeza demais.

**Critério de aceitação**

| | |
|---|---|
| Métrica | (a) cobertura das faixas; (b) vazamento da zona cinzenta para `confirmado` |
| Alvo | 100% dos resultados em exatamente uma faixa; 0% dos scores entre os limiares de `confirmado` e `sem match` classificados como `confirmado`; precisão de `confirmado` ≥ 90% no conjunto de teste |
| Entrega | Limiares publicados + matriz de classificação real vs. faixa atribuída |
| Classificação auxiliar | Faixa de confiança |

### US-08 — Não “lave” a parte nova

Como quem consulta o sistema, **quero** que um match só cubra o trecho já catalogado, **para que** uma afirmação nova colada num boato velho não pareça verificada.

**Critério de aceitação**

| | |
|---|---|
| Métrica | Taxa de endosso indevido: % de casos mistos em que o veredito catalogado é aplicado à parte nova |
| Alvo | 0% de endosso indevido; 100% dos casos mistos com a parte extra marcada `não verificada` |
| Entrega | Conjunto de teste de alegações `mistas` e verificação caso a caso da marcação de cobertura |
| Classificação auxiliar | Cobertura da alegação (`catalogada` / `não verificada` / `mista`) |

### US-09 — As agências discordam

Como quem consulta o sistema, **quero** ver os dois vereditos quando agências discordam da mesma alegação, **para que** o sistema não escolha um lado em silêncio.

**Critério de aceitação**

| | |
|---|---|
| Métrica | Taxa de exposição de divergência: % dos pares conhecidos `divergente` em que as duas fontes e os dois vereditos normalizados aparecem |
| Alvo | 100% de exposição; 0% de resolução automática (mostrar só um veredito) |
| Entrega | Lista de pares divergentes de referência e verificação de que ambos os lados são exibidos |
| Classificação auxiliar | Acordo entre agências (`convergente` / `divergente` / `única fonte`) |

### US-10 — Falar a mesma língua

Como quem consulta o sistema, **quero** vereditos traduzidos para uma lista única, **para que** confiança e divergência não comparem rótulos que não são a mesma coisa.

**Critério de aceitação**

| | |
|---|---|
| Métrica | (a) cobertura do mapeamento; (b) acurácia amostral do mapeamento |
| Alvo | 100% dos rótulos de origem mapeados (nada usado em classificação como `sem mapeamento`); acurácia ≥ 95% numa amostra revisada de pelo menos 100 registros |
| Entrega | Tabela curada rótulo-de-origem → veredito normalizado + ata da amostragem, **antes** de alimentar US-07 e US-09 |
| Classificação auxiliar | Veredito normalizado |

---

## Em uma linha

| US | Quero | Para que | Métrica (alvo) |
|---|---|---|---|
| 01 | Medir se o boato reaparece no tempo | Só construir o buscador se isso for real | `R ≥ 10%` → `go` / `no-go` |
| 02 | Classificar a cobertura da base | Não confundir buraco com reciclagem | ≥ 95% registros completos; ≥ 2 anos; 10 agências ou lacuna nomeada |
| 03 | Achar a checagem mesmo com o texto mudado | Não depender da palavra exata | `Recall@5 ≥ 70%` (nenhuma classe < 50%) |
| 04 | Reconhecer boato antigo que voltou | Não tratar reincidência como novidade | `Recall@5 ≥ 60%` em pares ≥ 180 dias |
| 05 | Ouvir “não achei” quando não tem checagem | Não inventar veredito | `FPR_confirmado ≤ 5%` fora do corpus |
| 06 | Ver o texto-fonte de cada candidato | Eu decidir, não o modelo | 100% evidência `completa` no top-5 |
| 07 | Receber faixa de confiança | Dúvida ir a humano | 0% cinza → `confirmado`; precisão `confirmado` ≥ 90% |
| 08 | Cobrir só o trecho já checado | Não lavar a parte nova | 0% de endosso indevido em casos `mista` |
| 09 | Ver os dois lados da discórdia | O sistema não escolher sozinho | 100% dos pares `divergente` expostos |
| 10 | Unificar rótulos das agências | Comparar coisas iguais | 100% mapeados; ≥ 95% corretos na amostra |

---

## Contabilidade SMART

Cada história foi checada nos cinco critérios. Onde o “prazo” não é uma data de calendário, o limite é a **fase de entrega** (gate, conjunto de teste ou antes do uso público).

| US | Specific | Measurable | Achievable | Relevant | Time-bound | Resultado |
|---|---|---|---|---|---|---|
| 01 | Corpus FactPolCheckBr + recorrência ≥ 180 dias | `R` e decisão `go` / `no-go` | Calculável nos ~1.882 registros | Sem reciclagem, o challenge não se justifica | Relatório **antes** de indexar | Passa |
| 02 | Três dimensões: tema, tempo, agência | Completude %, anos, agências + faixa de adequação | Os campos já existem na fonte; lacuna vira rótulo, não chute | Cobertura fraca fabrica falso padrão | Junto com o gate | Passa |
| 03 | Consulta reescrita → checagem no top-5 | `Recall@5` global e por classe | Conjunto de teste derivado do próprio corpus | É o núcleo do retrieval | Tabela publicada **antes** de uso público | Passa |
| 04 | Par com gap ≥ 180 dias | `Recall@5` só nesse recorte | Só é executável se US-01 = `go` | Distingue paráfrase de hoje de reincidência | Depois do gate, no mesmo conjunto de teste | Passa, **dependente de US-01** |
| 05 | Alegações fora do corpus | `FPR_confirmado` e % em `sem match` / `inédito` | Dá para montar um conjunto negativo agora | Falso “confirmado” é o pior erro | Mesma leva de avaliação da US-03 | Passa |
| 06 | Campos obrigatórios por candidato | % `completa` = 100 | Checagem automática de campos | Sem evidência, a faixa de confiança vira selo opaco | Em todo resultado do conjunto de teste | Passa |
| 07 | Uma faixa por resultado; cinza ≠ confirmado | Cobertura 100%, vazamento 0%, precisão ≥ 90% | Limiares saem da distribuição do conjunto de teste | Evita veredito binário | Limiares publicados com a avaliação | Passa |
| 08 | Alegação `mista` | Taxa de endosso indevido = 0% | Exige conjunto misto rotulado (viável e pequeno) | Evita “lavar” afirmação nova | Antes de uso público | Passa |
| 09 | Pares `divergente` conhecidos | 100% de exposição | Conjunto de referência pequeno e enumerável | Discordância escondida é viés | Na mesma avaliação da política de decisão | Passa |
| 10 | 10 agências → taxonomia única | 100% mapeados; ≥ 95% na amostra ≥ 100 | Conjunto de rótulos é finito e curável à mão | Sem isso, US-07 e US-09 comparam rótulos diferentes | **Antes** de alimentar confiança e divergência | Passa |

Nenhuma história ficou só como desejo. US-04 é a única condicional: se o gate for `no-go`, ela não é entregue — o escopo volta a ser discutido, como já está no plano OpenSpec.
