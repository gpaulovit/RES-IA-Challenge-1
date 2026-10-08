# Dados do bot

> Responsável: Cibelly Lourenço (`papel: dominio-dados`). Issue
> [#35](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/35).

O bot usa duas bases. A **base de checagens** alimenta a busca da camada 1 (RF-06, RF-07). A
**base de treino** alimenta o classificador da camada 2 (RF-08, RN-04). As duas são geradas por
código em [`src/checagens/bases/`](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/src/checagens/bases)
a partir dos datasets públicos, com a versão fixada por commit e conferida por sha256.

| Arquivo | Uso | Linhas | Período |
| --- | --- | ---: | --- |
| `data/processados/checagens/checagens.json` | busca (camada 1) | 10.442 | 02/07/2013 a 01/12/2022 |
| `data/processados/checagens/amostra_teste_30.json` | teste manual da busca | 30 | 29/11 a 01/12/2022 |
| `data/processados/treino/treino.csv` | treino do classificador | 9.934 | 2009 a 15/09/2018 |
| `data/processados/treino/teste.csv` | teste do classificador | 3.295 | 16/09 a 28/10/2018 |
| `data/processados/treino/teste_curtos.csv` | teste extra, textos curtos | 297 | 2010 a 2019 |

Os números desta página vêm de dois relatórios gerados junto com as bases e versionados no git:
[`data/relatorios/checagens.json`](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/data/relatorios/checagens.json)
(gerado por `checagens.py`) e [`data/relatorios/treino.json`](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/data/relatorios/treino.json)
(`treino.py`).

## Como regenerar

O DVC do repositório ainda não tem remote: os arquivos versionados não podem ser baixados com
`dvc pull`. Para gerar tudo do zero (baixa cerca de 130 MB):

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[test]' 'dvc>=3,<4'
source .venv/bin/activate
dvc repro            # baixar → checagens → treino (stages em dvc.yaml)
```

Sem DVC, os mesmos passos são:

```sh
python -m checagens.bases.baixar          # data/brutos/, confere o sha256 de cada arquivo
python -m checagens.bases.checagens       # base de checagens + amostra + relatório
python -m checagens.bases.treino --corte 2018-09-15
```

Os scripts são idempotentes: rodar duas vezes gera arquivos idênticos byte a byte. A única
aleatoriedade é a ordem das linhas dos CSVs, embaralhadas com semente fixa (`SEMENTE = 42`, em
`treino.py`). As regras são testadas em `tests/test_bases.py`, sem precisar dos dados.

## Base de checagens (camada 1)

### Campos

| Campo | Conteúdo |
| --- | --- |
| `id` | `<base>-<linha no arquivo de origem>`, ex. `factpolcheckbr-0195` |
| `alegacao` | título da checagem sem carimbo, prefixo de veredito ("É falso que") nem nome do site |
| `veredito_original` | rótulo exatamente como a agência publicou (RN-01, RN-02) |
| `veredito_normalizado` | `falso`, `enganoso`, `verdadeiro` ou `outro` (RN-02) |
| `agencia` | nome legível da agência |
| `data` | data da checagem, `AAAA-MM-DD` |
| `link` | link da checagem, como veio da fonte |
| `fonte_dataset` | `FactPolCheckBr`, `FACTCK.BR`, `FactChecks.br/Central de Fatos` ou `FactChecks.br/FakeRecogna` |

O arquivo é uma lista JSON, ordenada da checagem mais recente para a mais antiga. O contrato é
conferido em código por `validar()` em `checagens.py`: todos os campos preenchidos, data válida,
veredito normalizado entre os quatro valores e nenhuma duplicata de id, link ou alegação.

### O que entra de cada fonte

Contagens em `lidos_por_fonte`, `descartes_por_fonte_e_motivo`, `validos_por_fonte`,
`duplicatas_removidas` e `final.por_fonte` de `data/relatorios/checagens.json`.

| Fonte | Lidos | Descartados | Válidos | Removidos como duplicata | Na base |
| --- | ---: | ---: | ---: | ---: | ---: |
| [FactPolCheckBr](https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr) | 1.882 | 55 | 1.827 | 23 | 1.804 |
| [FACTCK.BR](https://github.com/jghm-f/FACTCK.BR) | 1.313 | 424 | 889 | 4 | 885 |
| [FactChecks.br](https://github.com/fake-news-UFG/FactChecks.br) / Central de Fatos | 10.461 | 3.179 | 7.282 | 247 | 7.035 |
| FactChecks.br / FakeRecogna | 11.773 | 8.577 | 3.196 | 2.478 | 718 |
| **Total** | 25.429 | 12.235 | 13.194 | 2.752 | **10.442** |

Do FactChecks.br entram só o Central de Fatos e o FakeRecogna. As outras partes (Fake.br,
Fact-check_tweet e FakeNewsSet) não são checagens com alegação em texto. No FakeRecogna, só entram
os registros com `is_fake = 1`: os demais são notícias de jornal, não checagens.

### Por que um registro sai

Cada registro conta uma vez, no primeiro motivo em que cai (`descartes_por_fonte_e_motivo` no
relatório).

| Motivo | FactPolCheckBr | FACTCK.BR | Central de Fatos | FakeRecogna |
| --- | ---: | ---: | ---: | ---: |
| sem link válido (exigido por RF-07) | 1 | — | — | — |
| sem data válida (exigido por RF-07) | — | — | — | 346 |
| sem veredito na fonte | 50 | 4 | — | — |
| sem carimbo da agência no título (ver abaixo) | — | — | 3.177 | 2.272 |
| carimbo contradiz o `is_fake` da base | — | — | — | 8 |
| `is_fake` diferente de 1 (notícia, não checagem) | — | — | — | 5.951 |
| checagem de várias alegações ("Veja o que é #FATO ou #FAKE…") | 4 | 87 | 2 | — |
| várias alegações no mesmo link, cada uma com seu rótulo | — | 333 | — | — |

- **FactPolCheckBr:** os 50 sem veredito são, na maioria, checagens de várias alegações (debates,
  entrevistas) ou textos explicativos ("Entenda…"). Não representam um boato único.
- **FACTCK.BR:** 91 links aparecem em 420 linhas, uma por alegação do mesmo artigo. Em 61 deles, as
  alegações têm rótulos diferentes, como Falso, Verdadeiro e Exagerado
  (`factckbr_links_com_varias_alegacoes` no relatório). Como a alegação usada é o
  título e o link precisa ser único, não há como dizer a qual alegação o rótulo se refere. Por isso
  nenhuma delas entra.
- **Datas inválidas do FakeRecogna:** misturam formatos e têm erros como `5/04/20195`.

### Veredito original e veredito normalizado

O bot mostra o `veredito_original` ao usuário e nunca o troca pelo normalizado (RN-01). Por isso,
só vale como `veredito_original` o que a própria agência escreveu:

- **FactPolCheckBr:** coluna "Natureza da notícia". É o rótulo que a base consolidou a partir da
  checagem: Falsa, Verdadeira ou Parcialmente verdadeira.
- **FACTCK.BR:** coluna `alternativeName`, o rótulo publicado pela agência na marcação ClaimReview.
- **FactChecks.br:** a base só tem o `is_fake` binário, que **nunca** vira rótulo de agência.
  Entra apenas o registro cujo título tem um carimbo explícito da agência:
  - `#boato` e `Boato:`, do Boatos.org;
  - `É #FAKE` e `É #FATO`, do Fato ou Fake;
  - "É falso", "É enganoso", "É verdadeiro" e afins no início do título;
  - "Falso:" e "Enganoso:" como prefixo.

  O carimbo vira o `veredito_original` exatamente como está escrito. Ficam de fora:
  - frases com verbo ("Post engana ao…");
  - descrições ("É montagem", "É antiga");
  - títulos em forma de pergunta;
  - títulos com carimbos de sentido oposto.

  As regras estão em `CARIMBOS`, em `vereditos.py`.

Quantos registros do FactChecks.br têm carimbo, por agência, antes dos outros filtros
(`factchecksbr_carimbo_por_agencia` no relatório):

| Base | Agência | Registros | Com carimbo | Sem carimbo |
| --- | --- | ---: | ---: | ---: |
| Central de Fatos | Boatos.org | 5.468 | 5.044 | 424 |
| Central de Fatos | Agência Lupa | 1.824 | 911 | 913 |
| Central de Fatos | Aos Fatos | 1.430 | 350 | 1.080 |
| Central de Fatos | Fato ou Fake | 785 | 782 | 3 |
| Central de Fatos | Estadão Verifica | 593 | 112 | 481 |
| Central de Fatos | Projeto Comprova | 361 | 85 | 276 |
| FakeRecogna (`is_fake = 1`) | Boatos.org | 2.425 | 2.420 | 5 |
| FakeRecogna | Fato ou Fake | 1.125 | 947 | 178 |
| FakeRecogna | E-farsas | 804 | 0 | 804 |
| FakeRecogna | Projeto Comprova | 669 | 140 | 529 |
| FakeRecogna | AFP Checamos | 503 | 12 | 491 |
| FakeRecogna | UOL Confere | 275 | 30 | 245 |
| FakeRecogna | UOL | 18 | 1 | 17 |
| FakeRecogna | G1 | 3 | 0 | 3 |

Aos Fatos, Estadão Verifica, Comprova e AFP raramente põem o rótulo no título. Por isso perdem a
maior parte dos registros. No FakeRecogna, os títulos do E-farsas vêm lematizados ("condenar morrer
o o enganar") e não serviriam como alegação de qualquer forma.

**Mapeamento original → normalizado** (`TAXONOMIA`, em `vereditos.py`; contagens em
`mapeamento_vereditos` no relatório). O que não está na tabela vira `outro`.

| Normalizado | Rótulos originais (registros na base) |
| --- | --- |
| `falso` | Falsa (1.792), Falso/falso (756), #boato/#Boato (5.358), É falso/É falsa (1.253), É #FAKE (1.060), Boato (21), FALSO/Falso (4) |
| `enganoso` | Parcialmente verdadeira (3), Distorcido/distorcido (35), Exagerado/exagerado (27), Sem contexto (10), Impreciso (2), Subestimado (1), É enganoso/É enganosa (37) |
| `verdadeiro` | Verdadeira (9), Verdadeiro/verdadeiro (33), "Verdadeiro, mas" (0 após os filtros), É verdadeiro/É verdadeira/É verdade (16), É #FATO (4) |
| `outro` | Discutível (8), Impossível provar (7), Insustentável (4), De olho (1), outros (1), Ainda é cedo para dizer (0 após os filtros) |

Resultado: 10.244 `falso`, 115 `enganoso`, 62 `verdadeiro` e 21 `outro`. A base serve para a
busca, não para treinar o classificador: ela tem 98% de `falso`.

Proporção de vereditos por fonte (`por_fonte_e_veredito` no relatório):

| Fonte | falso | enganoso | verdadeiro | outro | % falso |
| --- | ---: | ---: | ---: | ---: | ---: |
| FactPolCheckBr | 1.792 | 3 | 9 | 0 | 99,3% |
| FACTCK.BR | 756 | 75 | 33 | 21 | 85,4% |
| Central de Fatos | 6.994 | 21 | 20 | 0 | 99,4% |
| FakeRecogna | 702 | 16 | 0 | 0 | 97,8% |
| **Total** | 10.244 | 115 | 62 | 21 | 98,1% |

O FACTCK.BR é a única fonte com variedade de vereditos, porque traz o rótulo da agência em
coluna própria.

### Nome da agência

O FactChecks.br só informa o domínio (`uol.com.br`, `globo.com`…). O nome sai do link, por host e
caminho, na tabela `AGENCIAS_POR_HOST` de `vereditos.py`:

- `piaui.folha.uol.com.br/lupa` vira Agência Lupa;
- `noticias.uol.com.br/confere` vira UOL Confere;
- `noticias.uol.com.br/comprova` vira Projeto Comprova;
- `g1.globo.com/fato-ou-fake` vira Fato ou Fake;
- `www.e-farsas.com` vira E-farsas, embora a base informe o domínio `r7.com`.

Quando o link não identifica a agência, vale o nome do site (`SITES_POR_DOMINIO`). Isso aconteceu
em 1 registro ("UOL", um vídeo do UOL). No FactPolCheckBr, o nome vem da coluna "Agência".

### Datas

- **FactPolCheckBr** publica as datas como M/D/AAAA. As ambíguas (os dois números ≤ 12 e
  diferentes entre si) são lidas como mês/dia: a análise de cobertura de 2022 achou 256
  confirmações pela data no link e nenhuma contra. Quando o primeiro número passa de 12, a data só
  é válida como dia/mês.
  - Contagens (`factpolcheckbr_regra_data`): 1.136 sem ambiguidade (inclui 80 com dia igual ao
    mês, como 9/9/2022), 738 ambíguas lidas como mês/dia e 8 lidas como dia/mês.
  - Regra em `ler_data_factpolcheckbr()`, em `texto.py`.
- **Demais fontes:** aceita AAAA-MM-DD, AAAA/MM/DD e DD/MM/AAAA. A data também precisa estar entre
  2000 e hoje.

### Duplicatas

O critério está em `deduplicar()`, em `checagens.py`, aplicado depois dos descartes:

1. **Link com vereditos conflitantes:** se o mesmo link normalizado aparece com vereditos
   normalizados diferentes em bases diferentes, saem todos os registros. Foram 8, em 4 links. Por
   exemplo, a Lupa titulou "É falso" e o FACTCK.BR marca "Verdadeiro".
2. **Mesmo link:** o link normalizado usa https, sem `www`, sem parâmetros de rastreio (`utm_*`,
   `fbclid`, `gclid`, `igshid`, `amp`), sem fragmento nem barra final, e com o caminho
   decodificado. Foram 2.689 removidos.
3. **Mesma alegação:** a alegação normalizada (NFKC, caixa, pontuação e espaços) também derruba
   duplicatas. Foram 55 removidos.

Quando há duplicata, fica o registro da fonte com o rótulo mais rico: FACTCK.BR, depois
FactPolCheckBr, Central de Fatos e FakeRecogna. A maior sobreposição é entre FakeRecogna e Central
de Fatos: 2.467 registros do FakeRecogna saem porque o Central de Fatos já os tem
(`por_par_removida_mantida` no relatório).

### Tamanho e período

Contagens em `final.por_fonte`, `final.periodo_por_fonte`, `final.por_ano` e `final.por_agencia`
de `data/relatorios/checagens.json`.

| Fonte | Na base | Período |
| --- | ---: | --- |
| Central de Fatos | 7.035 | 02/07/2013 a 19/05/2021 |
| FactPolCheckBr | 1.804 | 01/08/2022 a 01/12/2022 |
| FACTCK.BR | 885 | 15/06/2016 a 22/07/2019 |
| FakeRecogna | 718 | 13/11/2018 a 03/09/2021 |

Por ano: 2013: 49 · 2014: 100 · 2015: 66 · 2016: 593 · 2017: 800 · 2018: 1.604 · 2019: 1.848 ·
2020: 2.514 · 2021: 1.064 · 2022: 1.804. **Não há checagens de 2023 em diante**, nem da campanha de
2026.

Por agência: Boatos.org 5.693 · Agência Lupa 1.352 · Fato ou Fake 1.214 · Aos Fatos 967 ·
Projeto Comprova 309 · UOL Confere 250 · AFP Checamos 198 · Fato ou Boato (Justiça Eleitoral) 171 ·
Agência Pública 135 · Estadão Verifica 101 · E-farsas 48 · Folha de S. Paulo 2 · CNJ 1 · UOL 1.

### Cobertura de 2022

As checagens de 2022 são todas do FactPolCheckBr e cobrem só a campanha presidencial, de 01/08 a
01/12/2022 (`cobertura_2022` no relatório).

| Mês (2022) | Checagens |
| --- | ---: |
| Agosto | 245 |
| Setembro | 368 |
| Outubro | 726 |
| Novembro | 444 |
| Dezembro (só o dia 1º) | 21 |

Por agência: Boatos.org 314 · Aos Fatos 302 · Agência Lupa 239 · UOL Confere 221 · AFP
Checamos 187 · Fato ou Boato 171 · Projeto Comprova 169 · Fato ou Fake 150 · E-farsas 48 ·
Folha 2 · CNJ 1. A campanha de 2022 é dominada por boatos sobre urnas e sistema eleitoral, e os
vereditos são quase todos `falso` (1.792 de 1.804).

### Amostra de 30 checagens recentes

`amostra_teste_30.json` tem os mesmos campos da base. Ela reúne as 30 checagens mais recentes, com
no máximo 4 por agência (`amostra_recente()` em `checagens.py`), para a equipe testar a busca à
mão. Vai de 29/11 a 01/12/2022 e cobre 9 agências:

- 4 cada: AFP Checamos, Agência Lupa, Aos Fatos, Boatos.org, Fato ou Boato e Projeto Comprova;
- 3: E-farsas;
- 2: Fato ou Fake;
- 1: UOL Confere.

## Base de treino (camada 2)

### Campos

`treino.csv`, `teste.csv` e `teste_curtos.csv` têm as colunas:

- `texto`: texto sem carimbos de rótulo e com espaços normalizados;
- `rotulo`: `falso` ou `verdadeiro`;
- `fonte`: `Fake.br-Corpus`, `FakeWhatsApp.Br` ou `FakeTweet.Br`;
- `data`: `AAAA-MM-DD`, vazia quando a fonte não traz.

### Fontes

- [**Fake.br-Corpus**](https://github.com/roneysco/Fake.br-Corpus), versão `size_normalized_texts`:
  - 3.600 notícias falsas e 3.600 verdadeiras, em pares cortados para o mesmo número de palavras;
  - data de publicação lida dos metadados de `full_texts`;
  - falsas e verdadeiras vêm de sites diferentes;
  - 7 textos ficam sem data: os textos 697 e 1468 de cada classe não têm metadados no
    repositório, e outros 3 têm data ilegível.
- [**FakeWhatsApp.Br**](https://github.com/cabrau/FakeWhatsApp.Br), arquivo
  `fakeWhatsApp.BR_2018.csv`:
  - 282.601 mensagens de grupos públicos;
  - 21.289 mensagens têm rótulo (`misinformation` 0 ou 1), todas de texto, de 02/07 a
    28/10/2018;
  - entram só texto, rótulo e data; identificador de usuário, DDD e estado ficam de fora (RN-03).
- [**FakeTweet.Br**](https://github.com/prc992/FakeTweet.Br): 299 tweets de 2010 a 2019, nos arquivos
  `FakeTweetBr.csv` e `FakeTweetBr-Test.csv`.

### Divisão treino e teste (RN-04)

Tamanho, período e proporção de classes de cada arquivo e de cada base dentro dele (`arquivos`
em `data/relatorios/treino.json`):

| Arquivo | Base | Linhas | falso | verdadeiro | % falso | Período |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `treino.csv` | Fake.br-Corpus | 7.199 | 3.600 | 3.599 | 50,0% | 01/06/2009 a 23/07/2018 (7 sem data) |
| `treino.csv` | FakeWhatsApp.Br | 2.735 | 1.162 | 1.573 | 42,5% | 02/07 a 15/09/2018 |
| `treino.csv` | **total** | 9.934 | 4.762 | 5.172 | 47,9% | |
| `teste.csv` | FakeWhatsApp.Br | 3.295 | 1.628 | 1.667 | 49,4% | 16/09 a 28/10/2018 |
| `teste_curtos.csv` | FakeTweet.Br | 297 | 199 | 98 | 67,0% | 31/10/2010 a 18/05/2019 |

Somando treino e teste, o FakeWhatsApp.Br entra com 6.030 mensagens: 2.790 falsas (46,3%) e
3.240 verdadeiras.

**Por que essa divisão:**
- O teste se parece com o que o bot vai receber: mensagens de grupo encaminhadas.
- O modelo já vê um pouco de WhatsApp no treino.
- O teste é **posterior** ao treino, inclusive o 1º turno de 2018.
- A data de corte é o argumento `--corte` de `treino.py`, definido no stage `treino` do `dvc.yaml`.

**Atenção:** o teste é do **mesmo canal** e de **época próxima** (as semanas logo depois do corte).
A métrica nele tende a ser otimista em relação a mensagens de 2026.

**Verificações feitas em código** (`verificar()` em `treino.py`; resultado em `verificacoes` no
relatório):
- nenhum texto normalizado se repete dentro de um arquivo nem entre treino, teste e teste_curtos;
- todo o WhatsApp do treino é de até o corte, e todo o teste é de depois dele;
- nenhum carimbo sobrou;
- todo texto tem pelo menos 5 palavras (RF-11).

**Deduplicação** (antes do corte, pelo texto normalizado sem acento, caixa, pontuação e espaços;
`descartes` e `quase_duplicatas_removidas_do_teste` no relatório):
- 14.972 repetições removidas, ficando a ocorrência mais antiga;
- 9 linhas com o mesmo texto e rótulos opostos saem todas;
- 279 mensagens do teste com cosseno TF-IDF ≥ 0,9 com algum texto do treino também saem, porque
  são a mesma corrente com pequenas edições (`quase_duplicatas()`).

### Carimbos removidos

`CARIMBOS`, em `treino.py`, remove de **todos** os textos, de qualquer classe, o que entrega o
rótulo (`carimbos_removidos` e `carimbos_removidos_teste_curtos` no relatório):

| Carimbo | Exemplo | Fake.br falso / verd. | WhatsApp falso / verd. | FakeTweet falso / verd. |
| --- | --- | ---: | ---: | ---: |
| "é fake/falso/boato/mentira" (com ou sem #, com "que") | "isso é Fake News" | 20 / 3 | 128 / 49 | 1 / 23 |
| palavra em maiúsculas | "FALSO", "MENTIRA", "FAKE NEWS" | 13 / 0 | 74 / 14 | 0 / 6 |
| hashtag de rótulo | `#boato`, `#FatoouFake`, `#verificamos` | 0 / 0 | 5 / 6 | 1 / 10 |
| link de agência de checagem | `https://www.boatos.org/politica/…` | 0 / 0 | 7 / 11 | 1 / 22 |
| trecho de link com rótulo | `…/e-fake-que-…`, `…/e-falsa-pesquisa-…` | 0 / 0 | 11 / 14 | 1 / 15 |

Exemplos (antes → depois; mais em `exemplos_carimbos` no relatório):

- WhatsApp, verdadeiro: "Urnas eletrônicas estão programadas para o horário de verão #boato
  https://www.boatos.org/politica/urnas-eletronicas-horario-verao.html" → "Urnas eletrônicas estão
  programadas para o horário de verão"
- WhatsApp, falso: "📣📢FALSO ATENTADO PODE ESTAR EM CURSO!!!" → "📣📢 ATENTADO PODE ESTAR EM CURSO!!!"
- FakeTweet, verdadeiro: "É #FAKE que Lula aparece na lista de mais ricos do mundo da revista
  Forbes . #FatoouFake" → "Lula aparece na lista de mais ricos do mundo da revista Forbes"

**Efeito colateral:** a remoção também apaga usos legítimos dessas expressões. Por exemplo, "Vamos
provar que é mentira" vira "Vamos provar que". Preferimos isso a deixar o rótulo no texto.

### Outros vazamentos encontrados

A busca exploratória (`VAZAMENTOS`, em `treino.py`; `vazamentos_exploratorios_treino_e_teste` no
relatório) conta, sem remover, a porcentagem de textos de
treino e teste com cada padrão, depois da remoção dos carimbos:

| Padrão | Fake.br falso | Fake.br verdadeiro | WhatsApp falso | WhatsApp verdadeiro |
| --- | ---: | ---: | ---: | ---: |
| "fake", "falso", "boato", "mentira" em minúsculas, no meio da frase | 3,4% | 2,4% | 7,8% | 3,2% |
| "G1", "O Globo" | 4,1% | 10,1% | 1,6% | 1,0% |
| "leia mais", "leia também", "veja também" | 6,7% | 1,4% | 0,0% | 0,2% |
| nome de agência de checagem | 1,9% | 1,8% | 2,4% | 1,1% |
| "verificamos", "checamos", "checagem" | 0,1% | 0,1% | 0,0% | 0,0% |
| "Folha de S.Paulo", "Folhapress" | 0,9% | 0,4% | 0,0% | 0,2% |
| "Estadão Conteúdo", "Agência Estado" | 0,1% | 0,0% | 0,0% | 0,0% |
| "compartilhe", "repasse", "divulgue" | 4,5% | 3,4% | 22,9% | 11,3% |
| "urgente" | 1,9% | 0,3% | 4,6% | 1,2% |

"Compartilhe" e "urgente" são sinais de estilo que o bot pode mostrar (RF-08), não vazamento.
"G1/O Globo" e "leia também", ao contrário, indicam o veículo do Fake.br, não o conteúdo.

## Licenças

| Dataset | Licença | Onde consta |
| --- | --- | --- |
| FactPolCheckBr | CC BY-NC-SA 4.0 | `LICENSE.md` do repositório |
| FACTCK.BR | MIT | `LICENSE` do repositório |
| FactChecks.br | MIT | `LICENSE` do repositório (vale para o repositório) |
| Central de Fatos e FakeRecogna (partes do FactChecks.br) | a confirmar | — |
| Fake.br-Corpus | a confirmar | o repositório não tem arquivo de licença; o README pede citação |
| FakeWhatsApp.Br | GPL-3.0 | `LICENSE` do repositório |
| FakeTweet.Br | a confirmar | o repositório não tem arquivo de licença |

A CC BY-NC-SA 4.0 do FactPolCheckBr pede atribuição, uso não comercial e o mesmo licenciamento para
derivados. A `checagens.json` contém registros dele.

## Limitações

- **Sem checagens recentes.** A base de checagens termina em 01/12/2022. Boatos de 2026 só são
  encontrados se repetirem narrativas antigas.
- **Quase tudo é `falso`** (98%). Uma correspondência na busca quase sempre devolve "falso".
- **Alegação nem sempre é o boato.** Muitos títulos já trazem a correção ("Lula não disse que…",
  "Marcola citado por Lula não é o do PCC" com veredito FALSO). Nesses casos, a alegação mostrada
  descreve o desmentido, não o boato.
- **Agências sub-representadas.** Aos Fatos, Estadão Verifica, Comprova e AFP raramente põem o
  rótulo no título, e a regra de carimbo deixa de fora a maior parte dos registros delas no
  FactChecks.br.
- **Veredito do FactPolCheckBr** é a consolidação feita pela base (Falsa, Verdadeira,
  Parcialmente verdadeira), não o rótulo literal de cada agência.
- **Base de treino pode ensinar o veículo.** No Fake.br, falsas e verdadeiras vêm de sites
  diferentes, e marcas de jornal aparecem mais numa classe que na outra ("G1/O Globo" em 10,1% das
  verdadeiras e 4,1% das falsas; "leia também" em 6,7% das falsas e 1,4% das verdadeiras). Um
  classificador pode aprender o estilo do site em vez do conteúdo.
- **Teste otimista.** O teste é do mesmo canal e de semanas próximas ao treino, e tudo é de 2018.
- **FakeTweet.Br desbalanceado e com cara de agência.** Os tweets "verdadeiros" são, em boa parte,
  publicações das próprias agências. Mesmo sem os carimbos, ficam marcas como "via Aos Fatos".

## Pendências

- O DVC não tem remote: o grupo precisa definir onde guardar os arquivos. Até lá, regenerar com
  `dvc repro`.
- Licenças a confirmar: Fake.br-Corpus, FakeTweet.Br, Central de Fatos e FakeRecogna.
