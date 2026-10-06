# Experimentos: gate de reciclagem e modelos (issue #8)

Notebooks da frente **Modelos de IA** que respondem à seção 1 do
[`tasks.md`](../openspec/changes/add-recycled-claim-semantic-retrieval/tasks.md):
existe reciclagem temporal de alegações no corpus FactPolCheckBr? A decisão
(**NO-GO** para a premissa temporal dentro de um ciclo eleitoral) e os números estão em
[`design.md` → Gate Result](../openspec/changes/add-recycled-claim-semantic-retrieval/design.md).
O gate complementar, entre ciclos eleitorais, está em andamento (ver
[Gate entre ciclos](#gate-entre-ciclos-05-em-andamento)).

Este arquivo registra **como** cada número foi produzido: ambiente, dados, ordem de
execução, decisões de preparação e protocolo de rotulagem.

## Ambiente

```bash
python3 -m venv .venv
.venv/bin/pip install -r experiments/requirements.txt
.venv/bin/dvc pull                     # baixa experiments/data (ver "Dados (DVC)")
cd experiments
../.venv/bin/jupyter nbconvert --to notebook --execute --inplace 00_load_corpus.ipynb
# repetir para 01, 02 e 03, nessa ordem
```

- Python 3.14.6; versões fixadas em [`requirements.txt`](requirements.txt).
- Modelo de embeddings: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`,
  revisão do Hugging Face `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`.
- Os notebooks rodam a partir de `experiments/` (caminhos relativos `data/` e `results/`).
- **Execução atual:** 00 → 03 rodados de novo em 01/10/2026, no macOS, depois da
  limpeza compartilhada (`limpeza.py`). A 1ª execução (commit `726c6ef`) teve o 02 rodado no Linux.

### Reprodutibilidade por plataforma

| Etapa | Mesma máquina e ambiente | Outra plataforma (Linux × macOS) |
|---|---|---|
| 00 (limpeza) | idêntico (mesmo SHA-256) | idêntico |
| 01 (embeddings) | idêntico | **bits diferentes** (ponto flutuante): o hash do `.npy` muda, mas os resultados do gate não. A taxa no τ validado contou as mesmas 25 alegações nas duas plataformas. |
| 02 (clusters) | idêntico (atribuições 100% iguais em duas execuções) | **estrutura diferente** (ver [Clusterização](#clusterização-02-tarefa-12)) |
| 03 (gate) | idêntico | mesma decisão e mesmas alegações acima do τ validado |

Por isso, a reprodutibilidade dos embeddings se confere pelos **resultados** (contagens
do gate), e não pelo hash do `.npy`.

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

## Pipeline

| Arquivo | Entrada | Saída | Faz |
|---|---|---|---|
| `limpeza.py` | — | — | `limpar_titulo()` e `eh_multi_alegacao()`, **usadas pelo 00 e pelo 05** |
| `00_load_corpus` | `data/com_texto.csv` | `data/com_texto_limpo.csv` | dedup, datas, coluna `claim`, flags `agregador` e `multi_claim` |
| `01_embeddings` | `com_texto_limpo.csv` | `data/emb_minilm.npy` | embeddings normalizados de `claim`; teste título bruto × `claim` |
| `02_clusters` | `com_texto_limpo.csv`, `emb_minilm.npy` | `data/clusters.csv`, `results/kmeans_silhouette.csv`, `hdbscan_sweep.csv`, `coerencia_clusters.csv`, `umap_clusters.png` | clusterização temática (tarefa 1.2) |
| `03_recurrence` | os três acima | `results/taxa_reciclagem_grade.{csv,png}`, `validacao_pares.csv`, `precisao_por_faixa.csv`, `reciclagem_por_cluster.csv`, `data/pares_temporais.csv` | recorrência temporal e validação manual (tarefas 1.3–1.4) |
| `04_teste_reescrita` | — | — | vazio; Bloco 4 (tarefa 3.1), ainda não iniciado |
| `05_reciclagem_entre_ciclos` | `com_texto_limpo.csv`, `emb_minilm.npy`, `data/factchecksbr/central_de_fatos.tsv` | em andamento | gate complementar entre ciclos |

## Procedência e integridade (SHA-256)

| Arquivo | SHA-256 |
|---|---|
| `data/com_texto.csv` (fonte `e4b4feafce9b83789a517f649abb39ad4645f1b3`) | `7f0c9443dcf2d7fb15ef3320eb1bfeb8b0d67f4689a13757b33809f200e84681` |
| `data/com_texto_limpo.csv` | `45b54bb32629b435e1af29fc23e83b98b9c7da758239964c2aee540e6196fbc0` |
| `data/emb_minilm.npy` (macOS) | `d3446245288ca5ef58e0d9dcb34b77ad67f761ee734700e73053325d369714bd` |
| `data/pares_temporais.csv` | `071cfa867d7bed7264c5d781121ee3d541b2a49b90461a56174b68a2fd760b54` |
| `results/validacao_pares.csv` | `b625b1d80af9ac76371b03481237d6a3b0883f4f40161f87fb57aef952d3786c` |
| `data/factchecksbr/FactChecksbr.zip` (release v0.1) | `035faf96dcb851e166c330af4636689669b5ff032c46bec109178669317c31b3` |
| `data/factchecksbr/central_de_fatos.tsv` | `1b3c964b0f33b9b9845af4f11afd2ac4b623489535aa2e5cbf6cce324bad12c0` |

O `data/clusters.csv` não está na tabela: ele é regenerado pelo 02 sempre que as notas
de coerência mudam. A versão vale pelo `data.dvc` do commit.

O hash do `com_texto.csv` é o mesmo registrado pela Engenharia em
[`docs/semana-1-engenharia.md`](../docs/semana-1-engenharia.md). Para conferir:
`shasum -a 256 experiments/data/*.csv experiments/data/*.npy experiments/results/validacao_pares.csv`.

**Histórico de hashes do `com_texto_limpo.csv`:**

- `9c78394c…`: 1ª execução, usada no Gate Result de 29/09.
- `45b54bb3…`: depois da limpeza compartilhada (01/10). A coluna `claim` é idêntica
  (diff de 0 linhas); só `multi_claim` mudou em 6 linhas (ver abaixo).

## Decisões de preparação (00, `limpeza.py`)

| Decisão | Efeito | Motivo |
|---|---|---|
| Remover linhas com mesmo título + agência + data | 1.882 → 1.877 | Erro de coleta (bloco de índices 820–827 repetido). Títulos iguais em agências diferentes ficam: são cobertura paralela ou republicação. |
| Datas lidas como mês/dia/ano (`%m/%d/%Y`) | 8 datas viram `NaT` e saem da análise temporal | Formato do README da fonte; a ambiguidade foi validada (ver abaixo). |
| Coluna `claim` = título sem o enquadramento de veredito | 872 títulos alterados | Prefixos ("É falso que", "É #FAKE", "Vídeo engana ao afirmar que"…) e o sufixo `#boato` inflavam a similaridade entre assuntos sem relação: a média caiu de 0,254 para 0,213 após a limpeza (01). Só a 1ª letra vira maiúscula: o tokenizador diferencia caixa, então nomes próprios ficam intactos. |
| `ROTULO`: remove o rótulo de seção da agência (`#Verificamos:`, `#CaiuNaRede:`, `Checamos:`) | 0 títulos em 2022; ~1.650 na Central de Fatos | Exige `#` antes ou `:` depois, para não pegar o **verbo** ("Checamos as alegações de…"). É aplicado antes do prefixo de veredito, porque o rótulo pode vir sem veredito depois. |
| `multi_claim`: títulos que cobrem várias alegações | 25 em 2022 (19 "Veja o que é #FATO ou #FAKE…" + 6 "Checamos/Verificamos…" como verbo); excluídos de 02 e 03 | Não servem como alvo de busca. Na Central de Fatos, também "N boatos…" e "O melhor do Boatos.org em AAAA". |
| `agregador` = Fato ou Boato (Justiça Eleitoral) | 184 linhas; pares que o envolvem saem da taxa | Republica checagens de parceiros dias depois, o que imitaria reciclagem. |

**Mudanças de limpeza são conferidas por diff, não só por hash.** Toda alteração no
`limpeza.py` é seguida de um diff da coluna `claim` entre a versão anterior e a nova do
`com_texto_limpo.csv`. O hash diz que algo mudou; o diff mostra se a mudança está certa.
Foi o diff que pegou uma regex sem a âncora `^` alterando 25 títulos no meio da frase.

**Validação do formato das datas.** A Engenharia registrou 738 datas ambíguas
entre dia/mês e mês/dia. Conferimos com as datas que aparecem nas URLs das
checagens (Lupa, UOL Confere e Fato ou Fake: 645 links). Das 262 datas ambíguas
que têm data na URL, **256 batem como mês/dia e nenhuma como dia/mês**. As 12
divergências do total são de 1 dia ou de mês trocado em registros do Fato ou Fake.
Conclusão: a leitura mês/dia se sustenta. Reprodução:

```python
raw = pd.read_csv("data/com_texto.csv", dtype=str)
p = raw["Data da checagem"].str.extract(r"^(\d{1,2})/(\d{1,2})/(\d{4})$").astype(float)
u = raw["Link"].fillna("").str.extract(r"2022[/-](\d{2})[/-](\d{2})").astype(float)
amb = (p[0] <= 12) & (p[1] <= 12) & (p[0] != p[1]) & u[0].notna()
print(amb.sum(), ((p[0] == u[0]) & (p[1] == u[1]) & amb).sum(), ((p[1] == u[0]) & (p[0] == u[1]) & amb).sum())
# 262 256 0
```

## Clusterização (02, tarefa 1.2)

- **Entrada:** 1.852 alegações (sem multi-alegação).
- **KMeans** (k ∈ {10, 15, 20, 30, 40}, silhouette por cosseno): melhor k = 10, silhouette = 0,084.
- **HDBSCAN** sobre UMAP-5D (`n_neighbors=15`, `min_dist=0`, cosseno, `random_state=42`).
  A varredura está em `hdbscan_sweep.csv`.
- **Parâmetros:** `min_cluster_size=15`, `min_samples=3`, escolhidos na 1ª execução.

| | 1ª execução (Linux, 1.858 alegações) | Atual (macOS, 1.852) |
|---|---|---|
| Clusters | 36 | 24 |
| Ruído | 20,5% | 15,8% |
| Maior cluster | 10,2% | 25,3% |
| Silhouette | 0,058 | 0,029 |

**Achado: a clusterização deste corpus não é estável.** Seis alegações a menos e outra
plataforma mudaram a estrutura com os mesmos parâmetros. Os clusters servem só para
descrever o corpus e **não entram na decisão do gate**. A 1ª execução continua no histórico
(commit `726c6ef`).

### `data/clusters.csv`: uma linha por alegação

| Coluna | Conteúdo |
|---|---|
| `idx` | linha da alegação no `com_texto_limpo.csv` |
| `claim`, `Agência`, `Data da checagem` | a alegação, para ler o arquivo sem cruzar com outro |
| `cluster_hdbscan`, `cluster_kmeans` | cluster de cada método (`-1` = ruído no HDBSCAN) |
| `tamanho_cluster`, `top_termos_cluster` | tamanho e 8 termos característicos (TF-IDF por cluster) |
| `inspecionado` | `True` para os 10 clusters sorteados para inspeção (semente 42) |
| `nota_coerencia`, `comentario_coerencia` | nota do cluster (1 = mistura de temas, 2 = tema amplo com intrusos, 3 = tema único) |

O arquivo é ordenado por cluster, então as alegações de um mesmo cluster ficam juntas.

**Onde avaliar: `results/coerencia_clusters.csv`**, com 10 linhas, uma por cluster
inspecionado: tamanho, termos característicos e 8 alegações de exemplo (separadas por `|`).
Preencha `nota_coerencia` e `comentario` e rode o 02 de novo; as notas passam para o
`data/clusters.csv`. O 02 cria esse arquivo-modelo quando ele não existe ou ainda não tem
nenhuma nota. Se já houver notas e os clusters tiverem mudado (outro cluster sorteado ou
outro tamanho), o 02 para com erro em vez de colar a nota antiga num cluster que já é
outro. Isso evita o que aconteceu na reexecução de 01/10, quando o arquivo ficou com notas
de clusters que não existiam mais. O arquivo fica no git para revisão.

**Notas da execução atual (01/10/2026, Paulo):** média 2,2 nos 10 clusters inspecionados.
4 receberam nota 3 (257 alegações), 4 nota 2 (109) e 2 nota 1 (51). Os clusters de tema
único são os maiores (ex.: 11, votos "roubados" de Bolsonaro; 15, pesquisa Ipec; 17, urna
e boletim). As notas da 1ª execução (média 2,1) estão no commit `726c6ef` e valem só para
aquela clusterização.

## Recorrência temporal (03, tarefas 1.3–1.4)

- **Entrada:** 1.844 alegações (sem multi-alegação e sem data inválida); período de
  01/08 a 01/12/2022 (122 dias). Na 1ª execução eram 1.850; a diferença são as 6
  checagens "Checamos/Verificamos…" marcadas como multi-alegação.
- **Definição:** o par (*i*, *j*) é reciclagem quando `cos(i, j) ≥ τ` e *j* foi checada
  **pelo menos N dias antes** de *i* (diferença com sinal).
- **Filtros:** sem pares envolvendo o agregador; sem pares da mesma agência com `cos > 0,98`.
- **Taxa** = % de alegações com pelo menos um original. Grade com τ ∈ {0,75; 0,80; 0,85; 0,90}
  e N ∈ {7, 14, 30, 60}.
- **No τ validado (0,90, N = 7):** 25/1.844 = **1,36%**. São as mesmas 25 alegações da
  1ª execução (25/1.850 = 1,35%). Nenhum dos 71 pares de validação envolve as 6
  alegações excluídas.

### Protocolo de rotulagem (`results/validacao_pares.csv`)

- **Amostra:** pares com N = 7, estratificados por faixa de similaridade:
  - 8 por faixa na rodada 1 (semente 42);
  - faixas 0,80–0,85 e 0,85–0,90 completadas na rodada 2 (semente 43), com
    **cada alegação em no máximo um par**, para histórias muito checadas
    (ex.: o vídeo falso da pesquisa Ipec) não dominarem a amostra.
  - A faixa 0,85–0,90 parou em 25 pares: não havia mais alegações inéditas.
  - Total: 71 pares.
- **`rotulo`** (obrigatório, uma única opção):
  - `mesma`: a mesma alegação de fundo;
  - `tema`: mesma narrativa, alegação diferente;
  - `diferente`: sem relação.
- **Regra da negação:** o desmentido ("Lula não disse X") e a alegação ("Lula disse X")
  contam como `mesma`.
- **Regra do detalhe:** mesma história com data ou número diferente conta como `mesma`.
  O cenário alternativo, contando esses pares como `tema`, está no Gate Result e não
  muda a decisão.
- **`tipo`** (opcional, descreve a reescrita): `parafrase`, `negacao`, `detalhe` ou `repetida`.
  Nenhum par foi marcado `repetida`, o que indica que os filtros de agregador e
  duplicata funcionaram.
- **Anotação:** um único anotador (Paulo, frente Modelos de IA), em 29/09/2026.
  Não há medida de concordância entre anotadores: essa é uma limitação do gate.
- O CSV tem rótulos com espaço no início (ex.: `' mesma'`). O código aplica
  `strip().lower()` antes de contar.
- `validacao_pares_backup.csv` é a cópia automática feita antes da rodada 2. É
  mantido só para rastrear a mudança; a fonte da verdade é `validacao_pares.csv`.

### Resultados

Os números finais estão em `precisao_por_faixa.csv` e no Gate Result do `design.md`.
Os 34 pares `mesma` foram salvos em `data/pares_temporais.csv`, como insumo da
categoria temporal do conjunto de teste (tarefa 3.1).

### Pendências conhecidas no 03

- A célula `TAU = 0.75` imprime 16,5%, e o `reciclagem_por_cluster.csv` foi calculado
  com esse τ. **O gate invalidou τ = 0,75** (precisão de 12% na faixa 0,75–0,80).
  Esses dois números são exploratórios e não devem ser citados como taxa de reciclagem.
  O τ validado é 0,90.

## Gate entre ciclos (05, em andamento)

Testa a ressalva mais forte do Gate Result: a reciclagem **entre** eleições, que não é
observável num corpus de 122 dias.

- **Critério pré-registrado** no `design.md`, commit `3294219` (01/10/2026, 14:59), antes
  de calcular qualquer similaridade entre os corpora.
- **Corpus histórico:** subconjunto `central_de_fatos` do
  [FactChecks.br](https://github.com/fake-news-UFG/FactChecks.br), release v0.1
  (`https://github.com/fake-news-UFG/FactChecks.br/releases/download/v0.1/FactChecksbr.zip`).
  São 10.461 checagens de 2013 a 2021 (1.692 em 2018), de Boatos.org, UOL, Aos Fatos,
  G1, Estadão e Comprova.
- **Leitura:** o TSV é lido com `csv.reader`, sem o `load_dataset` do Hugging Face. O
  padrão do `load_dataset` é outro subconjunto (`fakebr`, notícias, não checagens), e o
  script de carregamento executa `eval()` sobre o conteúdo do arquivo. O `pd.read_csv`
  com `sep="\t"` desloca as colunas neste arquivo.
- **Alegação:** 1ª linha do `review_text`, limpa com a mesma `limpar_titulo()` do 00:
  8.106 títulos alterados, 69 `multi_claim`, 4 vazios.

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
