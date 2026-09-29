# ADR-003 — Limitar entradas e preservar módulos existentes

- **Status:** proposta técnica para revisão
- **Data:** 2026-09-29
- **Participantes da decisão:** Arquitetura e Engenharia
- **Relacionado:** [Exemplos e medições](../10-escolhas-com-evidencias.md)

## Contexto

A API já rejeita texto vazio e JSON inválido. O código já separa dados, representação, busca e API. Faltava um limite claro para o tamanho do texto recebido; uma reorganização grande de pastas teria custo sem benefício demonstrado.

## Decisão proposta

Na demonstração local, aceitar no máximo 2.000 caracteres no campo `texto` e responder HTTP 422 quando o campo for inválido. Testar Unicode e outros idiomas como entradas válidas, sem prometer compreensão ou classificação do idioma. Preservar a divisão atual dos módulos. Adiar qualquer reestruturação até existir uma dependência ou responsabilidade nova que a justifique.

## Alternativas

| Alternativa | Avaliação |
| --- | --- |
| Sem limite de texto | Permite trabalho e consumo de memória sem necessidade na demonstração. |
| Limite de 2.000 caracteres no campo | Protege a busca local e mantém espaço para alegações longas; deve ser revisto com exemplos reais. |
| Mover tudo para pastas em camadas | Aumenta mudanças e risco de quebrar importações sem resolver falha observada. |

## Limites da decisão

O limite do campo não limita o corpo HTTP inteiro. Se a API for publicada, será preciso definir limites de requisição, acesso, volume de chamadas e cuidado com dados pessoais nos registros. Essas decisões dependem do ambiente de publicação.

## Resumo da etapa

Uma entrada exagerada recebe uma orientação clara. A organização atual já ajuda a trocar partes do sistema e deve ser mantida enquanto continuar simples de entender.
