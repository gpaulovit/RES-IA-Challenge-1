# Perguntas Orientadas ao Problema

## Natureza e causa raiz do problema

- Por que a desinformação política se propaga mais rápido do que a correção factual? O problema é de velocidade (checagem chega tarde), de alcance (checagem não chega aos mesmos canais) ou de credibilidade (o desmentido não é aceito mesmo quando chega)?
- O gargalo real está na produção da checagem (agências não conseguem cobrir volume), na distribuição dela (checagem existe mas não circula onde o boato circula), ou na demanda (o público não busca checar antes de compartilhar)?
- A desinformação política é majoritariamente boato reciclado (mesmo conteúdo, nova roupagem) ou conteúdo genuinamente novo a cada ciclo eleitoral? Essa proporção muda completamente o valor de uma solução baseada em banco histórico.

## Comportamento humano e psicologia do compartilhamento

- As pessoas compartilham desinformação política por não saberem que é falsa, ou por não se importarem (a alegação confirma uma crença prévia)? Isso muda radicalmente se uma ferramenta de checagem sequer teria efeito.
- Em que momento do processo de decisão o eleitor estaria disposto a checar uma informação — antes de compartilhar, ao receber, ou só quando já tem dúvida? Se ninguém checa antes de compartilhar, uma ferramenta reativa chega tarde por definição.
- Existe resistência à correção quando ela vem de uma fonte percebida como politicamente alinhada ao "outro lado"?

## Ecossistema e atores

- Quem já resolve pedaços desse problema hoje (agências de checagem, plataformas, iniciativas de letramento midiático, TSE) e onde exatamente está a lacuna que ninguém cobre?
- As próprias plataformas de mensageria (WhatsApp, Telegram) têm incentivo ou mecanismo técnico que limita estruturalmente qualquer solução externa (ex.: encriptação ponta a ponta impede varredura ativa, só permite consulta voluntária)?
- Existe regulação ou legislação eleitoral brasileira (TSE, marco de desinformação) que já define o que conta como "boato verificável" e que restringe ou obriga certos comportamentos de um produto nesse espaço?

## Escala e janela temporal do problema

- Qual é o ritmo real de surgimento de novos boatos por dia/semana em período eleitoral, comparado à capacidade de produção humana das agências de checagem? Isso define se o problema é de escala ou de acesso.
- O problema é sazonal e concentrado (picos em período eleitoral, com vale entre eleições) ou constante ao longo do tempo? Isso muda o modelo de sustentabilidade de qualquer solução, não só a técnica.

## Definição do sucesso

- O que conta como "resolver" esse problema — reduzir o volume de boatos em circulação, reduzir a velocidade de propagação, aumentar a proporção de pessoas que veem a checagem antes de compartilhar, ou simplesmente aumentar a confiança pública no processo eleitoral? Cada definição aponta para uma solução completamente diferente.

## Norteadora do Problema

Existe evidência suficiente, nesta fase de concepção, de que o principal gargalo do combate à desinformação política no Brasil é a falta de acesso rápido e comparável a checagens já existentes — e não a falta de checagens em si, a falta de vontade do público em checar, ou uma barreira estrutural das plataformas de mensageria — de forma que um produto de recuperação semântica endereça a causa raiz do problema, e não apenas um sintoma secundário dele?

- Usando os embeddings das alegações já catalogadas, é possível identificar clusters temáticos latentes (ex.: urnas eletrônicas, saúde, segurança pública) sem depender de rótulos manuais prévios?
- Existe uma sazonalidade temporal nos boatos (picos em datas de debate, véspera de votação, resultado) que se correlacione com o tipo de entidade mencionada?
- Boatos antigos "ressurgem" reciclados em novos eventos eleitorais? Isso é detectável via similaridade semântica entre alegações de anos diferentes na base?
- Há uma diferença estrutural mensurável entre o texto da alegação (como o boato circula) e o texto do veredito (como a agência escreve), que o modelo precise aprender a atravessar?

### Pergunta norteadora (Eixo 1)

A base de dados consolidada do FactPolCheckBr possui volume, cobertura temática e temporal suficientes para sustentar um índice semântico representativo do universo de boatos políticos brasileiros, validável por meio de clusterização e análise de distribuição dentro desta fase de concepção?

## Eixo 2 — IA e NLP

Este eixo já é o núcleo técnico central, então a expansão é sobre robustez e limites conhecidos do que embeddings conseguem fazer.

### Expansão

- O modelo mantém a correspondência correta quando a alegação é reescrita substituindo nomes de figuras públicas por apelidos, gírias regionais ou erros ortográficos propositais (comuns em corrente de WhatsApp)?
- Existe degradação de precisão quando a alegação inverte a polaridade da afirmação (ex.: "X fez" vs. "X não fez"), já que embeddings tendem a captar tópico mas não necessariamente negação?
- Um modelo fine-tunado com pares (alegação informal → checagem oficial) supera um modelo genérico pré-treinado sem ajuste, mesmo com poucos exemplos rotulados disponíveis?
- Qual é o comportamento do modelo diante de paráfrase adversarial deliberada (reescrita para escapar de detecção), versus paráfrase natural e não intencional?
- A comparação entre modelos (ex.: BERTimbau, modelos multilíngues tipo LaBSE, embeddings de propósito geral) já é possível de responder nesta fase apenas com a base existente, sem necessidade de dados de produção?

### Pergunta norteadora (Eixo 2)

Dentro do escopo de um MVP, é possível selecionar (ou ajustar) um modelo de embeddings que recupere corretamente a checagem correspondente para uma parcela relevante de alegações parafraseadas ou informais, validando empiricamente a busca semântica como abordagem superior à classificação estilística de "fake ou não"?

## Eixo 3 — Decisão, Validação e Produto

Aqui a expansão principal é sobre o que fazer nas zonas cinzentas, que é onde produtos desse tipo geram mais dano se malfeitos.

### Expansão

- Em vez de um único threshold binário, faz sentido um sistema de faixas de confiança (match confirmado / match provável, sugerir conferência humana / sem match, alegação inédita)?
   - Sim, faz sentido. Adotaremos uma política de faixas em vez de decisão binária:
     - **Alta similaridade (ex.: ≥ 80%):** *Match verificado.* Exibe o veredito oficial com link da agência.
     - **Média similaridade (ex.: 60% a 79%):** *Match provável.* Apresenta o resultado como "Alegação similar encontrada no acervo" e solicita conferência do usuário.
     - **Baixa similaridade (ex.: < 60%):** *Não catalogado / Alegação inédita.* Resposta transparente indicando que não há checagem histórica correspondente no banco.

- Como o sistema deve tratar uma alegação que é parcialmente verdadeira misturada com uma parte falsa já checada — retornar o veredito da parte catalogada arrisca "endossar" a parte não checada?
  - Não retornaremos o veredito de forma genérica para o texto inteiro. Quando houver correspondência apenas com um trecho específico, o sistema exibirá um aviso de limitação de escopo.
  - A resposta mostrará explicitamente qual trecho foi encontrado no acervo e informará ao usuário que o veredito se aplica exclusivamente a essa alegação catalogada, sem validar ou desmentir o restante do texto não checado.
 
- É viável apresentar ao usuário o top-k de candidatos mais próximos com explicação do porquê do match, em vez de uma resposta única e opaca, para mitigar erro de confiança excessiva?
    - Sim, é totalmente viável e será adotado. Em vez de uma resposta única e categórica, o produto exibirá o Top-K (limitado aos 2 ou 3 candidatos mais semelhantes).
    - Para cada candidato retornado, o sistema apresentará:
      - A porcentagem/grau de similaridade semântica.
      - O texto original da alegação catalogada.
      - O veredito e o link direto para a checagem oficial da agência.
    - Isso evita o efeito de "caixa-preta", dando transparência sobre o porquê daquele resultado ter sido encontrado e permitindo que o próprio usuário compare as informações.

- Como o produto deve se posicionar quando o veredito de duas agências de checagem diverge para alegações semanticamente equivalentes?
    - O produto manterá uma postura de neutralidade e transparência. Caso duas ou mais agências apresentem vereditos divergentes (ex.: uma carimbou como "Falso" e outra como "Distorcido" ou "Sem Provas") para a mesma alegação:
      - O sistema não tentará decidir qual veredito é o "correto".
      - A interface exibirá os vereditos de ambas as agências lado a lado no Top-K.
      - O produto incluirá um alerta explícito indicando a existência de divergência no ecossistema de checagem, disponibilizando os links das duas fontes para que o usuário leia os fundamentos de cada uma.

- Existe um teste possível, ainda nesta fase, para simular "falsos positivos" com alegações reais e legítimas fora da base, medindo taxa de erro antes de ir a campo?
    - Sim, é viável e necessário ainda nesta fase de concepção.A metodologia consiste em:
      - Criar um conjunto de controle de validação com 20 a 30 declarações legítimas e notícias reais recentes (que não constam no acervo do FactPolCheckBr).
      - Rodar a busca semântica dessas alegações verdadeiras contra o banco de boatos e medir a taxa de colisão (porcentagem de notícias verdadeiras classificadas erroneamente com alta similaridade).
      - Usar esses dados empíricos para calibrar os limiares de corte (thresholds) e definir a zona de baixa similaridade/fallback antes de ir para a fase de desenvolvimento da interface.

### Pergunta norteadora (Eixo 3)

É possível, com os dados e modelos disponíveis nesta fase de concepção, definir uma política de decisão (threshold(s) + tratamento de fallback) que separe de forma confiável alegações já checadas de alegações inéditas ou ambíguas, dentro de margens de erro toleráveis para uso público?

- **Sim, é totalmente possível.** A combinação da política de decisão em 3 faixas de confiança com a exposição transparente do Top-K e avisos explícitos para casos ambíguos/mistos permite separar com segurança o conteúdo catalogado do inédito.
- A validação prática dessa política será respaldada pelo teste de falsos positivos com dados de controle ainda na fase de concepção, garantindo margens de erro toleráveis antes da implementação final do produto.

## Eixo 4 — Impacto Social e Cidadania

Este é o eixo onde preciso ser direto: as perguntas originais (redução de compartilhamento impulsivo, empoderamento do eleitor) descrevem impacto pós-lançamento, que depende de dados de uso reais — não são resolvíveis só com a concepção do produto. Vale reformular a norteadora para o que é respondível agora, e tratar o resto como hipótese a validar depois.

### Expansão

- É possível caracterizar, só a partir da própria base do FactPolCheckBr, padrões linguísticos associados ao canal de origem (ex.: alegações que circulam por WhatsApp vs. redes abertas) que sugiram diferentes estratégias de persuasão?
- Certas figuras públicas ou temas concentram desproporcionalmente boatos catalogados — isso é mensurável diretamente na base e serve como proxy de "vulnerabilidade de reputação"?
- Existe literatura ou dado secundário (fora da base) que permita estimar, sem precisar coletar dado de uso, o tempo médio entre exposição a um boato e checagem por fontes oficiais — como proxy de "janela de exposição"?
- Que métricas de impacto (não de opinião, mas comportamentais) poderiam ser desenhadas desde já para serem coletadas assim que o produto for lançado, mesmo que não possam ser respondidas antes disso?

### Pergunta norteadora (Eixo 4) — reformulada

É possível, com os dados e a literatura correlata disponíveis nesta fase, projetar indicadores mensuráveis de impacto social (concentração temática de vulnerabilidade, padrões por canal) que sirvam de baseline, deixando explícito que a validação causal do efeito sobre o comportamento do eleitor depende de dados de uso pós-lançamento e não é resolvível na etapa de concepção?
