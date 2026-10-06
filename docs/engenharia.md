# Engenharia

Como as peças do projeto se conectam, onde cada coisa fica e como conferir uma entrega.
O que o produto deve fazer está em [Requisitos](requisitos.md); o porquê, em [Perguntas](perguntas.md).

## Situação (2026-10-06)

O gate de generalização temporal rodou pela primeira vez e deu **NO-GO**. Fonte e ano sozinhos
preveem se a notícia é falsa melhor que o modelo de texto (AUC 0,92 contra 0,83 no teste A). Os
números estão no
[design.md da change](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/openspec/changes/add-fake-news-pattern-scoring/design.md).
Pela tarefa 4.3, nada de calibração, faixas ou API é construído antes de o grupo rediscutir o
escopo.

O protótipo de busca das semanas 1–3 (API com exemplos fictícios, pipeline de embeddings e
retrieval) foi removido do repositório e pode ser recuperado pela tag git `legado-busca`.

## Fluxo

```text
Fontes (FactPolCheckBr, Central de Fatos, Fake.br, FakeRecogna)
  → limpeza (carimbos de agência, multi-alegação)
  → conjuntos A e B (treino num período, avaliação no seguinte)
  → embeddings (MiniLM) e linhas de base (TF-IDF, controle fonte+ano)
  → gate (critérios pré-registrados) → GO / inconclusivo / NO-GO
  → [só depois de GO] calibração, faixas, API do score
```

Cada seta é um acordo entre frentes: Dados define as fontes e os rótulos; Modelos define os
modelos e os critérios; Produto define o que a resposta mostra; Engenharia e DevOps garantem
que tudo roda de novo com o mesmo resultado.

## Onde cada coisa fica

| Local | Responsabilidade |
| --- | --- |
| `experiments/` | Código, notebooks e resultados. Módulos descritos no [README de experiments](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/experiments/README.md). |
| `experiments/gate.py` | Gate temporal: monta os conjuntos, treina as linhas de base e aplica os critérios. |
| `experiments/results/` | Tabelas pequenas e rótulos manuais (no git, revisáveis linha a linha). |
| `experiments/data/` | Dados brutos e embeddings (DVC; `dvc pull`). |
| `tests/` | Testes automáticos da limpeza e das regras do gate. |
| `openspec/changes/` | Proposta, design (com critérios pré-registrados), spec e tarefas de cada mudança. |
| `docs/` | Esta documentação (GitHub Pages). |

## Como executar e conferir

```sh
python3 -m venv .venv
.venv/bin/pip install -r experiments/requirements.txt
.venv/bin/dvc pull
.venv/bin/python -m pytest -q
cd experiments && ../.venv/bin/python gate.py
```

`passed` no pytest indica que a limpeza e as regras do gate se comportam como o design.md
descreve. O `gate.py` imprime as contagens de cada conjunto, as métricas de cada modelo e o
veredito, e grava os três CSVs `results/gate_*.csv`.

**Regra de ordem:** um critério de avaliação só vale se o commit que o define for anterior ao
commit dos resultados. Confira com `git log --format='%h %ci %s' -- <arquivos>`.

## Dependências entre frentes

| Frente | O que Engenharia precisa receber | O que Engenharia devolve |
| --- | --- | --- |
| Domínio de dados | Fontes, significado dos rótulos, recorte político | Leitores das fontes e contagens por ano e classe |
| Modelos de IA | Modelos candidatos e critérios do gate | Gate executável e resultados reproduzíveis |
| Produto e decisão | Cenários e o que a resposta deve mostrar | Fluxo demonstrável e limites conhecidos |
| DevOps e MLOps | Ambiente, remote do DVC, automação | Dependências fixadas e comandos de execução |

Um bloqueio deve dizer: **o que falta, quem resolve, qual entrega está parada e até quando.**

## Registro semanal (issue ou PR com `papel: engenharia`)

```text
Entrega da semana:
Issue:
Entradas recebidas (de quem):
Decisões tomadas e onde estão registradas:
Como executar e conferir:
Resultado:
Bloqueios, responsável e prazo:
Próximo passo:
```
