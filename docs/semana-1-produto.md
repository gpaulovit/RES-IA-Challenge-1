# Semana 1 — Produto e Decisão: Mitigação de Falsos Positivos e Diretrizes de MLOps

**Definição do conjunto de controle, regras de exibição neutra e enquadramento do produto com as boas práticas de MLOps.**

Issue: [#5 — Produto & Decisão: leitura de zonas cinzentas e síntese da semana](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/5)
Responsável: Ana Júlia Batista (`papel: produto-decisao`).

---

## 1. Contexto e Diagnóstico de Produto

A análise do corpus expandido — que engloba o *FactPolCheckBr* e repositórios complementares (*Fake.br-Corpus*, *FakeWhatsAppBR*, *FakeTweet.Br*, *FACTCK.BR*, *FactChecks.br*, *BRACIS2019* e *FakeNewsNet*) — revelou um cenário de **forte desbalanceamento**: as bases são compostas quase exclusivamente por alegações falsas e boatos desmentidos (com cerca de 97% de checagens com veredito `falso`).

Sem uma estratégia de produto clara, um modelo de busca semântica exposto a uma consulta do usuário sobre uma notícia real do dia a dia tenderia a **forçar uma correspondência inadequada** com um boato antigo, gerando falsos positivos graves.

---

## 2. Decisões Estratégicas de Produto

Para garantir a viabilidade técnica e a confiabilidade do produto, foram estabelecidas três diretrizes fundamentais:

### A. Criação do Conjunto de Controle de Falsos Positivos
* **Estratégia:** Foi construído um conjunto de notícias legítimas e recentes de veículos de imprensa (G1, UOL, CNN, Folha) para atuar como grupo de controle nos testes do modelo.
* **Regra de Negócio:** Notícias reais e verdadeiras devem obrigatoriamente retornar pontuação de similaridade semântica abaixo do limiar de corte ($< 60\%$), resultando na classificação de `sem_match` (notícia/alegação inédita).

### B. Exibição Neutra e Transparente no Bot
* **Estratégia:** Diante de divergências metodológicas entre agências e de checagens cujos títulos já contêm a própria correção ("É #FAKE que..."), o sistema não deve emitir um veredito automático sumário.
* **Regra de Negócio:** O bot conversacional atuará priorizando a **busca semântica e a exibição transparente do link e do desmentido oficial**, permitindo que o usuário consulte a checagem na fonte original.

### C. Alinhamento com a Arquitetura de MLOps (Kreuzberger et al., 2023)
Em conformidade com a literatura de MLOps:
* **Foco em Dados (*Data-Centric AI*):** A validação do produto passa pela qualidade da bancada de testes de benchmark (`data/testes_benchmark.json`), criada para testar a robustez do modelo frente a ruídos do mundo real (gírias, erros ortográficos, negações e variações temporais).
* **Rastreabilidade e Versioneamento (P4/C7):** Garantia de que a bancada de testes de benchmark permaneça versionada via Git no repositório, permitindo a reprodutibilidade dos experimentos de embeddings realizados pela equipe de IA.

---

## 3. Matriz de Decisões e Próximos Passos (Semana 2)

| Problema Identificado | Risco para o Produto | Decisão de Produto | Impacto na Engenharia / IA |
| --- | --- | --- | --- |
| Base composta 97% por boatos falsos | Alta taxa de falsos positivos para notícias reais | Criação de controle com 32 notícias reais | Modelo deve retornar `<60%` de similaridade (`sem_match`) |
| Inversão de negação ("Lula NÃO prometeu...") | Modelo dar match em frases com sentido oposto | Inclusão de testes de negação no benchmark | Avaliação da capacidade do modelo de distinguir polaridade |
| Linguagem informal (WhatsApp / Gírias) | Falha de recuperação para buscas do usuário real | Testes adversariais de gírias e erros de digitação | Avaliação do vetor de embedding em texto ruidoso |

---

## Resumo Final

**O produto foi estruturado para evitar a colisão entre notícias reais e boatos passados, definindo limiares rígidos de similaridade e entregando uma bancada de testes balanceada (`data/testes_benchmark.json`) para a avaliação objetiva dos modelos de IA na Semana 2.**