## 1. Limpeza

- [x] 1.1 Mover as changes descartadas para `/archive/openspec/` e contextualizar `openspec/config.yaml`; verificar com `git grep "openspec/changes/add-"` fora de `/archive`
- [x] 1.2 Mover os notebooks 03/04, os CSVs deles, `gate.py` e `historico-gates.md` para `/archive/experiments/`; reescrever `experiments/README.md` por assunto; verificar que o `pytest` passa
- [x] 1.3 `docs/refs.md` com datasets e Kreuzberger et al. (2023); atualizar `docs/_sidebar.md` e `docs/README.md`

## 2. Critério antes do teste

- [x] 2.1 Commitar `docs/relatorio-camada2.md` com critério, divisão e semente; verificar com `git log` que o commit é anterior a qualquer `metricas_camada2.json`

## 3. Camada 1 (protótipo em `experiments/`)

- [x] 3.1 `experiments/camada1.py`: índice com hash, `buscar()`, faixas e negação; testes com corpus fictício
- [x] 3.2 `experiments/calibrar_limiares.py`: RNF-04/RNF-05 no benchmark, `calibracao_camada1.csv` e `params.yaml`
- [x] 3.4 Normalização da consulta por dicionário (apelidos, internetês), antes da calibração oficial; top-3 relatado com e sem
- [x] 3.3 Rodar com a base da Cibelly e registrar o resultado (limites 0,86/0,76; `calibracao_camada1.csv`)

## 4. Camada 2 (protótipo em `experiments/`)

- [x] 4.1 `experiments/classificador.py`: treino com semente fixa, faixas e sinais; testes
- [x] 4.2 `experiments/treino.py` + `dvc.yaml`: `dvc repro` gera modelo, métricas e params; duas execuções iguais
- [x] 4.3 Rodar no teste, preencher o relatório e registrar `go`/`no-go` (**no-go**); avisar Produto

## 5. Subida para `src/inteligencia/`

- [x] 5.1 `src/inteligencia/` (`busca.py`, `calibracao.py`, `classificador.py`, `treino.py`) com as mesmas assinaturas; testes sem download de modelo
- [ ] 5.2 Avisar a Engenharia com as assinaturas e o formato do retorno
