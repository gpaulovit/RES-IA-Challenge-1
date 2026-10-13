# `inteligencia`: camadas 1 e 2 do bot
** Desenho e decisões:
[`add-bot-intelligence-layers`](../../openspec/changes/add-bot-intelligence-layers/design.md).

```python
from inteligencia import buscar, classificar
```

## `buscar(texto: str, k: int = 3) -> list[dict]` (camada 1: RF-06, RN-05, RN-06)

Devolve as `k` checagens mais parecidas, da mais parecida para a menos:

```python
[{"id": "...", "alegacao": "Alexandre de Moraes recebeu R$ 60 milhões de Lula para fraudar urnas",
  "veredito_original": "Falso", "veredito_normalizado": "falso", "agencia": "Boatos.org",
  "data": "2022-10-05", "link": "https://...", "fonte_dataset": "...",
  "semelhanca": 0.91, "faixa": "ja_checado"},
 ...]
```

| `faixa` do 1º item | O bot diz (RN-05) | O bot faz |
| --- | --- | --- |
| `ja_checado` | "Essa informação já foi checada" | mostra a checagem e **não** roda a camada 2 |
| `relacionada` | "Encontrei uma checagem relacionada" | mostra a checagem com ressalva e roda a camada 2 |
| `baixa` | — | roda a camada 2 |

- `semelhanca` é de uso interno (registro, RF-13). Não mostre o número ao usuário (RNF-06).
- A consulta passa por um dicionário de apelidos e internetês antes da busca ("Xandão" → "Alexandre de Moraes", "ñ" → "não"). O bot pode mandar o texto como chegou.
- A negação (RN-06) já vem aplicada: "X NÃO fez Y" contra "X fez Y" nunca sai como `ja_checado`.
- Pré-requisito: o índice em `data/indices/camada1/` (`dvc repro indice`) e o pacote instalado com
  `pip install -e '.[busca]'`. A 1ª chamada baixa e carrega os dois modelos (~470 MB cada, alguns
  segundos depois de baixados); depois, cerca de 0,7 s por busca na CPU (RNF-01: < 5 s).

### Como a busca decide (3 etapas)

O MiniLM sozinho errava quando a mensagem tinha nomes famosos e uma palavra que ele não conhece:
"Flávio Bolsonaro e o tesouraço" saía como `ja_checado` com a checagem da saidinha de Natal, só
por citar Flávio Bolsonaro. Por isso a busca tem três etapas:

1. **Cosseno (MiniLM):** semelhança entre a mensagem e cada checagem. É o `semelhanca` devolvido.
2. **Candidatas (híbrida):** as 20 melhores pelo cosseno + as 20 melhores pela nota
   `cosseno + 0,2 × cobertura do assunto`. A cobertura é a fração das palavras de assunto da
   mensagem (as que não são nomes) presentes na checagem, pesadas pela raridade na base.
3. **Reranker:** um cross-encoder multilíngue (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`,
   Apache-2.0, revisão fixada) lê mensagem e checagem juntas e dá uma nota. A ordem e a faixa saem
   dessa nota:

| Faixa | Regra |
| --- | --- |
| `ja_checado` | nota ≥ 9, cosseno ≥ `limite_alta` e a mesma negação nos dois textos |
| `relacionada` | nota ≥ 4 |
| `baixa` | o resto |

Os valores ficam no topo de `busca.py`. Foram escolhidos por grade no benchmark de 62 mensagens e
em 25 perguntas soltas, numa região estável (notas de 3 a 5 dão o mesmo resultado):

| | Só cosseno | Com reranker |
| --- | --- | --- |
| Notícias reais (controles) com alguma checagem mostrada | 20/32 | 1/32 |
| Notícias reais como `ja_checado` | 1 | 0 |
| Checagem certa no top-3 (24 reescritas) | 17/24 | 21/24 |
| Checagem certa mostrada | 11/24 | 12/24 |
| 25 perguntas soltas com resposta certa | 13/25 | 22/25 |

`Buscador(..., reranquear=None, hibrida=False)` volta ao comportamento antigo (só cosseno), para
comparar. **`calibracao.py` ainda mede só o cosseno**: os números dele não descrevem a busca com
reranker.

## `classificar(texto: str) -> dict` (camada 2: RF-08)

```python
{"faixa": "muitos_sinais", "sinais": ["URGENTE", "urnas", "fraudadas"]}
```

- `faixa`: `muitos_sinais` / `incerto` / `poucos_sinais`. `sinais`: 2 ou 3 palavras do próprio
  texto, como o usuário escreveu. Não há probabilidade (RNF-06).
- **Só exiba se o [relatório da camada 2](../../docs/relatorio-camada2.md) disser `go` (RN-04).**
  Com `no-go`, sem checagem parecida, o bot responde que não encontrou e indica as agências.
- Pré-requisito: o modelo em `models/classificador.joblib` (`dvc repro treinar`).

## Erros

As duas funções levantam `ValueError` com mensagem em português para texto vazio, índice ou modelo
ausente e índice alterado depois de gerado. O bot deve capturar e responder com a mensagem padrão
(RNF-09).

## Arquivos

| Arquivo | O quê |
| --- | --- |
| `busca.py` | camada 1: base, índice com hash, busca híbrida, reranker, faixas e negação |
| `calibracao.py` | calibra os limites da RN-05 no `data/testes_benchmark.json` |
| `classificador.py` | camada 2: modelo, faixas e sinais |
| `treino.py` | treino com um comando (RF-14) e critério de go/no-go |
| `normalizacao.py` | desfaz apelidos e internetês da consulta antes da busca (RF-05); dicionários em `dicionarios/` |
| `texto.py` | normalização de texto compartilhada |
