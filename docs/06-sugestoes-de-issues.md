# Sugestões de issues para revisão

Os textos abaixo podem ser copiados para o repositório do time depois de revisão. Eles não foram publicados. Cada issue entrega uma mudança verificável e preserva a API demonstrativa atual.

## P0 — Definir o `texto_alegacao` canônico

**Problema:** o título de uma checagem pode resumir a matéria, criar suspense ou juntar contexto; por isso, não deve ser indexado automaticamente como se fosse a alegação verificada.

**Proposta:** definir, com Dados, a regra de criação do `texto_alegacao`, registrar sua origem e manter título e corpo separados.

**Aceite:** contrato documentado; amostra revisada por humanos; registros incertos marcados; índice informa qual campo foi usado.

## P0 — Versionar um benchmark auditável

**Problema:** referências textuais frágeis dificultam repetir e auditar a avaliação.

**Proposta:** cada caso positivo deve apontar para um `id_referencia` estável. Registrar versão/hash do corpus, origem, anotação e split (`desenvolvimento` ou `teste`). Casos `sem_match` não devem ter referência.

**Aceite:** nenhum ID ausente ou órfão; nenhum `sem_match` com referência; splits sem a mesma alegação subjacente; benchmark com versão e hash.

## P0 — Medir recuperação separada da decisão

**Problema:** encontrar um texto próximo não equivale a classificar a alegação como falsa ou verdadeira.

**Proposta:** medir Recall@1/3/5 e MRR antes de criar faixas de confiança ou regras de produto.

**Aceite:** métricas gerais e por paráfrase, gíria, apelido, erro, negação, recorrência e controles negativos; relatório lista consultas que falharam.

## P1 — Ampliar controles negativos difíceis

**Problema:** exemplos sem relação são fáceis; o maior risco é recuperar algo sobre o mesmo tema, pessoa, local ou período, mas com alegação diferente.

**Proposta:** adicionar pares negativos difíceis e revisar manualmente a diferença entre as alegações.

**Aceite:** categorias de confusão registradas; exemplos cobrem entidades e contexto semelhantes; falsos positivos ficam rastreáveis.

## P1 — Versionar qualidade e elegibilidade

**Problema:** vereditos, cobertura parcial, divergências, datas e duplicatas podem ser tratados de formas diferentes entre execuções.

**Proposta:** preservar `veredito_original` e criar normalização versionada. Registrar `escopo_coberto`, divergência entre agências, elegibilidade para índice e grupos de duplicatas prováveis.

**Aceite:** regras e exceções documentadas; contagens antes/depois; nenhum original sobrescrito; versão gravada no manifesto.

## P1 — Criar avaliação reprodutível

**Problema:** uma métrica isolada não informa exatamente quais dados, código e modelo a produziram.

**Proposta:** fornecer um comando único que receba corpus, modelo e benchmark e gere artefato legível por máquina e por pessoa.

**Aceite:** saída registra hashes, revisão do modelo, versão do pipeline, métricas por estrato e consultas que falharam; execução limpa reproduz os resultados dentro de tolerância definida.

## P2 — Definir o contrato da futura resposta real

**Problema:** a demonstração não deve ser confundida com a resposta definitiva do produto.

**Proposta:** especificar, sem alterar a API atual, um contrato futuro contendo consulta, candidatos, IDs, trechos de evidência, URLs, datas, agência, veredito histórico, pontuação, versão do índice e avisos.

**Aceite:** schema e exemplo documentados; campos obrigatórios e opcionais claros; mensagens dizem que pontuação não é probabilidade de fake e que a decisão é humana.

## Ordem sugerida

1. Fechar o significado de alegação.
2. Congelar um benchmark rastreável.
3. Medir a recuperação.
4. Melhorar negativos e qualidade dos dados.
5. Automatizar a avaliação.
6. Especificar o contrato futuro do produto.

## Resumo final da etapa

As issues priorizam entendimento antes de infraestrutura. Primeiro o time define qual texto representa a alegação; depois cria uma prova auditável e mede se a busca encontra o item correto. Só então faz sentido falar em confiança ou resposta real. Isso reduz o risco de chamar “mesmo assunto” de “mesma alegação”.
