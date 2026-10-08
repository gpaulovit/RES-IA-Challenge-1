## Why

O produto agora é um bot no Telegram (ver [docs/requisitos.md](../../../docs/requisitos.md)). O bot
precisa de duas peças de inteligência que a Engenharia chama por função:

- **Camada 1:** encontrar checagens de agências parecidas com a mensagem e dizer se a informação
  "já foi checada" ou se há uma checagem "relacionada" (RF-06, RF-07, RN-05, RN-06).
- **Camada 2:** quando não há checagem com semelhança alta, devolver uma faixa de alerta com os
  termos que pesaram (RF-08). Ela só vai ao ar se passar no critério escrito antes do teste
  (RN-04, RNF-02, RNF-03).

As changes anteriores (reciclagem de alegação e scoring de fake news) foram descartadas e estão
em `/archive`.

## What Changes

- `buscar(texto: str, k: int = 3) -> list[dict]`: devolve os campos da base de checagens mais
  `semelhanca` (0 a 1) e `faixa` (`ja_checado` / `relacionada` / `baixa`).
- Filtro de negação: quando a consulta e a checagem divergem em negação, `ja_checado` cai para
  `relacionada` (RN-06).
- Calibração dos limites da RN-05 no `data/testes_benchmark.json` (RNF-04, RNF-05).
- `classificar(texto: str) -> dict`: devolve `faixa` (`muitos_sinais` / `incerto` /
  `poucos_sinais`) e `sinais` (2 ou 3 termos), sem expor probabilidade (RNF-06).
- Um comando de treino gera modelo, métricas e parâmetros versionados com DVC (RF-14, RNF-10).
- Relatório de métricas com decisão `go`/`no-go` (US-08).
- **As assinaturas de `buscar()` e `classificar()` são contrato com o bot.** Qualquer mudança é
  avisada à Engenharia.

## Out of scope

Veredito próprio (RN-01); interface do bot, extração de link e registro de consultas (frente da
Engenharia); retreino automático.
