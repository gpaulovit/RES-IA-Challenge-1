# Perguntas Orientadas ao Problema

> Responsável: Ana Júlia (`papel: produto-decisao`). Atualizado em 07/10/2026.
> As perguntas levam ao produto descrito em [Requisitos](requisitos.md): um bot no Telegram que
> mostra checagens já publicadas e, quando não há, uma faixa de sinais de alerta.

## Natureza e causa raiz do problema

- Por que a desinformação política se propaga mais rápido do que a correção factual? O problema é de velocidade (checagem chega tarde), de alcance (checagem não chega aos mesmos canais) ou de credibilidade (o desmentido não é aceito mesmo quando chega)?
- O gargalo real está na produção da checagem (agências não conseguem cobrir volume), na distribuição dela (checagem existe mas não circula onde o boato circula), ou na demanda (o público não busca checar antes de compartilhar)?
- A desinformação política é majoritariamente narrativa reciclada (o mesmo enredo com outros personagens, datas e números) ou conteúdo genuinamente novo a cada ciclo eleitoral? Essa proporção define se um modelo treinado com o passado tem algo a dizer sobre o presente.

## Comportamento humano e psicologia do compartilhamento

- As pessoas compartilham desinformação política por não saberem que é falsa, ou por não se importarem (a alegação confirma uma crença prévia)? Isso muda radicalmente se uma ferramenta de checagem sequer teria efeito.
- Em que momento do processo de decisão o eleitor estaria disposto a checar uma informação — antes de compartilhar, ao receber, ou só quando já tem dúvida? Se ninguém checa antes de compartilhar, uma ferramenta reativa chega tarde por definição.
- Existe resistência à correção quando ela vem de uma fonte percebida como politicamente alinhada ao "outro lado"? Um score automático é percebido como mais ou menos neutro do que uma agência?

## Ecossistema e atores

- Quem já resolve pedaços desse problema hoje (agências de checagem, plataformas, iniciativas de letramento midiático, TSE) e onde exatamente está a lacuna que ninguém cobre?
- As próprias plataformas de mensageria (WhatsApp, Telegram) têm incentivo ou mecanismo técnico que limita estruturalmente qualquer solução externa (ex.: encriptação ponta a ponta impede varredura ativa, só permite consulta voluntária)?
- Existe regulação ou legislação eleitoral brasileira (TSE, marco de desinformação) que restringe um produto que atribui a uma notícia uma chance de ser falsa sem checagem humana?

## Escala e janela temporal do problema

- Qual é o ritmo real de surgimento de novos boatos por dia/semana em período eleitoral, comparado à capacidade de produção humana das agências de checagem? A distância entre os dois é o espaço que um score automático ocupa.
- O problema é sazonal e concentrado (picos em período eleitoral, com vale entre eleições) ou constante ao longo do tempo? Isso muda o modelo de sustentabilidade de qualquer solução, não só a técnica.

## Definição do sucesso

- O que conta como "resolver" esse problema — reduzir o volume de boatos em circulação, reduzir a velocidade de propagação, aumentar a proporção de pessoas que desconfiam antes de compartilhar, ou simplesmente aumentar a confiança pública no processo eleitoral? Cada definição aponta para uma solução completamente diferente.

## Norteadora do Problema

Um bot no Telegram consegue ajudar o eleitor a conferir, antes de repassar, uma mensagem sobre as
eleições de 2026 — mostrando a checagem de agência quando ela existe e um alerta honesto quando
não existe — sem afirmar por conta própria que algo é verdadeiro ou falso?

- Boa parte do que circula já foi checado de alguma forma? Nos testes do projeto, a mesma
  alegação voltou pouco (1,4% dentro de 2022; 1,6% entre ciclos), mas a mesma **narrativa** voltou
  com frequência (62 de 71 pares em 2022; 53 de 59 entre 2013–2021 e 2022). Por isso a busca
  procura checagens **parecidas**, não idênticas.
- Quando não há checagem, um classificador de texto distingue falsas de verdadeiras em textos de
  outra fonte ou época, ou só aprende o estilo do veículo? (RN-04 e RNF-02.)
- Como responder sem que o eleitor leia a resposta como sentença? (RN-01, RNF-06.)

## Do problema de negócio ao problema de ML

Seguindo os passos 1 a 5 da Zona A de Kreuzberger, Kühl e Hirschl (2023):

1. **Problema de negócio (R1):** eleitores recebem em grupos notícias e frases sobre as eleições
   de 2026 e repassam sem conferir, porque checar dá trabalho e a checagem humana demora.
2. **Arquitetura (R2):** bot do Telegram em Python → extração de texto → busca na base de
   checagens → classificador → resposta. Um único serviço, sem infraestrutura paga.
3. **Problema de ML (R3):** são dois.
    - **Busca por similaridade:** dado um texto, achar as checagens mais parecidas.
    - **Classificação binária supervisionada:** falsa × verdadeira, com a probabilidade
      convertida em três faixas de alerta.
4. **Quais dados (R3 + R4):** checagens de agências para a busca; notícias rotuladas para o
   classificador.
5. **Qualidade e rótulos (R3 + R4):** normalizar vereditos das agências, tirar carimbos como
   "FALSO" do texto, igualar o tamanho dos textos e testar com fonte ou época diferentes das do
   treino.

## Eixo 1 — Dados e Contexto Eleitoral

### Pergunta norteadora (Eixo 1)

As bases disponíveis têm volume e equilíbrio entre classes suficientes para (a) montar uma base
de checagens para a busca e (b) treinar e testar um classificador com fonte ou época diferentes,
sem que o rótulo seja explicado só pela fonte?

### Uso de cada dataset

| Dataset | Uso | Atenção |
| --- | --- | --- |
| [FactPolCheckBr](https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr) | busca (camada 1) | já tem pipeline no repositório |
| [FACTCK.BR](https://github.com/jghm-f/FACTCK.BR) | busca (camada 1) | checagens com veredito e link |
| [FactChecks.br](https://github.com/fake-news-UFG/FactChecks.br) | busca (camada 1) | conferir sobreposição com os outros dois |
| [Fake.br-Corpus](https://github.com/roneysco/Fake.br-Corpus) | treino do classificador | usar a versão com textos de tamanho igualado; falsas e verdadeiras vêm de sites diferentes |
| [FakeWhatsApp.Br](https://github.com/cabrau/FakeWhatsApp.Br) | treino e teste do classificador | mensagens de grupos, parecidas com o que o bot vai receber |
| [FakeTweet.Br](https://github.com/prc992/FakeTweet.Br) | teste extra do classificador | textos curtos |
| [BRACIS2019_FAKENEWS](https://github.com/phfaustini/BRACIS2019_FAKENEWS) | opcional | conferir se repete o Fake.br |
| [FakeNewsNet](https://github.com/KaiDMML/FakeNewsNet) | não usar | em inglês |

Antes de treinar, Domínio de dados confirma tamanho, período e licença de cada base.

### O que já sabemos do FactPolCheckBr

- **Parcialmente.** O volume (1.882 checagens, 9 agências com 50 a 315 registros cada) é suficiente para um MVP e para o gate. A cobertura, porém, é de **uma única campanha presidencial (ago–dez/2022)**, com 97% dos vereditos `falso` e forte concentração no tema urnas/sistema eleitoral.
- O índice é representativo da **desinformação da eleição presidencial de 2022**, não do "universo de boatos políticos brasileiros". Para o gate, a reciclagem deve ser medida dentro dessa campanha. Medir entre eleições exige suplementar a base com outros anos (a avaliar na issue #6).
- Os vereditos já vêm consolidados pela fonte (Falsa, Verdadeira, Parcialmente verdadeira e 50 vazios). A taxonomia do projeto mapeia esses quatro valores; os 50 vazios são, na maioria, checagens com várias alegações e não devem entrar no índice como alegação única.

- Como a base de checagens é quase toda `falso`, ela serve para a busca, não para treinar o
  classificador. As notícias verdadeiras do treino vêm do Fake.br e do FakeWhatsApp.Br.

## Eixo 2 — IA e NLP

### Expansão

- A busca por embeddings acha a checagem certa quando a mensagem vem com gíria, apelido ou erro
  de digitação? (Benchmark `data/testes_benchmark.json`, RNF-04.)
- A negação ("X fez" × "X NÃO fez") inverte o sentido, mas embeddings tendem a captar o tema e não
  a polaridade. Como evitar mostrar uma checagem do sentido oposto? (RN-06.)
- Um baseline simples (TF-IDF + regressão logística) já separa falsas de verdadeiras em textos de
  outra fonte ou época? Algo mais complexo só vale se o baseline mostrar sinal.
- O carimbo da agência ("É #FAKE", "#boato") e o estilo do veículo vazam o rótulo? Quanto o
  desempenho cai quando eles são removidos?

### Pergunta norteadora (Eixo 2)

Dentro do prazo do MVP, é possível ter uma busca que encontra a checagem certa mesmo com a
mensagem reescrita, e um classificador simples que separa falsas de verdadeiras em textos de
outra fonte ou época com qualidade mínima (RNF-02, RNF-03)?

## Eixo 3 — Decisão, Validação e Produto

### Expansão

- Quando mostrar uma checagem como "já checado" e quando como "relacionada"? (Faixas de
  semelhança, RN-05.)
- Como apresentar o alerta sem que ele vire veredito? Em três faixas (muitos sinais / incerto /
  poucos sinais), sem porcentagem, com os sinais que pesaram e com aviso de limitação. A resposta
  nunca diz "é falsa" ou "é fake".
- Como testar falsos alarmes antes de apresentar? Com as 32 notícias reais do benchmark (g1, UOL,
  CNN, Folha) e com notícias verdadeiras que o classificador nunca viu.
- O que o eleitor faz depois? Toda resposta indica agências e o canal do TSE.

### Pergunta norteadora (Eixo 3)

É possível definir regras de resposta que mostrem a checagem certa quando ela existe, alertem
sem afirmar veredito quando não existe, e mantenham o falso alarme sobre notícias verdadeiras
dentro de uma margem tolerável?

## Eixo 4 — Impacto Social e Cidadania

Este é o eixo onde preciso ser direto: as perguntas originais (redução de compartilhamento impulsivo, empoderamento do eleitor) descrevem impacto pós-lançamento, que depende de dados de uso reais — não são resolvíveis só com a concepção do produto. Vale reformular a norteadora para o que é respondível agora, e tratar o resto como hipótese a validar depois.

### Expansão

- É possível caracterizar, só a partir das bases disponíveis, padrões linguísticos associados ao canal de origem (ex.: alegações que circulam por WhatsApp vs. redes abertas) que sugiram diferentes estratégias de persuasão?
- Certas figuras públicas ou temas concentram desproporcionalmente boatos catalogados — isso é mensurável diretamente na base e serve como proxy de "vulnerabilidade de reputação"? (E, pelo Eixo 3, como risco de viés do score.)
- Existe literatura ou dado secundário (fora da base) que permita estimar, sem precisar coletar dado de uso, o tempo médio entre exposição a um boato e checagem por fontes oficiais — como proxy de "janela de exposição"?
- Que métricas de impacto (não de opinião, mas comportamentais) poderiam ser desenhadas desde já para serem coletadas assim que o produto for lançado, mesmo que não possam ser respondidas antes disso?

### Pergunta norteadora (Eixo 4) — reformulada

É possível, com os dados e a literatura correlata disponíveis nesta fase, projetar indicadores mensuráveis de impacto social (concentração temática de vulnerabilidade, padrões por canal) que sirvam de baseline, deixando explícito que a validação causal do efeito sobre o comportamento do eleitor depende de dados de uso pós-lançamento e não é resolvível na etapa de concepção?

## Perguntas de MLOps da disciplina

**1. Papéis (R1–R7).** R1 Produto: Ana Júlia · R3 Modelos de IA: Paulo · R4 Domínio de dados:
Cibelly · R6/R7 DevOps e MLOps: Ingrid · R2/R5 Engenharia: a confirmar.

**2. Problema de negócio → problema de ML.** Ver a seção "Do problema de negócio ao problema
de ML".

**3. Componentes que o sistema realmente precisa:**

| Componente | Usa? | Como |
| --- | --- | --- |
| C1 CI/CD | sim | GitHub Actions rodando `pytest` a cada push |
| C2 Repositório | sim | este repositório |
| C3 Orquestração | não | um script de treino basta neste tamanho |
| C4 Feature store | não | features calculadas no próprio pipeline |
| C5 Infra de treino | sim, mínima | máquina local ou Colab |
| C6 Model registry | simplificado | modelo versionado com DVC (já configurado) |
| C7 Metadata store | simplificado | arquivo de métricas e parâmetros salvo junto do modelo |
| C8 Serving | sim | o próprio bot carrega o modelo e faz inferência online |
| C9 Monitoramento | simplificado | registros anônimos e votos 👍/👎 |

**4. Gatilho de retreino.** Agenda manual. O índice de checagens é atualizado quando novas
checagens forem baixadas, sem retreinar (RNF-11). O classificador é retreinado quando houver 👎
revisados ou nova base rotulada.

**5. O que é monitorado e para onde vai o feedback.** Tempo de resposta, camada usada,
distribuição das faixas e votos. 👎 na camada 1 volta para o ajuste do limiar; 👎 na camada 2
vira exemplo para revisão e retreino; queda da semelhança média indica base de checagens
desatualizada.

## Referência

Kreuzberger, D.; Kühl, N.; Hirschl, S. *Machine Learning Operations (MLOps): Overview,
Definition, and Architecture.* IEEE Access, v. 11, p. 31866–31879, 2023.
[doi:10.1109/ACCESS.2023.3262138](https://doi.org/10.1109/ACCESS.2023.3262138)
