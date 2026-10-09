# Avaliação de Benchmark e Métricas de Recuperação (MLOps)

Este documento registra a metodologia, os resultados de linha de base (*baseline*) e os comandos de reprodução da avaliação empírica do sistema de recuperação semântica do RES-IA.

---

## 1. Por que este processo é parte de MLOps

Em conformidade com as diretrizes de MLOps do projeto, uma métrica isolada não tem valor sem contexto: **precisamos saber exatamente qual dado entrou, qual modelo foi avaliado, quais hashes garantem a integridade dos artefatos e qual foi o comportamento por categoria de linguagem**.

As métricas de avaliação e posicionamento no ranking estão implementadas em `experiments/avaliacao.py` e validadas nos testes de busca em `tests/test_busca.py`.

---

## 2. Estrutura do Benchmark

O conjunto de avaliação está versionado em [`data/testes_benchmark.json`](../data/testes_benchmark.json) e contém **62 casos de teste**, divididos em dois grandes blocos:

1. **Casos positivos (30 casos):** consultas que possuem correspondência direta com uma checagem histórica no corpus (`alegacao_ref_original`).
2. **Casos negativos de controle (32 casos):** notícias reais coletadas de portais (G1, CNN, UOL, Folha) sem relação com boatos desmentidos no corpus (`resultado_esperado: sem_match`).

### Estratos avaliados:

| Categoria | Casos | Objetivo de teste |
| --- | ---: | --- |
| `controle_falso_positivo` | 32 | Medir se o sistema evita falsos positivos diante de fatos legítimos fora da base. |
| `erro_ortografico` | 6 | Resistência a erros de digitação e escrita coloquial. |
| `giria` | 6 | Identificação de expressões típicas de redes sociais ("zap", "500k", "mole"). |
| `apelido` | 6 | Associação de apelidos e menções indiretas a entidades ("Xandão", "Mito", "Molusco"). |
| `negacao` | 6 | Sensibilidade a inversões de sentido ("Lula NÃO prometeu...", "Salário NÃO é..."). |
| `recorrencia_temporal` | 6 | Identificação de boatos antigos reciclados com nova data (ex: eleições de 2026). |

---

## 3. Métricas Avaliadas

* **Recall@1:** percentual de consultas em que a checagem correta apareceu na 1ª posição.
* **Recall@3 e Recall@5:** percentual de consultas em que a checagem correta esteve entre os 3 ou 5 primeiros candidatos retornados.
* **MRR (*Mean Reciprocal Rank*):** média ponderada do inverso da posição correta ($1/\text{rank}$), valorizando retornos no topo.
* **Score Top Médio:** pontuação média do primeiro candidato retornado (essencial para calibrar limiares de `sem_match`).
* **Latência:** tempo médio de inferência e busca por consulta em milissegundos.

---

## 4. Resultados da Linha de Base (`baseline-hashing-256`)

Executado sobre o índice de 1.882 registros em `data/indices/experimental`:

```text
======================================================================
 RELATÓRIO DE AVALIAÇÃO DE MLOPS - BENCHMARK DE RECUPERAÇÃO
======================================================================
 Modelo avaliado:           baseline-hashing-256
 Total de casos testados:   62
 Casos com referência:      30
 Casos controle negativo:   32
 Latência média / consulta: 0.88 ms
----------------------------------------------------------------------
 Recall@1 geral:  0.4000 (40.0%)
 Recall@3 geral:  0.6000 (60.0%)
 Recall@5 geral:  0.6000 (60.0%)
 MRR geral:       0.4889
======================================================================
 Categoria / Tipo          | Casos  | Rec@1   | Rec@5   | MRR     | Score Top
----------------------------------------------------------------------
 erro_ortografico          | 6      | 0.8333  | 0.8333  | 0.8333  | 0.5695
 recorrencia_temporal      | 6      | 0.3333  | 0.6667  | 0.5000  | 0.5397
 apelido                   | 6      | 0.3333  | 0.5000  | 0.3889  | 0.5277
 giria                     | 6      | 0.3333  | 0.5000  | 0.4167  | 0.4455
 negacao                   | 6      | 0.1667  | 0.5000  | 0.3056  | 0.6168
 controle_falso_positivo   | 32     | -       | -       | -       | 0.4614
======================================================================
```

### Análise dos resultados:
1. **Erros ortográficos:** O Hashing lexico-estatístico responde relativamente bem a variações de digitação (Recall@1 de 83,3%).
2. **Apelidos, gírias e negações:** Revelam o gargalo esperado de um modelo semântico denso. O baseline teve menos de 35% de Recall@1 em gírias e apelidos, e confundiu frases negativas com o boato original com alta pontuação (0.6168).
3. **Decisão para a Semana 2:** Esses números justificam a necessidade do gate de modelos de IA e estabelecem o patamar mínimo que os modelos densos (`sentence-transformers` / BERTimbau) devem superar.

---

## 5. Como Executar e Reproduzir
 
 Para validar as funções de ranking e testes de busca automatizados:
 
 ```sh
 pytest tests/test_busca.py
 ```
 
 Para reproduzir a análise empírica comparativa dos modelos e estratos do benchmark, utilize o notebook:
 
 ```sh
 jupyter notebook experiments/05_avaliacao.ipynb
 ```
 
 O cálculo das posições no ranking e métricas de Recall@k e MRR pode ser importado diretamente a partir de `experiments.avaliacao`.
