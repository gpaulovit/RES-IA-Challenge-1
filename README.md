# RES-IA-Challenge-1

Estimar, a partir de boatos políticos já checados, a chance de uma notícia nova ser falsa,
apresentando o resultado em faixas e nunca como veredito.

📄 Página do projeto: [gpaulovit.github.io/RES-IA-Challenge-1](https://gpaulovit.github.io/RES-IA-Challenge-1/)

## Situação

Antes de construir o produto, um **gate** testa a hipótese com critérios escritos antes de rodar:
um modelo treinado com notícias de um período separa falsas de verdadeiras num período posterior?

A 1ª rodada (2026-10-06) deu **NO-GO**. Só a fonte e o ano já preveem o rótulo melhor que o modelo
de texto, e os embeddings não superam TF-IDF. Pela proposta, o escopo volta para discussão antes
de qualquer API. Números e leitura no
[design.md](openspec/changes/add-fake-news-pattern-scoring/design.md).

## Como executar

Pré-requisito: Python 3.11 ou superior (os resultados registrados usaram 3.14).

```sh
python3 -m venv .venv
.venv/bin/pip install -r experiments/requirements.txt
.venv/bin/dvc pull                     # dados de experiments/data (remote: ver experiments/README)
.venv/bin/python -m pytest -q          # testes da limpeza e das regras do gate
cd experiments && ../.venv/bin/python gate.py
```

## Estrutura

- [experiments/](experiments/): código, notebooks e resultados ([README](experiments/README.md)).
- [tests/](tests/): testes automáticos.
- [openspec/](openspec/): propostas, design, specs e tarefas ([OpenSpec](https://openspec.dev)).
- [docs/](docs/): página do projeto (docsify): requisitos, histórias, cronograma e engenharia.
- [data/testes_benchmark.json](data/testes_benchmark.json): 32 manchetes verdadeiras do g1 (controles do teste C).
- [refs/](refs/): material de referência.

O protótipo de busca das semanas 1–3 foi removido e está na tag git `legado-busca`.
