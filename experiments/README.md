# Experimentos

Protótipos da frente **Modelos de IA** para as duas camadas do bot (ver
[Requisitos](../docs/requisitos.md) e a change
[`add-bot-intelligence-layers`](../openspec/changes/add-bot-intelligence-layers/design.md)).
Cada camada nasce aqui e, depois de validada, sobe para `src/checagens/`.

- **Camada 1, busca de checagens** (RF-06, RN-05, RN-06): a construir em `camada1.py`.
- **Camada 2, classificador de sinais de alerta** (RF-08, RF-14): a construir em
  `classificador.py`.

Os produtos descartados (reciclagem de alegação e scoring de fake news) e o gate deles estão em
[`/archive`](../archive/README.md).

## Ambiente

Um ambiente só para o repositório inteiro:

```bash
python3 -m venv .venv
.venv/bin/pip install -r experiments/requirements.txt
.venv/bin/dvc pull                     # baixa experiments/data (ver "Dados (DVC)")
.venv/bin/python -m pytest -q
```

- Versões fixadas em [`requirements.txt`](requirements.txt).
- Notebooks e scripts rodam a partir de `experiments/` (caminhos `data/` e `results/`).
- A 1ª geração de embeddings baixa o modelo do Hugging Face; os vetores ficam em cache em
  `data/emb/`, pela revisão do modelo e pelo hash dos textos.

## Módulos

| Arquivo | Responsabilidade |
|---|---|
| `limpeza.py` | `limpar_titulo()` (prefixos de veredito e carimbos de agência) e `eh_multi_alegacao()` |
| `corpora.py` | Lê FactPolCheckBr e o zip do FactChecks.br (Fake.br, FakeRecogna, Central de Fatos) no esquema `claim, is_fake, ano, fonte, categoria, origem` |
| `modelos.py` | Modelos de embeddings candidatos (id, revisão fixada, prefixo) e `embeddings()` com cache |
| `reescrita.py` | Reescritas de apelido, gíria, erro de digitação e negação |
| `normalizacao.py` | Normalização da consulta (Enelvo + apelidos) |
| `avaliacao.py` | Recall@k e MRR de uma busca |

## Notebooks

| Notebook | O que responde |
|---|---|
| `00_load_corpus.ipynb` | Carga e limpeza do FactPolCheckBr |
| `01_embeddings.ipynb` | Embeddings das alegações |
| `02_clusters.ipynb` | Agrupamento das alegações |
| `05_avaliacao.ipynb` | Teste de reescrita (gíria, apelido, erro, negação) e normalização da consulta |
| `06_modelos.ipynb` | Comparação de modelos de embeddings (Recall@k e MRR), base da escolha do MiniLM |

## Dados (DVC)

`experiments/data/` é versionada com [DVC](https://dvc.org): o git guarda só o ponteiro
[`data.dvc`](data.dvc) (hash md5 da pasta), e os arquivos ficam no remote do DVC. Um
commit do git mais `dvc pull` reconstroem os dados exatos daquele commit:

```bash
git checkout <commit> && .venv/bin/dvc pull
```

- **Remote atual: local**, só na máquina do Paulo (`~/dvc-storage/res-ia-challenge-1`,
  configurado em `.dvc/config.local`, fora do git). **Até a migração, só essa máquina
  consegue reproduzir os experimentos**, e a pasta do remote deve estar no backup.
- **Migração prevista** (início do deploy do modelo): Google Drive ou storage em nuvem,
  combinado com DevOps/MLOps.

  ```bash
  pip install "dvc[gdrive]"
  dvc remote add -d gdrive gdrive://<ID_DA_PASTA>
  dvc remote modify --local gdrive gdrive_client_id '<CLIENT_ID>'        # nunca commitar
  dvc remote modify --local gdrive gdrive_client_secret '<CLIENT_SECRET>'
  dvc push -r gdrive
  ```

- **Hashes:** o DVC usa md5 (no `data.dvc`); a tabela abaixo usa SHA-256, que é o
  formato da Engenharia. Os dois valem.
- **Histórico:** os commits anteriores ao `ace022f` têm os CSVs dentro do próprio git;
  o histórico não foi reescrito, para os commits do gate continuarem reproduzíveis.
- **Fica no git, não no DVC:** `experiments/results/` (tabelas pequenas e os **rótulos
  manuais**, que precisam de revisão linha a linha pelo `git diff`).

## Procedência e integridade (SHA-256)

| Arquivo | SHA-256 |
|---|---|
| `data/com_texto.csv` (fonte `e4b4feafce9b83789a517f649abb39ad4645f1b3`) | `7f0c9443dcf2d7fb15ef3320eb1bfeb8b0d67f4689a13757b33809f200e84681` |
| `data/com_texto_limpo.csv` | `45b54bb32629b435e1af29fc23e83b98b9c7da758239964c2aee540e6196fbc0` |
| `data/emb_minilm.npy` (macOS) | `d3446245288ca5ef58e0d9dcb34b77ad67f761ee734700e73053325d369714bd` |
| `data/pares_temporais.csv` | `071cfa867d7bed7264c5d781121ee3d541b2a49b90461a56174b68a2fd760b54` |
| `results/validacao_pares.csv` | `b625b1d80af9ac76371b03481237d6a3b0883f4f40161f87fb57aef952d3786c` |
| `data/factchecksbr/FactChecksbr.zip` (release v0.1) | `035faf96dcb851e166c330af4636689669b5ff032c46bec109178669317c31b3` |
| `data/factchecksbr/central_de_fatos.tsv` (igual ao membro do zip; o código lê do zip) | `1b3c964b0f33b9b9845af4f11afd2ac4b623489535aa2e5cbf6cce324bad12c0` |

O `data/clusters.csv` não está na tabela: ele é regenerado pelo 02 sempre que as notas
de coerência mudam. A versão vale pelo `data.dvc` do commit.

O hash do `com_texto.csv` é o mesmo registrado pela Engenharia em
`docs/semana-1-engenharia.md` (removido; está na tag git `legado-busca`). Para conferir:
`shasum -a 256 experiments/data/*.csv experiments/data/*.npy experiments/results/validacao_pares.csv`.

**Histórico de hashes do `com_texto_limpo.csv`:**

- `9c78394c…`: 1ª execução, usada no Gate Result de 29/09.
- `45b54bb3…`: depois da limpeza compartilhada (01/10). A coluna `claim` é idêntica
  (diff de 0 linhas); só `multi_claim` mudou em 6 linhas (ver abaixo).

## Licença dos dados

- `data/com_texto.csv` e seus derivados vêm do
  [Dataset-FactPolCheckBr](https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr)
  (Interfaces – Núcleo de Estudos Sociopolíticos dos Algoritmos e da Inteligência
  Artificial, UFSCar), sob licença [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/):
  exige atribuição, proíbe uso comercial e obriga redistribuir sob a mesma licença.
- `data/factchecksbr/` vem do FactChecks.br (Gomes, J. R. S., DOI `10.57967/hf/1016`),
  declarado MIT no Hugging Face. O subconjunto `central_de_fatos` tem origem própria
  (Couto et al., *Central de Fatos*, DSW 2021). **Os termos de uso da Central de Fatos
  ainda precisam ser conferidos antes de usar esses dados no deploy.**
