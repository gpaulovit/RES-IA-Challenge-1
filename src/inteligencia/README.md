# `inteligencia`: camadas 1 e 2 do bot

Contrato entre a frente de Modelos de IA e o bot. **Se uma assinatura ou um campo mudar, avise a
Engenharia no grupo.** Desenho e decisões:
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
- A negação (RN-06) já vem aplicada: "X NÃO fez Y" contra "X fez Y" nunca sai como `ja_checado`.
- Pré-requisito: o índice em `data/indices/camada1/` (`dvc repro indice`) e o pacote instalado com
  `pip install -e '.[busca]'`. A 1ª chamada carrega o modelo (alguns segundos); depois, cerca de
  10 ms por busca.

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
| `busca.py` | camada 1: base, índice com hash, faixas e negação |
| `calibracao.py` | calibra os limites da RN-05 no `data/testes_benchmark.json` |
| `classificador.py` | camada 2: modelo, faixas e sinais |
| `treino.py` | treino com um comando (RF-14) e critério de go/no-go |
| `texto.py` | normalização de texto compartilhada |
