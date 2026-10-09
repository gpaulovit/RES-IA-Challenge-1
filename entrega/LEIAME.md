# Entrega: modelos de IA do bot de checagem (frente de Modelos)

RES IA ELD UnB, Turma 2 · 09/10/2026 · Paulo Vitor Gomes
Repositório: <https://github.com/gpaulovit/RES-IA-Challenge-1> (branch `main`)

O bot tem duas camadas de IA:

| Camada | O que faz | Modelo | Resultado |
| --- | --- | --- | --- |
| 1. Busca de checagens | acha checagens de agências parecidas com a mensagem | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revisão `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` (pré-treinado) + limites calibrados | atende: top-3 em 71% (meta 70%), 0 de 32 notícias reais como "já checado" |
| 2. Sinais de alerta | sem checagem, diz se o texto tem cara de desinformação | TF-IDF + regressão logística (treinado por nós) | **no-go**: F1 0,67 (meta 0,75), falso alarme 31% (meta 15%) |

## O que tem nesta pasta

| Caminho | O quê |
| --- | --- |
| `notebook/modelos_camadas.ipynb` | **Notebook principal**: carrega, executa e avalia as duas camadas. Salvo já executado. |
| `models/classificador.pkl` | Modelo da camada 2 (pickle). Um dicionário: `pipeline` (scikit-learn) + `corte_alto` e `corte_baixo` |
| `models/classificador.joblib` | O mesmo modelo no formato recomendado pelo scikit-learn. É o arquivo que o código usa. |
| `data/indices/camada1/` | Índice da camada 1: vetores das 10.442 checagens, os registros e um manifesto com sha256 |
| `data/testes_benchmark.json` | Benchmark de 62 mensagens usado para calibrar e avaliar a camada 1 |
| `experiments/results/` | Métricas geradas pelo pipeline: `metricas_camada2.json`, `params_camada2.json`, `calibracao_camada1*.csv` |
| `src/inteligencia/` | Código das duas camadas (o mesmo que o bot usa). O contrato está em `src/inteligencia/README.md` |
| `params.yaml` | Parâmetros: semente, limites da camada 1, hiperparâmetros da camada 2 |
| `requirements.txt` | Versões usadas |
| `material_relatorio/` | Base para o relatório técnico: critério e resultado da camada 2, decisões de projeto, documentação dos dados |
| `SHA256SUMS` | Hashes dos modelos e do índice |

O modelo de embeddings (~470 MB) não vai na pasta: é público e baixa sozinho do Hugging Face na
revisão fixada acima, na primeira chamada de `buscar()`.

## Como usar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

```python
import sys; sys.path.insert(0, "src")
from inteligencia import buscar, classificar

buscar("Xandão recebeu 60 milhões do Molusco para fraudar as urnas")
# [{'alegacao': 'Alexandre de Moraes recebeu R$ 60 milhões de Lula para fraudar urnas…',
#   'veredito_original': 'Falsa', 'semelhanca': 0.97, 'faixa': 'ja_checado', …}, …]

classificar("URGENTE!!! compartilhem: as urnas foram fraudadas")
# {'faixa': 'muitos_sinais', 'sinais': ['URGENTE', 'foram', 'compartilhem']}
```

Só o `.pkl`, sem o pacote (dá a probabilidade, não a faixa):

```python
import pickle
m = pickle.load(open("models/classificador.pkl", "rb"))   # requer scikit-learn 1.9.1
p_falsa = m["pipeline"].predict_proba(["texto da mensagem"])[0, 1]
```

## O que roda só com esta pasta

- Seção 2 do notebook (camada 1 inteira, incluindo o benchmark) e a inferência da camada 2.
- A **avaliação da camada 2** no conjunto de teste precisa das bases de treino e teste, que não vão
  aqui: são da frente de Dados, têm licenças próprias e são regeneradas no repositório com
  `dvc repro` (ver `material_relatorio/dados.md`). As saídas dessa avaliação já estão no notebook
  executado e em `experiments/results/metricas_camada2.json`.

## Decisões que o relatório precisa citar

- O critério de go/no-go da camada 2 foi **escrito antes** de rodar o teste
  (`material_relatorio/relatorio-camada2.md`). A divisão de dados foi emendada, também antes do
  teste, para usar a base entregue pela frente de Dados.
- O `no-go` foi causado por **atalho de veículo**: o modelo aprendeu o estilo de jornal das
  notícias verdadeiras do Fake.br (seção 3.3 do notebook). Pela RN-04, o bot vai ao ar só com a
  camada 1.
- Os limites da camada 1 priorizam **nunca dizer "já checado" para notícia verdadeira**. O custo é
  mostrar a checagem certa em 38% dos boatos reescritos, embora ela esteja no top-3 em 71%
  (`material_relatorio/design-decisoes.md`).
