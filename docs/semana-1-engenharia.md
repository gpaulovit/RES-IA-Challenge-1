# Semana 1 — Engenharia, uma etapa por vez

**Etapa 1 concluída: conhecemos a base e registramos seus problemas. A base
ainda não foi corrigida nem preparada para a busca real.**

## 1. O que estamos tentando fazer

A Semana 1 pede uma base pronta para análise. Antes de transformar qualquer
informação, precisamos entender o que recebemos. Pense em uma planilha: cada
registro é uma checagem e cada coluna descreve uma característica dela.
CSV é uma maneira de guardar essa planilha em texto. Um campo pode conter
vírgulas e várias linhas; contar as linhas do arquivo não basta para contar registros.

| Etapa | Entrega | Situação |
| --- | --- | --- |
| 1. Conhecer | Original preservado, origem registrada e diagnóstico | Concluída |
| 2. Organizar | Conversão repetível, mantendo valores originais e problemas visíveis | Aguardando continuidade |
| 3. Conferir | Testes da conversão e instruções para outro computador | Aguardando etapa 2 |
| 4. Alinhar | Pendências com Produto e síntese da semana | Aguardando etapas anteriores |

## 2. De onde vieram os dados

- Fonte: [Dataset-FactPolCheckBr, Interfaces-UFSCAR](https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr).
- Arquivo: `dados/com_texto.csv`.
- Versão consultada: `e4b4feafce9b83789a517f649abb39ad4645f1b3`.
- Cópia obtida em **22/09/2026 às 18:44:09 UTC** (15:44:09 em Brasília).
- Tamanho: **5.035.762 bytes**.
- Identificação SHA-256: `7f0c9443dcf2d7fb15ef3320eb1bfeb8b0d67f4689a13757b33809f200e84681`.

A versão identifica o estado do repositório da fonte. O SHA-256 funciona como
uma impressão digital do arquivo: se seu conteúdo mudar, a identificação muda.
Usamos os dois para permitir que outra pessoa repita a inspeção do mesmo material.

Atribuição: Interfaces — Núcleo de Estudos Sociopolíticos dos Algoritmos e da
Inteligência Artificial. A fonte declara [licença CC BY-NC-SA 4.0](https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr/blob/e4b4feafce9b83789a517f649abb39ad4645f1b3/LICENSE.md).
O CSV original e os resultados automáticos ficam locais, fora do Git; este
diagnóstico e o programa que o reproduz fazem parte do projeto.

## 3. O que cada coluna significa

| Coluna original | Como entender | Campos vazios |
| --- | --- | ---: |
| `Link` | Endereço da checagem de origem | 1 |
| `Título da checagem` | Título escrito pela agência | 0 |
| `Data da checagem` | Data registrada na fonte | 0 |
| `Natureza da notícia` | Veredito registrado pela fonte | 50 |
| `Candidato(s) favorecidos(s) pela notícia falsa` | Atribuição de favorecimento registrada no dataset | 0 |
| `Agência` | Nome da fonte que fez a checagem | 0 |
| `texto` | Texto coletado da página da checagem | 4 |

“Vazio” significa campo sem conteúdo ou contendo apenas espaços/quebras de
linha. Essa verificação não detecta todos os textos incompletos, marcadores de
ausência escritos por extenso ou erros de conteúdo. Link preenchido também não
significa página acessível: os endereços não foram visitados um a um.

**Título não é necessariamente o boato original.** Um título pode já trazer a
correção ou a conclusão da agência. Não criamos um campo “alegação original”
a partir dele. Essa escolha precisa ser combinada com a frente de Dados.

## 4. Resultados da inspeção

### Quantidade e estrutura

Encontramos **1.882 registros**, exatamente a quantidade informada para
`com_texto.csv` no [README da fonte](https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr/blob/e4b4feafce9b83789a517f649abb39ad4645f1b3/README.md).
Todos os registros têm os sete campos esperados. Isso confirma a contagem,
mas não garante que cada registro esteja completo ou correto.

### Datas: preenchidas, mas com formatos diferentes

O README da fonte descreve mês/dia/ano. **Oito registros** não seguem esse
formato: os registros 1609–1615 contêm `30/10/2022` e o 1616, `31/10/2022`.
Eles são datas possíveis quando interpretados como dia/mês/ano.

Há **738 datas ambíguas**: são possíveis nos dois formatos, mas representam
dias diferentes. Por exemplo, `8/2/2022` pode significar 2 de agosto ou 8 de
fevereiro. Isso não prova que as 738 estejam erradas; indica que não devemos
trocar o formato automaticamente sem conferir a origem.

Nenhuma data é impossível nos dois formatos testados. Se usarmos somente o
formato informado no README, o intervalo dos registros aceitos vai de
01/08/2022 a 01/12/2022. **Esse intervalo é provisório**, exclui as oito datas
fora desse formato e não é uma conclusão sobre a cobertura temporal real.

### Agências

O CSV contém **11 nomes distintos**, embora o README descreva dez arquivos de
agências. A distribuição observada é:

| Agência, exatamente como registrada | Registros |
| --- | ---: |
| AFP Checamos | 196 |
| Agência Lupa | 245 |
| Aos Fatos | 314 |
| Boatos.org | 315 |
| CNJ | 1 |
| E-farsas | 50 |
| Fato ou Boato (Justiça Eleitoral) | 184 |
| Fato ou Fake | 172 |
| Folha de S. Paulo | 2 |
| Projeto Comprova | 175 |
| UOL Confere | 228 |

A contagem total bate, mas os nomes e volumes não reproduzem toda a distribuição
descrita no README da fonte. A causa ainda não foi investigada; não renomeamos
nem redistribuímos agências para forçar concordância.

### Possíveis duplicações

| Comparação exata | Grupos repetidos | Ocorrências além da primeira |
| --- | ---: | ---: |
| Todos os sete campos | 5 | 5 |
| Link preenchido | 6 | 6 |
| Título | 19 | 20 |
| Texto preenchido | 6 | 6 |

Essas contagens se sobrepõem; não devem ser somadas. Mesmo título não comprova
registro duplicado. As comparações preservam maiúsculas, acentos e espaços;
não detectam duplicações aproximadas. **Nenhum registro foi removido.**
Os números dos registros envolvidos estão no relatório JSON local.

## 5. Como repetir e conferir

Na raiz do repositório, use o ambiente instalado conforme o README:

```sh
source .venv/bin/activate
python -m checagens.inspecao --baixar
```

No Windows, ative com `.venv\Scripts\Activate.ps1`. O download usa `curl`, que
precisa estar disponível no terminal. O programa baixa a versão fixa se ela
ainda não existir, confere a impressão digital e então faz a inspeção. Se o
original já estiver presente e correto, ele é reutilizado sem alteração.

Depois da primeira execução, não é necessária internet para inspecionar:

```sh
python -m checagens.inspecao
python -m pytest -q
```

| Local | O que você encontra |
| --- | --- |
| `data/originais/factpolcheckbr/com_texto.csv` | Cópia original, sem limpeza |
| `data/originais/factpolcheckbr/origem.json` | Fonte, versão, data de obtenção, tamanho, licença e identificação |
| `data/relatorios/inspecao-factpolcheckbr.json` | Contagens e números dos registros com problemas |
| `src/checagens/inspecao.py` | Programa que permite repetir a conferência |

O relatório numera os **registros a partir de 1, sem o cabeçalho**. Isso é
diferente do número de linha mostrado por um editor, pois os textos têm quebras
de linha. O programa interrompe com mensagem clara se o arquivo mudou, se o
cabeçalho é inesperado ou se a quantidade de campos está incorreta.

## 6. O que isso significa para a tarefa 1.1

| Critério | Situação nesta etapa |
| --- | --- |
| Conferir quantidade com a fonte | Atendido: 1.882 registros |
| Conferir preenchimento de data e agência | Atendido quanto à ausência de vazios; formatos de data ainda precisam de tratamento |
| Ter alegação e verificação utilizáveis | Pendente: título não é alegação original e há quatro textos vazios |
| Ter veredito disponível | Pendente em 50 registros |
| Consolidar em formato pronto para análise | Pendente: nenhuma conversão ou correção nesta etapa |

Portanto, **a tarefa 1.1 continua aberta**. A API permanece usando os três
exemplos fictícios. Os testes do protótipo não comprovam a qualidade deste corpus.

## 7. Aprendizado e pequeno exercício

Você deve conseguir explicar estas três ideias:

1. Conferir a quantidade é necessário, mas não garante qualidade.
2. Preservar o original permite conferir o que mudou e repetir o trabalho.
3. Uma data preenchida pode estar ambígua; um título pode conter uma correção,
   e não o boato que queremos buscar.

**Exercício:** abra uma cópia do CSV em um visualizador de planilhas, sem salvar
alterações no original. Localize o primeiro registro e identifique título,
texto, veredito, data, agência e link. Observe `8/2/2022`: quais são as duas
leituras possíveis? O título parece apenas repetir a alegação ou já corrigi-la?
Se a planilha converter datas automaticamente, consulte o texto original no editor.

Para estudar, sem precisar terminar um curso inteiro:

- [Python 3 — Mundo 1, Curso em Vídeo](https://www.cursoemvideo.com/curso/python-3-mundo-1/): primeiras aulas e primeiros comandos. Objetivo: reconhecer como executamos um programa.
- [Fluxo de trabalho com dados — Do zero à prática, Escola de Dados](https://escoladedados.org/wp-content/uploads/2021/03/livrov2.pdf): partes de obtenção e limpeza. Objetivo: relacionar fonte, inspeção e preparação.

## 8. Diário e próximo passo

**22/09/2026 — Etapa 1:** cópia original preservada, proveniência registrada,
inspeção reproduzível implementada e diagnóstico documentado. Testes específicos
usam dados fictícios para conferir registros multilinha, campos vazios,
repetições, datas mistas e erros estruturais. OpenSpec atualizado diretamente;
seu CLI continua indisponível neste ambiente.

Verificação: **48 testes passaram** (41 do protótipo e 7 da inspeção), com os
dois avisos já conhecidos das dependências de testes. A repetição da inspeção
real preservou a identificação do original; os testes também conferem que
um arquivo alterado não é sobrescrito. Links locais e exclusão dos dados
baixados do Git foram conferidos.

**Próxima etapa, após sua leitura:** organizar os dados preservando os valores
originais e sinalizando lacunas. O formato de datas e o uso do título como
representação da alegação precisam de decisões explícitas antes da conversão.
O alinhamento das faixas de confiança do Eixo 3 fica para a etapa 4.

## Resumo final

**Temos os 1.882 registros e sabemos de onde vieram. Encontramos campos vazios,
datas ambíguas, nomes de agência diferentes da descrição e possíveis duplicações.
Nada foi corrigido ou excluído. Você deve aprender a distinguir “arquivo baixado”
de “dados prontos para análise”. Vamos parar aqui antes de organizar a base.**
