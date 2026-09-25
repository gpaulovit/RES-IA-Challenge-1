# Semana 2 — Engenharia, passo a passo

O objetivo desta semana é deixar pronto o caminho que transforma os registros
organizados em vetores e mantém cada vetor ligado ao seu registro de origem.

## 1. Situação atual

A infraestrutura da issue #9 foi implementada. A frente de Modelos de IA ainda
não registrou na issue #8 quais modelos serão comparados. Por isso, usamos um
modelo lexical pequeno somente para conferir o funcionamento do pipeline.

Esse teste técnico não escolhe o modelo final, não conclui o gate e não mede a
qualidade da busca semântica.

## 2. Fluxo desta entrega

```text
Corpus organizado
       ↓
Escolha do gerador de vetores
       ↓
Vetores + metadados na mesma ordem
       ↓
Manifesto com modelo, formato e hashes
```

Cada linha do arquivo de vetores corresponde à mesma posição no arquivo de
metadados. O campo `linha_vetor` permite conferir essa ligação.

## 3. Testar primeiro com a amostra

A amostra contém três registros fictícios e pode ser mantida no Git. Ela ajuda
a conferir o processo mesmo quando a base real não está disponível.

```sh
python -m checagens.embeddings \
  --corpus data/amostras/corpus-organizado-exemplo.json \
  --saida data/indices/amostra \
  --modelo baseline-hashing
```

No Windows PowerShell, execute em uma linha:

```powershell
python -m checagens.embeddings --corpus data/amostras/corpus-organizado-exemplo.json --saida data/indices/amostra --modelo baseline-hashing
```

Resultado esperado: três vetores com 256 dimensões.

## 4. Executar sobre o corpus organizado

Depois de gerar o corpus da Semana 1:

```sh
python -m checagens.embeddings --modelo baseline-hashing
```

O comando cria arquivos locais em `data/indices/experimental/`:

| Arquivo | Para que serve |
| --- | --- |
| `vetores.npy` | Matriz numérica com um vetor por registro. |
| `metadados.json` | Liga cada linha ao texto, veredito, agência e data. |
| `manifesto.json` | Registra modelo, dimensões, fonte, aviso e hashes dos arquivos. |

Os arquivos ficam fora do Git porque podem ser reproduzidos. O manifesto
permite perceber se um arquivo foi trocado ou alterado.

## 5. Usar um modelo candidato

Modelos compatíveis com `sentence-transformers` são opcionais. Instale-os em um
ambiente virtual separado:

```sh
python -m pip install -e '.[embeddings]'
python -m checagens.embeddings --modelo sentence-transformers:NOME_DO_MODELO --saida data/indices/NOME_CURTO
```

Substitua `NOME_DO_MODELO` pelo identificador entregue pela frente de Modelos de
IA. Use uma pasta diferente para cada candidato. Assim, um teste não sobrescreve
o resultado do outro.

Um BERTimbau sem adaptação não segue necessariamente essa interface. A frente de
Modelos precisa informar o identificador, a forma de gerar o vetor e a versão
exata usada na comparação.

## 6. Como voltar ou repetir o processo

Se algo der errado no futuro:

1. preserve o corpus organizado e o manifesto que apresentou problema;
2. anote o nome do modelo e o comando utilizado;
3. apague somente a pasta específica dentro de `data/indices/`;
4. execute primeiro a amostra fictícia;
5. compare os hashes do novo manifesto com os anteriores;
6. execute novamente o corpus real em uma pasta nova.

O corpus original e o corpus organizado não devem ser alterados para corrigir
um problema do modelo. A indexação é uma etapa posterior e reproduzível.

## 7. Pendências e responsáveis

| Pendência | Área responsável | Impacto |
| --- | --- | --- |
| Informar modelos candidatos, identificadores e versões | `papel: modelos-ia`, issue #8 | Impede validar o pipeline com os candidatos reais. |
| Registrar a decisão `go/no-go` | `papel: modelos-ia`, issue #8 | Impede avançar para a indexação real da Semana 3. |
| Confirmar se o título representa a alegação | `papel: dominio-dados` | O título continua marcado como uso experimental. |
| Relacionar os casos da issue #10 aos ids do corpus | Modelos de IA e Produto | Impede calcular métricas confiáveis por caso. |

## 8. Critério para concluir a issue #9

A parte de Engenharia fica pronta quando:

- o pipeline gera vetores e metadados alinhados;
- uma execução repetida com a mesma entrada e o mesmo modelo produz os mesmos arquivos;
- a amostra fictícia funciona em outro ambiente;
- pelo menos um modelo candidato da issue #8 é executado e registrado.

Os três primeiros itens podem ser concluídos pela Engenharia. O último depende
da entrega da frente de Modelos de IA.

## 9. Registro da execução

Em 24/09/2026, a amostra gerou **3 vetores de 256 dimensões** e o corpus
organizado gerou **1.882 vetores de 256 dimensões** com o
`baseline-hashing-256`. Uma segunda execução produziu os mesmos hashes para
vetores, metadados e manifesto. A suíte completa terminou com **66 testes
passando** e um aviso já conhecido de dependência de testes.

Esse resultado comprova o caminho técnico e a rastreabilidade. Ele não mede
qualidade semântica. A validação final da issue #9 depende de a issue #8
entregar pelo menos um modelo candidato com nome, versão e forma de execução.

## Resumo

O caminho técnico para gerar e guardar embeddings está pronto. Existe uma
amostra pequena para recuperação e um manifesto para conferir os arquivos. A
validação com modelos reais continua pendente porque a issue #8 ainda não
informou quais modelos e versões serão usados.
