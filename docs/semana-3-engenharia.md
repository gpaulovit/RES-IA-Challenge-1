# Semana 3 — Engenharia, passo a passo

O objetivo planejado para esta semana é ter o buscador real funcionando de
ponta a ponta. Algumas entradas obrigatórias ainda não foram entregues. Por
isso, esta etapa separa o que Engenharia conseguiu concluir do que continua
bloqueado pelas outras frentes.

## 1. Diagnóstico antes de começar

Em 24/09/2026, verificamos as issues relacionadas:

| Issue | Área | Situação que afeta Engenharia |
| --- | --- | --- |
| #8 | Modelos de IA | Gate sem decisão e nenhum modelo selecionado. |
| #11 | Domínio e Dados | QA dos dados indexados ainda não iniciado. |
| #13 | Modelos de IA | Acurácia do modelo integrado ainda não avaliada. |
| #15 | Produto e Decisão | Cenários executáveis ainda não detalhados. |

Sem essas entradas, não podemos declarar que existe uma primeira versão real do
produto. Podemos implementar e conferir a busca exata usando a amostra e o
baseline técnico da Semana 2.

## 2. O que foi implementado

O retrieval k-NN exato:

1. lê o manifesto, os vetores e os metadados;
2. confere os hashes antes de buscar;
3. impede consultar com um modelo diferente do usado no índice;
4. gera o vetor da consulta;
5. compara a consulta com **todos** os registros;
6. ordena pela similaridade e usa o id para desempatar;
7. devolve os `k` candidatos com texto, veredito, agência e data.

“Exato” significa que todos os vetores são comparados. Para 1.882 registros,
isso é simples e suficiente.

## 3. Conferir primeiro com a amostra

Gere o índice fictício:

```powershell
python -m checagens.embeddings --corpus data/amostras/corpus-organizado-exemplo.json --saida data/indices/amostra --modelo baseline-hashing
```

Faça uma consulta idêntica a um registro:

```powershell
python -m checagens.retrieval --indice data/indices/amostra --modelo baseline-hashing --texto "Vídeo antigo não mostra o evento desta semana" --top-k 3
```

O primeiro candidato deve ser `exemplo:0002`. Outras consultas documentadas
estão em `data/amostras/consultas-retrieval-exemplo.json`.

## 4. Conferir tecnicamente com o corpus completo

Se o índice experimental da Semana 2 já foi gerado:

```powershell
python -m checagens.retrieval --indice data/indices/experimental --modelo baseline-hashing --texto "COLE AQUI UM TÍTULO DO CORPUS" --top-k 5
```

Um título idêntico deve recuperar seu próprio registro na primeira posição.
Isso comprova a ligação índice → busca → metadados. Não comprova paráfrase,
recorrência histórica ou qualidade semântica.

## 5. Como repetir ou recuperar

Se uma busca futura produzir resultado diferente:

1. guarde a pasta do índice com problema;
2. confira no manifesto o modelo e os hashes;
3. execute novamente a amostra fictícia;
4. confirme que o modelo da consulta é igual ao modelo do índice;
5. recrie o índice em outra pasta, sem sobrescrever a anterior;
6. compare os manifestos e os primeiros resultados;
7. registre modelo, versão, comando, consulta e ids retornados.

Não altere o corpus para “consertar” uma busca. Primeiro descubra se o problema
está no modelo, no índice, na consulta ou no dado de origem.

## 6. Situação da checklist da issue #14

| Item | Situação | Evidência ou bloqueio |
| --- | --- | --- |
| Indexar com o modelo selecionado | Bloqueado | A issue #8 ainda não selecionou modelo nem registrou `go`. |
| Implementar retrieval k-NN exato | Concluído | Código, testes, amostra e execução local. |
| Passar os dois cenários do spec | Bloqueado | Reescrita histórica depende do gate, modelo, ids do benchmark e cenários da #15. |

Somente a segunda caixa pode ser marcada agora.

### Evidência da execução

Em 24/09/2026:

- a suíte completa terminou com **74 testes passando**;
- a consulta idêntica da amostra retornou `exemplo:0002` na primeira posição;
- uma consulta com o primeiro título do corpus real retornou o mesmo registro na
  primeira posição, com pontuação `1.0` e cinco candidatos;
- arquivos alterados, modelo incompatível e metadados desalinhados foram
  rejeitados pelos testes.

Essa evidência permite marcar apenas “Implementar o retrieval k-NN exato”.

## 7. Pendências por área

### Modelos de IA — issues #8 e #13

- registrar `go/no-go`;
- informar modelo, identificador e versão;
- gerar o índice com o modelo escolhido;
- calcular Recall@5 geral e para recorrência temporal;
- comparar o resultado integrado com o resultado do gate.

### Domínio e Dados — issue #11

- conferir uma amostra de vetor → metadados → registro original;
- confirmar se algum registro ficou fora;
- validar o campo usado como alegação e as datas pendentes.

### Produto e Decisão — issue #15

- transformar os cenários do spec em consultas com resultado esperado;
- indicar os ids corretos do corpus para cada caso;
- executar os cenários e registrar falhas.

### Engenharia — issue #14

- integrar o modelo após a decisão `go`;
- repetir a indexação com o modelo escolhido;
- executar os cenários entregues por Produto;
- corrigir problemas de integração encontrados pelas outras áreas.

## 8. Quando a Semana 3 estará concluída

A Semana 3 somente poderá ser declarada concluída quando:

- houver decisão `go` registrada;
- o índice usar o modelo oficialmente selecionado;
- Dados aprovar o alinhamento dos registros;
- Produto entregar os cenários executáveis;
- o registro indexado for recuperado;
- a reescrita histórica aparecer no top-k dentro da meta definida.

## Resumo

A busca k-NN exata está implementada e pode ser repetida com uma amostra
fictícia. A construção do produto real continua bloqueada pelo gate, pelo modelo
selecionado, pelo QA de Dados e pelos cenários de Produto. Essas dependências
precisam ser resolvidas antes de marcar as outras duas caixas da issue #14.
