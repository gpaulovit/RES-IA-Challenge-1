# Testes, Benchmark e Qualidade de Software (MLOps)

> Responsável: Ingrid (`papel: devops-mlops`). Atualizado em 08/10/2026 para a reta final do Bot.

Esta página reúne as instruções de execução de testes automatizados, critérios de qualidade não funcionais e como rodar a avaliação de benchmark de MLOps.

---

## 1. Como Executar os Testes Automatizados

Com o ambiente virtual ativado ou as dependências instaladas (`pip install -e '.[test]'`), execute a suíte completa de testes no terminal na raiz do repositório:

```sh
pytest -v
```

Ou utilizando a automação via **Makefile**:

```sh
make test
```

---

## 2. O Que a Suíte de Testes Confere

A suíte cobre tanto os componentes algorítmicos quanto os requisitos do Bot e conformidades regulatórias:

| Arquivo de Teste | Requisito / Foco | O que é verificado |
| :--- | :--- | :--- |
| `tests/test_robustez.py` | **RNF-09, RF-10, RF-11, RF-04** | Nenhuma entrada anômala derruba o bot (texto vazio, >5.000 caracteres, apenas emojis, áudio/vídeo/imagem, <5 palavras e links quebrados). |
| `tests/test_transparencia.py` | **RNF-07, RF-09, RN-01** | 100% das respostas contêm atribuição da agência e link (Camada 1) ou aviso de limitação e links oficiais TSE/agências (Camada 2). |
| `tests/test_registros.py` | **RF-12, RF-13, RN-03, RNF-08** | Registro de consultas e votos 👍/👎 em JSONL com garantia estrita de privacidade e conformidade com a LGPD (bloqueio de IDs pessoais). |
| `tests/test_reprodutibilidade.py`| **RNF-10** | Garante que o treino com semente fixa gera métricas e coeficientes idênticos em rodadas sucessivas. |
| `tests/test_manutencao.py` | **RNF-11** | Comprova que uma nova checagem entra na base apenas reindexando os vetores, sem necessidade de retreino. |
| `tests/test_mensagens_benchmark.py` | **RNF-01** | Valida a integridade do conjunto das 30 mensagens eleitorais de teste. |
| `tests/test_bases.py` | **RF-07, RN-02, RN-04** | Validação das bases de dados, regras de descarte, duplicatas e integridade temporal. |
| `tests/test_busca.py` | **RF-05, RF-06, RN-05** | Camada 1: busca vetorial k-NN por cosseno, ordenação do ranking e faixas de similaridade. |
| `tests/test_classificador.py` | **RF-08, RNF-02, RNF-03** | Camada 2: classificação em faixas de alerta, termos com maior peso e fallback. |
| `tests/test_normalizacao.py` | **RN-02** | Normalização de texto, remoção de diacríticos e pontuação. |
| `tests/test_experimentos.py` | **RN-04** | Limpeza de títulos de checagens e remoção de carimbos das agências. |

---

## 3. Avaliação de Benchmark (RNF-04 e RNF-05)

A aferição da busca semântica em relação a paráfrases, gírias, erros ortográficos e controles negativos utiliza o conjunto de benchmark versionado em `data/testes_benchmark.json`:

- As funções de cálculo de **Recall@k**, **MRR** e **posições no ranking** estão implementadas em `experiments/avaliacao.py`.
- O experimento empírico comparativo está documentado no notebook `experiments/05_avaliacao.ipynb`.
- Os testes automatizados da suíte (`tests/test_busca.py` e `tests/test_mensagens_benchmark.py`) garantem que os algoritmos de busca e as entradas de teste permaneçam íntegros a cada commit.

### Critérios de Aceitação:
- **RNF-04:** A checagem correta deve aparecer entre as 3 primeiras em **≥ 70%** dos 24 casos de reescrita, gíria, erro ortográfico e recorrência temporal.
- **RNF-05:** No máximo **2 de 32** notícias reais de controle podem ser classificadas falsamente como "já checado" (com casos de negação reportados à parte).

---

## 4. Medição de Desempenho e Latência (RNF-01)

Para aferir se o bot atende os requisitos de velocidade antes da apresentação:

```sh
python scripts/medir_latencia.py
```

### Critérios de Aceitação:
- **RNF-01:** Pelo menos **90%** das mensagens de texto devem responder em **até 5 segundos**, e links em **até 10 segundos**.

---

## 5. Pipeline de Integração Contínua (CI)

O repositório possui integração contínua automatizada via **GitHub Actions** (`.github/workflows/ci.yml`), que é acionada a cada `push` e `pull request`.

O pipeline executa:
1. Instalação e verificação de dependências em Python 3.11 e 3.12.
2. Execução da suíte completa com `pytest -v`.
3. Teste de fumaça (*Smoke Test*) do pipeline de indexação vetorial.
4. Teste de busca k-NN sobre a amostra.
