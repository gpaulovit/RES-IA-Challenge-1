# Perguntas Orientadas ao Problema

> **Reenquadramento (2026-10-06).** A primeira versão destas perguntas defendia um produto de
> **recuperação** da checagem já existente para cada alegação. A equipe descartou essa ideia:
> os gates mostraram que a mesma alegação quase não volta, mas a mesma **narrativa** volta com
> frequência. O produto passou a ser um bot que estima a **chance de uma notícia nova ser
> falsa** a partir desses padrões. A versão anterior está no histórico do git e na change
> [`add-recycled-claim-semantic-retrieval`](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-recycled-claim-semantic-retrieval);
> a nova está na change
> [`add-fake-news-pattern-scoring`](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-fake-news-pattern-scoring).

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

O padrão semântico das notícias falsas sobre política no Brasil se repete ao longo do tempo a ponto de um modelo treinado com boatos já checados de um período estimar, com confiabilidade, a chance de uma notícia nova de um período posterior ser falsa — sem que o que ele aprendeu seja só o veículo, a época ou o formato do texto?

- A unidade que se repete é a **narrativa** (o mesmo enredo com outros personagens, datas e números), e não a alegação idêntica? Evidência herdada: dentro de 2022, 62 de 71 pares rotulados foram `mesma` ou `tema`; entre 2013–2021 e 2022, 53 de 59. A mesma alegação, sozinha, voltou em só 1,4% (dentro do ciclo) e 1,6% (entre ciclos).
- Um modelo treinado até um ano separa falsas de verdadeiras no ano seguinte? E quando, além do ano, muda também a fonte? (Gate de generalização temporal, testes A e B do design.)
- O que o modelo aprende é narrativa ou atalho? Quanto fonte e ano, sozinhos, já predizem o rótulo?
- Usando os embeddings, é possível identificar clusters temáticos latentes (ex.: urnas eletrônicas, saúde, segurança pública) e acompanhar quais deles voltam a cada ciclo? Os clusters deste corpus se mostraram instáveis entre execuções, então servem para descrever, não para decidir.
- Existe sazonalidade nos boatos (picos em datas de debate, véspera de votação, resultado) que se correlacione com o tipo de narrativa?

### Pergunta norteadora (Eixo 1)

As bases disponíveis — FactPolCheckBr e Central de Fatos como exemplos falsos, Fake.br e FakeRecogna como exemplos verdadeiros — têm volume, cobertura temporal e equilíbrio entre classes suficientes, no recorte político, para treinar e testar um modelo em períodos diferentes, e quanto do rótulo é explicado só pela fonte e pela época?

- Ponto crítico conhecido: os corpora de checagem são quase só de boatos (FactPolCheckBr: 1.815 falsas, 9 verdadeiras; Central de Fatos: 10.286 e 141), e não há notícias verdadeiras de 2022 em volume.

## Eixo 2 — IA e NLP

Este eixo é o núcleo técnico: o modelo precisa aprender o padrão da narrativa, generalizar para o futuro e não se deixar enganar por reescrita de superfície.

### Expansão

- Um classificador simples sobre embeddings de frase (regressão logística) ou um score por vizinhos rotulados já separa falsas de verdadeiras fora do período de treino? Qual dos modelos de embeddings candidatos (multilíngues, BERTimbau) generaliza melhor?
- O score muda quando a notícia é reescrita com apelidos, gírias ou erros ortográficos propositais (comuns em corrente de WhatsApp)? Ele deveria se manter.
- A negação ("X fez" vs. "X não fez") inverte o sentido. Como o modelo se comporta? Embeddings tendem a captar o tema e não a polaridade, o que aqui é um risco, e não uma qualidade.
- O carimbo da agência ("É #FAKE", "#boato") e o estilo do veículo vazam o rótulo? Quanto o desempenho cai quando eles são removidos?
- Um modelo ajustado (fine-tuned) só vale a pena se as linhas de base mostrarem sinal e faltar capacidade, e não dados?

### Pergunta norteadora (Eixo 2)

Dentro do escopo de um MVP, é possível treinar um modelo sobre embeddings que estime de forma calibrada a chance de uma notícia política ser falsa em um período posterior ao do treino, estável a reescritas de superfície, e cujo desempenho não seja explicado pela fonte ou pela época?

## Eixo 3 — Decisão, Validação e Produto

Aqui a expansão é sobre o que o bot pode e não pode afirmar. Um score errado sobre uma notícia verdadeira causa dano direto, então a forma de apresentar importa tanto quanto o modelo.

### Expansão

- Como apresentar a estimativa sem que ela vire veredito?
  - Em faixas: compatível com narrativas falsas conhecidas / incerto / pouco compatível / fora dos padrões conhecidos.
  - As faixas saem de probabilidades **calibradas** (o que o modelo chama de 80% acontece em cerca de 80% dos casos), e não das probabilidades brutas.
  - A resposta nunca diz "é falsa" ou "é fake"; diz que a notícia se parece (ou não) com narrativas falsas já checadas, e aponta as agências para o veredito.
- O que fazer quando a notícia não se parece com nada que o modelo conhece?
  - Responder "fora dos padrões conhecidos" e dizer que o modelo não tem base para avaliar, independente da probabilidade.
- Como explicar o score?
  - Mostrar as notícias já checadas mais próximas, com fonte, data e o rótulo publicado pela agência. O usuário vê de onde vem a semelhança.
- Como testar falsos alarmes antes de ir a campo?
  - Usar notícias verdadeiras que o modelo nunca viu (as 32 manchetes do g1 já reunidas e o período de teste dos holdouts) e medir quantas caem em "compatível com narrativas falsas".
  - Relatar o score por figura pública mencionada: se uma pessoa concentra boatos no treino, notícias verdadeiras sobre ela podem ser marcadas injustamente.

### Pergunta norteadora (Eixo 3)

É possível definir faixas de resposta e uma linguagem que comuniquem a chance de uma notícia ser falsa sem afirmar veredito, com taxa de falso alarme sobre notícias verdadeiras dentro de uma margem tolerável para uso público, e com uma saída honesta para o que o modelo não conhece?

## Eixo 4 — Impacto Social e Cidadania

Este é o eixo onde preciso ser direto: as perguntas originais (redução de compartilhamento impulsivo, empoderamento do eleitor) descrevem impacto pós-lançamento, que depende de dados de uso reais — não são resolvíveis só com a concepção do produto. Vale reformular a norteadora para o que é respondível agora, e tratar o resto como hipótese a validar depois.

### Expansão

- É possível caracterizar, só a partir das bases disponíveis, padrões linguísticos associados ao canal de origem (ex.: alegações que circulam por WhatsApp vs. redes abertas) que sugiram diferentes estratégias de persuasão?
- Certas figuras públicas ou temas concentram desproporcionalmente boatos catalogados — isso é mensurável diretamente na base e serve como proxy de "vulnerabilidade de reputação"? (E, pelo Eixo 3, como risco de viés do score.)
- Existe literatura ou dado secundário (fora da base) que permita estimar, sem precisar coletar dado de uso, o tempo médio entre exposição a um boato e checagem por fontes oficiais — como proxy de "janela de exposição"?
- Que métricas de impacto (não de opinião, mas comportamentais) poderiam ser desenhadas desde já para serem coletadas assim que o produto for lançado, mesmo que não possam ser respondidas antes disso?

### Pergunta norteadora (Eixo 4) — reformulada

É possível, com os dados e a literatura correlata disponíveis nesta fase, projetar indicadores mensuráveis de impacto social (concentração temática de vulnerabilidade, padrões por canal) que sirvam de baseline, deixando explícito que a validação causal do efeito sobre o comportamento do eleitor depende de dados de uso pós-lançamento e não é resolvível na etapa de concepção?
