# ADR-002 — Medir a busca antes de escolher modelo e banco

- **Status:** proposta técnica para revisão
- **Data:** 2026-09-29
- **Participantes da decisão:** Arquitetura, Dados, Modelos de IA e Engenharia
- **Relacionado:** [Exemplos e medições](../10-escolhas-com-evidencias.md), [ADR-001](ADR-001-texto-alegacao.md)

## Contexto

O sistema já tem TF-IDF na demonstração e um índice experimental com hashing lexical. Os dois comparam palavras. Uma amostra fictícia mostrou que ambos perderam uma reescrita e apontaram frases contraditórias como muito próximas. Também mostrou que um índice exato pequeno cabe em memória com folga. A qualidade com checagens reais ainda não foi medida.

## Decisão proposta

Manter a busca exata e os arquivos com manifesto no experimento atual. Comparar um modelo semântico candidato com os baselines lexicais em um conjunto revisado antes de alterar a aplicação. Não adotar banco vetorial nesta fase.

## Alternativas

| Alternativa | Quando faz sentido | Limite agora |
| --- | --- | --- |
| Manter só TF-IDF | Demonstração simples e verificável. | Pode perder reescritas. |
| Modelo semântico + busca exata | Se melhorar os casos aprovados e preservar a segurança nos negativos. | Precisa de dados e avaliação revisados. |
| Modelo semântico + banco vetorial | Se a busca exata falhar em metas reais de volume ou tempo. | Ainda não há evidência desse gargalo. |

## Como decidir com evidência

1. Dados e Produto aprovam qual frase representa cada alegação e o que conta como mesma alegação.
2. Um conjunto de teste com IDs estáveis inclui reescritas, negação, troca de pessoa/objeto, casos sem correspondência e fontes auditáveis; famílias de alegações não se repetem entre desenvolvimento e teste.
3. Modelos de IA compara os candidatos no mesmo conjunto e registra `Recall@1/3/5`, erros por tipo, falsos candidatos e custo de execução.
4. Engenharia mede o caminho completo, do texto recebido à lista de candidatos, com o volume e o uso esperados. Banco vetorial só vira proposta se a busca exata não atender às metas combinadas e uma alternativa melhorar o resultado em teste reproduzível.

## Consequências

A API fictícia continua demonstrável. Não há promessa de busca semântica pronta nem classificação de verdade. Evita-se pagar e operar uma infraestrutura ainda sem benefício medido. A decisão deve ser revista quando os dados aprovados, o benchmark e as metas de uso existirem.

## Resumo da etapa

Primeiro comprovamos que a busca nova ajuda; depois escolhemos o modelo. Um banco diferente só entra se houver um problema real de capacidade.
