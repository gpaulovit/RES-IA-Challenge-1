# Semana 3 — Produto & Decisão: Validação dos Cenários de Aceitação e Benchmark

Este documento registra a avaliação empírica do mecanismo de busca semântica e recuperação $k$-NN desenvolvido na Semana 3 pela frente de Engenharia, executado contra o conjunto de testes de benchmark (`data/testes_benchmark.json`) e mapeado conforme as Histórias de Usuário (**US-03 a US-06**).

---

## 1. Escopo e Objetivos da Avaliação

O objetivo principal desta etapa de Produto é validar se o buscador atende aos critérios de aceitação estipulados para a recuperação de checagens históricas, medindo:

1. **Taxa de Falsos Positivos (US-05, US-06):** Capacidade de filtrar notícias reais da imprensa sem atribuir correspondência com boatos do acervo.
2. **Resiliência a Ruído e Variações Adversariais (US-03, US-04):** Capacidade de associar reescritas com gírias de WhatsApp, erros ortográficos e apelidos à alegação original catalogada.
3. **Mapeamento de Lacunas Técnicas:** Identificação de falhas conhecidas dos modelos de embeddings (ex: inversão de negação e polaridade).

---

## 2. Estrutura da Bancada de Benchmark (`data/testes_benchmark.json`)

A suíte de testes de validação é composta por **62 casos de teste executáveis**, divididos estrategicamente em duas frentes:

| Categoria do Teste | Quantidade | Objetivo de Produto | Resultado Esperado |
| :--- | :---: | :--- | :--- |
| **Grupo de Controle (Notícias Reais)** | 32 | Testar falsos positivos contra matérias legítimas da imprensa (G1, UOL, CNN, Folha). | `sem_match` (Similaridade $< 0.60$) |
| **Variações Adversariais e Reciclagem** | 30 | Testar reescritas informais de boatos históricos e variação com nomes/gírias. | `match_confirmado` (Similaridade $\ge 0.60$) |

---

## 3. Análise dos Resultados de Validação

### A. Grupo de Controle e Mitigação de Falsos Positivos
* **Resultado:** Todas as consultas do grupo de controle obtiveram pontuação de similaridade abaixo do limiar de corte ($< 0.60$), sendo corretamente classificadas como `sem_match` ou `inédito`.
* **Impacto:** A taxa de falso positivo permaneceu dentro da meta estipulada ($FPR \le 5\%$), prevenindo que o sistema endosse notícias verdadeiras como se fossem desinformação.

### B. Resiliência Semântica a Variações Informais
* **Resultado:** Consultas com substituição de termos formais por gírias e apelidos políticos mantiveram o resgate da checagem original na primeira posição ($k=1$).
* **Impacto:** Confirma a superioridade da busca vetorial sobre a busca por palavras-chave (lexical) para o canal de mensagens instantâneas.

### C. Mapeamento de Gap Técnico: Inversão de Negação
* **Diagnóstico:** Identificou-se que modelos de embeddings puros mantêm alta similaridade vetorial mesmo quando a consulta inverte a polaridade da afirmação (ex: *"Lula fez X"* versus *"Lula NÃO fez X"*).
* **Direcionamento para a Semana 4:** Necessidade de implementar uma camada complementar de pós-processamento, re-ranking ou filtro lexical específico para checagem de negações antes da exibição final ao usuário.

---

## 4. Matriz de Rastreadilidade de Requisitos

| História de Usuário | Requisito Relacionado | Status na Semana 3 | Observação / Próximo Passo |
| :--- | :--- | :---: | :--- |
| **US-03** | **RF-01, RF-02** | 🟢 Aprovado | Busca $k$-NN em memória atinge latência $< 2$s. |
| **US-04** | **RF-04** | 🟢 Aprovado | Reciclagem histórica identificada via vetor. |
| **US-05** | **RF-03** | 🟡 Gap Mapeado | Requer filtro complementar de negação. |
| **US-06** | **RF-05, RF-06** | 🟢 Aprovado | Exibição de evidências e grupo de controle sem falso positivo. |

---

## Conclusão e Próximos Passos

A validação de Produto confirma que a infraestrutura de retrieval k-NN desenvolvida na Semana 3 atende aos requisitos fundamentais do MVP. Com a aprovação dos cenários de aceitação e a documentação do gap de polaridade, a **Issue #15** é encerrada e a frentes de desenvolvimento ficam liberadas para os refinamentos da próxima semana.