## Why

Quem recebe uma notícia política nova no WhatsApp não tem como saber, na hora, se ela se parece
com boatos que já circularam: a maior parte do que chega nunca foi checada por uma agência, e a
checagem humana demora. A equipe descartou a ideia anterior (recuperar a checagem que já existe
para a alegação, change `add-recycled-claim-semantic-retrieval`) porque os gates mostraram que a
**mesma alegação** raramente volta (1,4% dentro de um ciclo; 1,6% entre ciclos). Os mesmos gates
mostraram outra coisa: a **mesma narrativa** volta com frequência (62 de 71 pares dentro de 2022 e
53 de 59 pares entre 2013–2021 e 2022 foram rotulados `mesma` ou `tema`).

Esta change propõe um bot que estima a chance de uma notícia nova ser falsa a partir dessa
recorrência de narrativa, e um gate que testa a hipótese antes do produto:

> O padrão semântico das notícias falsas se repete ao longo do tempo? Se sim, um modelo que aprende
> esse padrão em um período consegue avaliar notícias de um período posterior.

## What Changes

- **Hipótese e gate de generalização temporal** (substitui o gate de reciclagem de alegação): um
  modelo treinado com notícias até 2021 precisa separar falsas de verdadeiras em 2022, com
  critério pré-registrado no `design.md` antes de rodar. Sem passar no gate, não há produto.
- **Base de treino com exemplos verdadeiros:** os corpora de checagem do projeto são quase só de
  boatos (FactPolCheckBr: 1.815 falsas, 9 verdadeiras; Central de Fatos: 10.286 e 141). Os
  exemplos verdadeiros vêm de Fake.br e FakeRecogna (subconjuntos do FactChecks.br), com auditoria
  explícita de viés de veículo, época e gênero textual.
- **Score calibrado** da chance de a notícia ser falsa, apresentado em faixas (padrão compatível
  com boatos conhecidos / incerto / pouco compatível / fora dos padrões conhecidos), nunca como
  veredito sobre a notícia.
- **Explicação do score:** as narrativas falsas conhecidas mais próximas da notícia, com a fonte
  de cada uma.
- **Robustez:** o score não muda com paráfrase, gíria, apelido ou erro de digitação. Negação não
  entra nessa lista, porque inverte o sentido.
- **Normalização dos rótulos de veredito** entre agências: deixa de ser só exibição e passa a ser
  o alvo do treino.
- **BREAKING (em relação à change anterior):** sai o contrato de busca de checagens (`POST
  /buscar` com candidatos e veredito original), as faixas confirmado/provável/sem match/inédito, o
  tratamento de alegação mista e a exposição de divergência entre agências como funções do produto.
- **Fora de escopo:** dizer se uma notícia é verdadeira ou falsa; verificação de fatos
  automatizada; impacto comportamental pós-lançamento (como na change anterior).

## Capabilities

### New Capabilities
- `fake-news-pattern-scoring`: estimativa calibrada da chance de uma notícia política nova ser
  falsa, a partir de padrões narrativos de boatos já checados; inclui o gate de generalização
  temporal, as faixas de resposta, a explicação por narrativas próximas, a robustez a reescrita e a
  normalização de rótulos.

### Modified Capabilities

Nenhuma: `openspec/specs/` ainda não tem capacidades sincronizadas. A capacidade
`claim-recurrence-retrieval` da change anterior nunca foi sincronizada e é abandonada.

## Impact

- **Dados:**
  - FactPolCheckBr (CC BY-NC-SA 4.0) e Central de Fatos (FactChecks.br v0.1) como exemplos falsos.
  - Fake.br e FakeRecogna (no mesmo zip do FactChecks.br) como exemplos verdadeiros. **As
    licenças originais de Fake.br, FakeRecogna e Central de Fatos precisam ser conferidas antes do
    deploy.**
  - Uso não comercial herdado do FactPolCheckBr.
- **Experimentos reaproveitados:** `experiments/limpeza.py` (passa a ser defesa contra vazamento
  de rótulo), `reescrita.py`, `normalizacao.py`, `corpora.py` (precisa manter o rótulo
  `is_fake`), os pares rotulados dos gates e a lista de modelos do notebook 06. A métrica de
  Recall@k de `avaliacao.py` deixa de ser critério do produto.
- **Protótipo (`src/checagens/`):** a API e a busca mudam de contrato; inspeção, organização e
  geração de embeddings continuam.
- **Documentação:** `docs/perguntas.md`, `docs/requisitos.md` e `docs/historias.md` reescritos
  nesta change. Cronograma, docs de engenharia, README raiz e `experiments/README.md` ficam
  pendentes.
- **Risco central:** um modelo que diz "provavelmente falsa" para notícia verdadeira causa dano
  direto. O desenho trata isso com calibração, faixa de incerteza e linguagem que nunca afirma
  veredito.
