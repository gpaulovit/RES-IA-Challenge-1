## 1. Evidência herdada e pré-registro

- [x] 1.1 Registrar o resultado do gate entre ciclos e a releitura por narrativa na change
      `add-recycled-claim-semantic-retrieval` (design.md, seções "Gate complementar: resultado" e
      "Substituição"); verificado: totais 28/25/6 conferem com
      `experiments/results/validacao_entre_ciclos.csv` + `_chave.csv`.
- [ ] 1.2 Preencher os limites do critério do gate (design.md, Decisão 4: AUC em A e B, ECE,
      Brier, distância mínima ao modelo-controle, tolerância de mudança de faixa) e commitar só o
      design.md; verificar que o commit é anterior a qualquer avaliação nos períodos de teste.

## 2. Base de treino e avaliação

- [ ] 2.1 Estender `experiments/corpora.py` para carregar Fake.br e FakeRecogna (do zip, com
      `csv.reader`) mantendo `is_fake`, ano, fonte e categoria; verificar contagens por ano e
      classe iguais à tabela do design.md.
- [ ] 2.2 Acrescentar a `experiments/limpeza.py` a remoção de carimbos de agência ("É #FAKE",
      "Boato –", nomes de agência no início) e conferir por diff: nenhum título que começa com um
      carimbo sobra, e os títulos de 2022 mudam só onde havia carimbo.
- [ ] 2.3 Montar os conjuntos dos testes A, B e C (design.md, Decisão 3) só com o recorte político
      e a unidade título/1ª linha; verificar por tabela de contagem por conjunto, ano, fonte e
      classe, e registrar o hash de cada conjunto no `experiments/README.md`.
- [ ] 2.4 Normalizar os rótulos de todas as fontes numa taxonomia única e gerar o relatório de
      cobertura; verificar que nenhum item sem mapeamento entra nos conjuntos.
- [ ] 2.5 Auditoria de atalho antes de treinar: medir quanto fonte e ano sozinhos predizem o
      rótulo em cada conjunto; verificar que a tabela está no relatório da Seção 4.

## 3. Linhas de base

- [ ] 3.1 Regressão logística sobre embeddings para cada modelo da lista do notebook 06, treinada
      só no período de treino; verificar que nenhum item do período de avaliação foi usado
      (assert por ano e por hash de texto).
- [ ] 3.2 Score por vizinhos (k-NN ponderado sobre os itens rotulados); verificar o mesmo assert de
      separação temporal.
- [ ] 3.3 Modelo-controle só com fonte e ano; verificar que roda nos mesmos conjuntos.

## 4. Gate de generalização temporal

- [ ] 4.1 Avaliar A e B com o critério commitado (AUC geral e por fonte, ECE, Brier, distância ao
      controle) e escrever o resultado no design.md como GO, NO-GO ou inconclusivo; verificar que
      os números citados batem com o CSV de resultados.
- [ ] 4.2 Rodar o teste C descritivo (falsas de 2022 por faixa; controles do g1 por faixa);
      verificar que o relatório separa os dois e informa o n de cada um.
- [ ] 4.3 Se o resultado for NO-GO ou inconclusivo, parar e rediscutir o escopo antes da Seção 5;
      verificar que a decisão está registrada no design.md.

## 5. Calibração e faixas

- [ ] 5.1 Calibrar o modelo escolhido num conjunto de validação dentro do período de treino;
      verificar ECE antes e depois no período de avaliação.
- [ ] 5.2 Definir os limites das faixas e o limite de "fora dos padrões" (similaridade máxima com o
      treino, calibrada com os controles do g1 e itens fora de política); verificar o cenário
      "Text far from all known narratives" da spec com esses controles.

## 6. Explicação e linguagem da resposta

- [ ] 6.1 Retornar os itens rotulados mais próximos com fonte, data e rótulo da agência, usando a
      busca k-NN exata existente; verificar o cenário "User sees why the score was given".
- [ ] 6.2 Escrever os textos de cada faixa sem afirmar veredito e com o aviso de limitação;
      verificar o cenário "High estimate" (nenhuma resposta usa "falsa" ou "fake" como conclusão
      sobre o item).

## 7. Robustez

- [ ] 7.1 Medir a estabilidade da faixa em `experiments/results/teste_reescrita.csv` sem a
      categoria `negacao`; verificar contra a tolerância pré-registrada (1.2).
- [ ] 7.2 Relatório à parte da categoria `negacao`; verificar que ela não entra na taxa de
      estabilidade.

## 8. Contrato da API (depois do GO)

- [ ] 8.1 Trocar `POST /buscar` em `src/checagens/api.py` por um endpoint de score com faixa,
      estimativa, vizinhos e aviso; verificar com testes de API para entrada válida, entrada
      vazia (erro de validação, cenário "Empty text") e gate não aprovado (sem score exposto).

## 9. Documentação

- [x] 9.1 Reescrever `docs/perguntas.md`, `docs/requisitos.md` e `docs/historias.md` para a nova
      ideia; verificar com grep que "superior à classificação", "já checad" e "recuperação
      semântica" só aparecem como histórico.
- [ ] 9.2 Atualizar `docs/cronograma.md` (semanas 2–5, papel de Modelos de IA), README raiz, docs
      de engenharia e `experiments/README.md` (pipeline 04/05/06); verificar com o mesmo grep nos
      arquivos tocados.
