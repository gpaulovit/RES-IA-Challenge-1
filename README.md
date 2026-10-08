# RES-IA-Challenge-1

Bot no Telegram para quem recebeu uma mensagem ou link sobre as eleições de 2026 e quer saber,
antes de repassar, se aquilo já foi desmentido. O bot nunca dá veredito próprio de "verdade" ou
"mentira". O desenho completo está em [Requisitos](docs/requisitos.md).

📄 Página do projeto: [gpaulovit.github.io/RES-IA-Challenge-1](https://gpaulovit.github.io/RES-IA-Challenge-1/)

## Por onde começar: `experiments/`

A pasta [experiments/](experiments/) é a entrada principal. Os notebooks são numerados na ordem
em que devem ser lidos e guardam código e resultado lado a lado, para auditar célula a célula:

| Notebook | O que responde |
| --- | --- |
| `00_load_corpus.ipynb` | Carga do corpus de checagens (formato e colunas) |
| `01_embeddings.ipynb` | Embeddings das duas versões dos dados |
| `02_clusters.ipynb` | Agrupamento das alegações |
| `03_recurrence.ipynb` | Taxa de reciclagem: alegações falsas voltam a circular depois de checadas? |
| `04_reciclagem_entre_ciclos.ipynb` | Reciclagem de alegações entre ciclos eleitorais |
| `05_avaliacao.ipynb` | Conjunto de teste de reescrita e normalização da consulta |
| `06_modelos.ipynb` | Comparação de modelos de embeddings (Recall@k e MRR) |

Os módulos `.py` da pasta guardam a lógica que os notebooks importam; o
[README de experiments](experiments/README.md) descreve cada um. O registro dos gates está em
[historico-gates.md](experiments/historico-gates.md).

```sh
python3 -m venv .venv
.venv/bin/pip install -r experiments/requirements.txt
.venv/bin/dvc pull                     # dados de experiments/data
cd experiments && ../.venv/bin/jupyter lab
```

## Código do bot: `src/`

[src/checagens/](src/checagens/) guarda as regras que o bot aplica:

- `mensagens.py`: formatação, robustez e transparência das respostas.
- `registros.py`: registro anônimo de consultas e votos (LGPD).

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q        # testes do bot e das regras do gate
make latency               # tempo de resposta nas 30 mensagens de teste (RNF-01)
```

## Estrutura

- [experiments/](experiments/): notebooks, módulos e resultados dos modelos.
- [src/checagens/](src/checagens/): regras de mensagens e registros do bot.
- [tests/](tests/): verificações automáticas (rodam no CI).
- [scripts/](scripts/): medição de latência.
- [data/](data/): mensagens de teste e benchmark.
- [docs/](docs/): documentação publicada via GitHub Pages (docsify).
- [openspec/](openspec/): propostas e specs geridas pelo [OpenSpec](https://openspec.dev).

O protótipo de busca das semanas 1 a 3 (API, embeddings e retrieval em `src/`) foi retirado; ele
continua no histórico do git (tag `legado-busca` e commits da `main`) e nos guias semanais em
[docs/](docs/).
