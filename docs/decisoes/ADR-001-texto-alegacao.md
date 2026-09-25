# ADR-001 — Campo canônico da alegação

- **Status:** proposta para revisão
- **Data:** 2026-09-25
- **Responsáveis pela decisão:** `dominio-dados` e `produto-decisao`
- **Responsável pela implementação:** Engenharia, após aprovação
- **Relacionados:** [pipeline e contratos](../05-pipeline-e-contratos.md) e [sugestões de issues](../06-sugestoes-de-issues.md)

## Contexto

O pesquisador precisa comparar a consulta da pessoa com uma unidade textual do acervo. O título da publicação não é necessariamente a alegação: pode resumir, criar suspense ou misturar contexto e conclusão. O corpo inteiro também mistura evidências e veredito. Sem uma unidade canônica, o índice pode encontrar o mesmo tema sem encontrar a mesma afirmação.

## Decisão proposta

Adotar `texto_alegacao` como unidade semântica do pesquisador: uma frase curta, verificável e sem o veredito. O título original permanece preservado, mas só pode ser usado como alegação quando sua origem e aprovação estiverem explícitas.

Exemplo:

```text
texto_alegacao: "Banqueiros apoiam Lula em troca da revogação do Pix."

Evitar: "É falso que banqueiros apoiam Lula..."
Motivo: a segunda frase mistura a alegação com o veredito.
```

## Por que Dados e Produto decidem juntos

- `dominio-dados` define a regra de anotação, garante origem e qualidade e marca incertezas.
- `produto-decisao` define o que conta como mesma alegação, cobertura parcial ou sem relação e como isso será comunicado.
- Engenharia garante schema, IDs, integridade e manifesto; ela não decide o significado do campo.
- IA/Modelos compara alternativas somente sobre alegações aprovadas e reporta falhas.

## Contrato mínimo

| Campo | Significado |
| --- | --- |
| `claim_id` | ID estável da alegação. |
| `claim_family_id` | Agrupa reescritas da mesma alegação para evitar vazamento entre splits. |
| `source_check_id` | ID da checagem ou publicação de origem. |
| `texto_alegacao` | Frase canônica, sem veredito. |
| `origem_alegacao` | `humano_aprovado`, `sugestao_pendente` ou `indisponivel`. |
| `trecho_evidencia` | Trecho ou referência que comprova a origem. |
| `status_indexacao` | `indexavel`, `nao_indexavel` ou `revisar`. |
| `motivo_status` | Justificativa objetiva do status. |
| `escopo_coberto` | `total`, `parcial` ou `incerto`. |

Uma publicação com alegações independentes deve gerar mais de um `claim_id`, todos ligados ao mesmo `source_check_id`, ou permanecer em revisão.

## Alternativas consideradas

| Alternativa | Uso | Decisão |
| --- | --- | --- |
| Título da checagem | Baseline técnico. | Não usar automaticamente no produto. |
| Corpo completo | Contexto para leitura humana. | Não usar como unidade principal. |
| Extração automática por IA | Sugestão futura. | Exigir revisão humana antes de indexar. |
| Alegação curada | Produto e benchmark. | Alternativa recomendada. |

## Consequências

- O índice passa a apontar para `claim_id` e preserva os metadados da publicação.
- O manifesto registra `campo_indexado=texto_alegacao`, versão do contrato e contagens por status.
- O benchmark referencia `claim_id` e separa splits por `claim_family_id`.
- A API futura retorna alegação histórica, evidência e escopo, mas não cria um novo veredito.
- A demonstração atual permanece intacta e identificada como fictícia.

## Critérios de aceite

- [ ] Dados e Produto aprovam o contrato e o guia de anotação.
- [ ] Todo positivo do benchmark aponta para `claim_id` indexável e fonte rastreável.
- [ ] Nenhum título é tratado como alegação sem `origem_alegacao` explícita.
- [ ] Cada vetor aponta para um `claim_id` único e elegível.
- [ ] Desenvolvimento e teste não compartilham `claim_family_id`.
- [ ] A resposta informa que pontuação mede proximidade, não verdade.

## Estado e próxima ação

Esta ADR ainda é uma **proposta**. A próxima ação é uma revisão curta entre `dominio-dados` e `produto-decisao`. Engenharia só altera o pipeline depois da aprovação ou do registro das divergências.

## Resumo final da etapa

Dados prova qual afirmação foi checada; Produto define quando duas afirmações significam a mesma coisa; Engenharia faz o sistema respeitar essa decisão. O campo canônico reduz o risco de confundir assunto parecido com a mesma alegação.
