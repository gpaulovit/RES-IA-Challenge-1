# Escolhas de arquitetura, explicadas com exemplos

Este é um caderno de argumentos para discussão. As frases abaixo são fictícias. Os números vêm de uma amostra pequena, criada para revelar erros possíveis; **não medem a qualidade do produto com checagens reais**.

## 1. O que a busca atual realmente faz

Hoje a API de demonstração usa TF-IDF: dá peso às palavras que aparecem no texto. A `main` também tem um índice experimental com `baseline-hashing`, que transforma palavras em números de outra maneira. **Esse baseline ainda não entende significado**. Chamar qualquer lista de números de “busca semântica” seria enganoso.

| Consulta fictícia | Referência desejada | O que vimos na amostra | Lição |
| --- | --- | --- | --- |
| “No domingo, o coletivo municipal passou a ser gratuito.” | “A Câmara ... aprovou ônibus gratuitos aos domingos.” | Ambos os métodos lexicais deixaram de encontrar a referência. | Reescritas precisam ser testadas com um modelo de significado. |
| “A prefeitura ... **não** proibiu automóveis no centro.” | Nenhuma alegação equivalente. | TF-IDF apontou a frase sem “não” com pontuação 1,0; hashing deu 0,94. | Pontuação alta pode esconder uma contradição. |
| “A prefeitura ... proibiu **bicicletas** no centro.” | Nenhuma alegação equivalente. | A frase sobre automóveis apareceu em primeiro, acima de 0,87. | Mesmo lugar e ação não tornam duas alegações iguais. |

Na amostra de cinco alegações e nove consultas, os dois métodos encontraram a referência correta em primeiro lugar em cinco de seis casos positivos (`Recall@1 = 0,833`). Os três casos sem referência não foram classificados como acerto ou erro: **a busca ainda não tem regra aprovada para dizer “sem correspondência”**. Os números são uma demonstração, não uma meta alcançada.

**Argumento para a reunião:** “Temos uma razão concreta para comparar modelos de significado, mas precisamos testar também negação, troca de objeto e outros casos parecidos. A troca só vale se aumentar os acertos sem criar erros perigosos.”

## 2. Onde guardar os vetores

O arquivo JSON atual contém só três exemplos e é carregado uma vez ao iniciar a API; ele **não é relido a cada consulta**. O índice experimental já guarda vetores e metadados em arquivos separados com hashes de integridade. Para cerca de 1.882 registros, a busca exata compara todos os vetores sem exigir um serviço externo.

Uma medição local com **vetores sintéticos**, 1.882 linhas e 256 números por linha, ocupou 1.927.168 bytes (cerca de 1,84 MiB). A mediana da comparação em memória foi 0,008 ms em 100 consultas neste computador. Isso não inclui gerar o vetor da pergunta, carregar o índice, rede ou acesso simultâneo de várias pessoas. Os valores podem mudar em outra máquina.

| Opção | Ganho hoje | Custo ou limite |
| --- | --- | --- |
| Arquivos versionados por manifesto + comparação exata | Simples de repetir e auditar; suficiente para o tamanho atual. | É preciso refazer o índice quando o corpus mudar. |
| Banco vetorial | Pode ajudar se o acervo ou a carga crescerem muito e houver necessidade comprovada. | Acrescenta operação, migração, configuração e custo. |

**Decisão proposta:** manter o índice exato nesta fase. Reavaliar com medições de tempo completo, memória, atualizações e acessos simultâneos quando houver dados e requisitos de uso reais. A [ADR-002](decisoes/ADR-002-busca-e-armazenamento.md) registra o raciocínio.

## 3. Segurança e estabilidade

Texto vazio e JSON inválido já recebem resposta de validação. A melhoria proposta no programa limita o campo `texto` a 2.000 caracteres e testa textos longos, Unicode e outro idioma. Um idioma diferente pode produzir um candidato por coincidência de palavras; a resposta continua sendo apenas uma lista de candidatos, nunca um veredito.

| Situação | Resposta esperada |
| --- | --- |
| Campo vazio, tipo errado ou mais de 2.000 caracteres | HTTP 422 com orientação em português. |
| Texto válido, mas sem resultado | Lista vazia, sem afirmar que a alegação é verdadeira. |
| Arquivo do índice alterado | Rejeição pela conferência dos hashes. |
| API aberta ao público no futuro | Rever limite do corpo da requisição, acesso, volume de chamadas e registros de consulta antes de publicar. |

O limite do campo protege o processamento da busca; ele **não limita o tamanho total do corpo HTTP**. Essa proteção adicional só será necessária se a API deixar de ser uma demonstração local.

## 4. Organização do repositório

O código já separa leitura dos dados, representação de texto, busca e API em módulos. Isso permite trocar a representação nos testes sem alterar a API. Criar pastas `api/`, `core/` e `data/` agora moveria arquivos sem resolver um problema demonstrado. A regra é mudar a estrutura quando uma responsabilidade nova ou uma dependência difícil de manter justificar a mudança.

Para sua branch, a separação mais útil é de trabalho: decisões e exemplos aqui; alterações do programa em outra branch. Cada PR pode ser revisado por seu próprio motivo. A [ADR-003](decisoes/ADR-003-entradas-e-organizacao.md) registra essa proposta.

## Como repetir e interpretar

Na branch de avaliação do programa, depois da instalação indicada no README:

```sh
python -m checagens.avaliacao
python -m checagens.capacidade
python -m pytest -q
```

Os tempos são apenas uma fotografia da máquina. Os casos fictícios servem para argumentar sobre riscos e desenhar um teste real. A próxima decisão de produto depende de alegações aprovadas pela frente de Dados, um conjunto de teste revisado e comparação de modelos candidatos.

## Resumo da etapa

O projeto já tem uma base organizada para experimentar. A prioridade é medir se uma nova busca encontra melhor a mesma alegação sem confundir frases contraditórias. O banco atual pode continuar simples enquanto as medições não mostrarem uma necessidade diferente.
