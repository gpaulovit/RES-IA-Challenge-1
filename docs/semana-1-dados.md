# Semana 1 — Domínio de dados: cobertura e vereditos

**A base tem volume para um MVP, mas cobre só uma eleição (ago–dez/2022) e é
quase toda de alegações falsas. Ela permite testar reciclagem dentro da
campanha de 2022, não entre ciclos eleitorais.**

Issue: [#1 — exploração do corpus e taxonomia de vereditos](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/1).
Responsável: Cibelly Lourenço (`papel: dominio-dados`).

## 1. De onde vêm os números

Todos os números abaixo vêm do corpus organizado pela Engenharia
([Semana 1 — Engenharia](semana-1-engenharia.md)), versão
`e4b4feafce9b83789a517f649abb39ad4645f1b3` do FactPolCheckBr (1.882
registros). Para repetir:

```sh
source .venv/bin/activate
python -m checagens.inspecao --baixar
python -m checagens.organizacao
python -m checagens.cobertura
```

O último comando lê `data/processados/factpolcheckbr/corpus.json`, não altera
nenhum registro e grava `data/relatorios/cobertura-factpolcheckbr.json`
(local, fora do Git). O código está em `src/checagens/cobertura.py`.

## 2. Volume por agência

| Agência | Registros |
| --- | ---: |
| Boatos.org | 315 |
| Aos Fatos | 314 |
| Agência Lupa | 245 |
| UOL Confere | 228 |
| AFP Checamos | 196 |
| Fato ou Boato (Justiça Eleitoral) | 184 |
| Projeto Comprova | 175 |
| Fato ou Fake | 172 |
| E-farsas | 50 |
| Folha de S. Paulo | 2 |
| CNJ | 1 |

Nove agências têm volume relevante (50 a 315). Folha e CNJ somam 3 registros
e não mudam a análise.

## 3. Cobertura temporal

| Mês (2022) | Registros |
| --- | ---: |
| Agosto | 264 |
| Setembro | 393 |
| Outubro | 753 |
| Novembro | 451 |
| Dezembro (só dia 1º) | 21 |

**Todas as checagens estão entre 01/08/2022 e 01/12/2022.** As semanas com
mais registros são as do 1º turno (2/10) e do 2º turno (30/10): 201 e 194
checagens, contra 50 a 77 nas semanas de agosto.

### As 738 datas ambíguas devem ser lidas como mês/dia/ano

A tabela acima já usa essa leitura. A evidência:

- As 1.136 datas sem ambiguidade estão todas entre agosto e dezembro de 2022.
- Lidas como mês/dia, as ambíguas também caem nesse período. Lidas como
  dia/mês, se espalhariam de janeiro a dezembro, fora do período da coleta.
- 262 das ambíguas têm a data dentro do link da checagem. **256 confirmam
  mês/dia e nenhuma confirma dia/mês.** Seis não batem com nenhuma das
  leituras (registros 1207, 1208, 1209, 1304, 1667, 1726) e diferem em cerca
  de um dia ou um mês: provável erro de digitação na fonte.
- As 8 datas fora do formato (registros 1609–1616) só são válidas como
  dia/mês: 30 e 31/10/2022.

**Decisão proposta para a Engenharia:** padronizar as ambíguas como mês/dia e
as 8 fora do formato como dia/mês, marcando a regra aplicada no registro.
Manter as 6 divergentes marcadas como pendentes.

## 4. Vereditos e taxonomia

O FactPolCheckBr **já publica os vereditos consolidados** em quatro valores.
Os rótulos próprios de cada agência ("Enganoso", "#FAKE", "Distorcido"...)
não existem como coluna.

| Rótulo na fonte | Taxonomia do projeto | Registros |
| --- | --- | ---: |
| Falsa | `falso` | 1.820 |
| Verdadeira | `verdadeiro` | 9 |
| Parcialmente verdadeira | `parcialmente_verdadeiro` | 3 |
| (vazio) | `sem_veredito` | 50 |

A taxonomia está em `TAXONOMIA`, em `src/checagens/cobertura.py`. Um rótulo
novo interrompe o relatório em vez de passar sem mapeamento.

**Conferência por amostragem:** conferi os 62 registros que não são `falso`,
ou seja, todos eles e não uma amostra. Os 12 verdadeiros ou parciais batem com
o título (ex.: "É #FATO que voto servirá como prova de vida junto ao INSS").
Os 50 sem veredito são, na maioria, **checagens com várias alegações**
(debates, entrevistas, "Veja o que é #FATO ou #FAKE…") ou textos explicativos
("Entenda…", "Saiba o que é…"). Não há um único boato para indexar nesses
registros.

**O rótulo original da agência só aparece no título.** "É falso que…",
"#boato" (Boatos.org) e "É #FAKE que…" (Fato ou Fake) aparecem com frequência,
mas 843 títulos não têm marcador algum. Por isso, recuperar "enganoso" ou
"distorcido" exigiria ler o texto da checagem. Isso fica como lacuna
registrada.

### Consequências para Produto e Modelos de IA

- **Divergência entre agências (Eixo 3):** só uma leitura do título ou do
  texto pode mostrar "Falso" x "Enganoso". Na coluna de veredito, praticamente
  toda alegação é `falso`, então divergência é rara por construção.
- **Faixas de confiança:** com 97% de `falso`, uma correspondência quase sempre
  devolve "falso". O teste de falsos positivos com notícias verdadeiras fora
  da base, proposto no Eixo 3, fica ainda mais importante.
- **Indexação:** os 50 registros `sem_veredito` não devem entrar no índice
  como alegação única. O notebook de clusters de Modelos de IA (branch `feat/testsmodelo`) já filtra
  checagens com várias alegações.

## 5. Cobertura temática (exploratória)

Contei palavras-chave nos títulos. É uma heurística: um título pode ter mais
de um tema, e a clusterização por embeddings (tarefa 1.2) é quem responde de
verdade.

| Tema | Títulos |
| --- | ---: |
| Urnas e sistema eleitoral | 603 |
| Mídia e pesquisas | 163 |
| Forças Armadas e instituições | 152 |
| Segurança e crime | 142 |
| Economia e benefícios (Pix, auxílio) | 88 |
| Religião | 79 |
| Saúde | 41 |
| Costumes | 31 |
| Meio ambiente | 12 |
| Nenhuma palavra-chave | 764 |

Urnas e sistema eleitoral dominam. O campo "Candidato(s) favorecido(s)" é
concentrado: 1.547 favorecem Jair Bolsonaro, 156 Lula e 178 estão indefinidos.
O índice representa bem a desinformação da campanha presidencial de 2022, não
"o universo de boatos políticos brasileiros".

## 6. Primeiros sinais de reciclagem

Comparei os títulos entre si com TF-IDF (similaridade ≥ 0,6). É uma medida por
palavras e, por isso, subestima paráfrases.

- **243 registros (13%)** têm pelo menos um título quase igual na base.
- **199** desses pares são de agências diferentes: o mesmo boato checado por
  várias agências, quase sempre na mesma semana.
- Só **9 pares** estão a 30 dias ou mais de distância.

Exemplo de reciclagem: "banqueiros apoiam Lula em troca da revogação do Pix"
foi checado por 6 agências entre 1º e 5/08 e voltou reescrito em 29/10 ("Lula
define taxa para transações no Pix após encontro com banqueiros").

A medida por palavras mostra que a repetição existe. A recorrência temporal
por significado é a tarefa 1.3, com embeddings.

## 7. Lacunas e decisões pendentes

| Lacuna | Impacto | Proposta | Quem decide |
| --- | --- | --- | --- |
| Base cobre só ago–dez/2022 | Não dá para medir boato que volta em outra eleição | Gate mede reciclagem **dentro** da campanha; avaliar suplemento de outros anos na #6 | Dados + Modelos de IA |
| 97% `falso`, 9 verdadeiros | Pouco contraste para calibrar faixas | Conjunto de controle com notícias verdadeiras fora da base (Eixo 3) | Produto + Modelos de IA |
| Rótulo original só no título | Divergência entre agências fica pouco visível | Extrair marcador do título numa etapa futura | Dados + Produto |
| Título muitas vezes já traz a correção ("X **não** fez…") | Consulta do usuário (boato) difere do texto indexado | Tratar na decisão sobre o texto da alegação (ADR-001 na branch de arquitetura) | Dados + Engenharia |
| 50 registros sem veredito | Não representam um boato único | Excluir do índice como alegação única | Dados (proposta) |
| 738 datas ambíguas | Análise temporal incorreta se lidas errado | Ler como mês/dia (seção 3) | Dados (proposta) |
| 6 datas divergentes do link | Erro pontual | Manter pendentes | Dados |

## Resumo

**Temos 1.882 checagens de 9 agências relevantes, concentradas na campanha de
2022 e em alegações falsas sobre o sistema eleitoral. A base sustenta um MVP
de busca para essa campanha e já mostra alegações repetidas entre agências.
Ela não sustenta, sozinha, a afirmação de representar os boatos políticos
brasileiros em geral nem de medir reciclagem entre eleições.**
