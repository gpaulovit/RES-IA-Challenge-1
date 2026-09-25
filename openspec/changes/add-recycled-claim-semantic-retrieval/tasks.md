## 0. Protótipo de Engenharia com exemplos fictícios

Esta seção pode preceder o gate. Concluí-la não conclui as seções 1–4.

- [x] 0.1 Alinhar proposta, design e spec para permitir somente a demonstração fictícia antes do gate.
- [x] 0.2 Criar carregamento validado dos três exemplos, representação substituível e busca TF-IDF ordenada.
- [x] 0.3 Criar API local com saúde, busca, validação em português e identificação de demonstração.
- [x] 0.4 Verificar busca, erros, ordenação, limites, substituição de representação e caminho completo pela API.
- [x] 0.5 Documentar instalação, execução, funcionalidades, organização, testes, ciclo semanal, glossário e apresentação; verificar comandos e links.

Verificação do protótipo em 2026-09-22: instalação em ambiente virtual novo,
41 testes passando no Python 3.14.6, dependências compatíveis (`pip check`),
consultas HTTP reais de saúde, resultado conhecido e ausência de resultado,
e links locais dos guias conferidos. O CLI OpenSpec não está instalado neste
ambiente; os documentos foram revisados diretamente, sem validação pelo CLI.

## 1. Validação empírica de reciclagem (gate)

Avanço parcial de 1.1 em 22/09/2026: inspeção da versão
`e4b4feafce9b83789a517f649abb39ad4645f1b3` da fonte concluída, com
1.882 registros. Data e agência não têm vazios; há 8 datas fora do formato
informado e 738 ambíguas entre dia/mês e mês/dia, 50 vereditos e 4 textos
vazios, 1 link vazio, 11 nomes de agência e 5 ocorrências integralmente
duplicadas além das primeiras. Original preservado, sem correções ou exclusões.
Diagnóstico e reprodução em `docs/semana-1-engenharia.md`. Tarefa 1.1 permanece
aberta: organização e decisões sobre as lacunas serão tratadas na próxima etapa.

Organização implementada e executada em 24/09/2026: os 1.882 registros foram
preservados em ordem, com campos originais, versão da fonte e pendências
explícitas. A conversão foi repetida com saída idêntica. A tarefa continua
aberta até a frente de Dados validar o uso do título, as datas pendentes e os
vereditos ausentes; detalhes em `docs/semana-1-engenharia.md`.

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
