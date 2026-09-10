## 1. Validação empírica de reciclagem (gate)

- [ ] 1.1 Consolidar o corpus FactPolCheckBr (texto da alegação + texto de
      verificação + veredito + data + agência) em um formato pronto para
      análise; verificar carregando o dataset e confirmando que a
      contagem de registros bate com a fonte (~1.882) e que data/agência
      estão preenchidas em cada registro.
- [ ] 1.2 Rodar clusterização temática latente (sem rótulo manual) sobre
      os embeddings do corpus; verificar inspecionando uma amostra dos
      clusters quanto à coerência temática e reportando número/tamanho
      dos clusters.
- [ ] 1.3 Rodar análise de recorrência temporal: para cada cluster/tema,
      checar se alegações reaparecem reescritas em períodos diferentes;
      verificar produzindo uma taxa de recorrência mensurável (ex.: % de
      alegações com pelo menos uma alegação semanticamente similar a
      >= N dias de distância) e uma conclusão escrita de go/no-go.
- [ ] 1.4 Registrar a decisão go/no-go do gate (atualizar `design.md` com
      o resultado); se no-go, parar e revisitar o escopo com o usuário
      conforme a mitigação de risco descrita em `design.md` antes de
      seguir para a seção 2.

## 2. Cobertura e preparação de dados

- [ ] 2.1 Construir um mapeamento curado dos rótulos de veredito de cada
      agência para uma taxonomia normalizada; verificar checando por
      amostragem se os registros mapeados batem com os rótulos de origem.
- [ ] 2.2 Avaliar a cobertura do corpus (amplitude temática, extensão
      temporal, volume por agência) à luz dos achados do gate; verificar
      produzindo um relatório curto de cobertura apontando lacunas
      identificadas (ver Open Question em `design.md` sobre suplementar
      com outros datasets se a cobertura for insuficiente).

## 3. Retrieval semântico robusto

- [ ] 3.1 Montar um conjunto de teste rotulado de pares de alegação
      parafraseada/adversarial (gíria, apelido, erro ortográfico,
      inversão de negação, e recorrência reescrita ao longo do tempo)
      derivado do corpus; verificar confirmando que o conjunto cobre cada
      categoria de reescrita citada no spec.
- [ ] 3.2 Comparar modelos de embeddings candidatos (multilíngue
      genérico, BERTimbau, fine-tuned em pares alegação↔veredito) contra
      o conjunto de teste; verificar reportando acurácia de retrieval
      top-k por modelo e por categoria de reescrita.
- [ ] 3.3 Implementar a indexação do corpus e o retrieval k-NN exato
      usando o modelo selecionado; verificar com os cenários "Claim is
      retrievable after indexing" e "Reworded historical claim is
      recognized as recurrence" do spec passando contra o conjunto de
      teste.

## 4. Política de decisão e responsabilidade

- [ ] 4.1 Calibrar os thresholds das faixas de confiança (confirmado/
      provável/sem match/inédito) usando a distribuição de scores de
      similaridade do conjunto de teste; verificar reportando taxa de
      falso-positivo/falso-negativo nos thresholds escolhidos usando
      alegações legítimas fora do corpus.
- [ ] 4.2 Implementar o tratamento de alegação parcial/mista de forma que
      um match só endosse a parte catalogada da alegação de entrada;
      verificar com o cenário "Mixed claim is not fully endorsed by a
      partial match" passando.
- [ ] 4.3 Implementar a detecção e exposição de divergência de veredito
      entre agências; verificar com o cenário "Divergent verdicts are
      both shown" passando contra um par conhecido de agências com
      veredito divergente para a mesma alegação subjacente.
- [ ] 4.4 Implementar a apresentação explicável de top-k (cada candidato
      mostrado com o texto-fonte com que foi comparado); verificar com o
      cenário "User can see why a match was returned" passando.
