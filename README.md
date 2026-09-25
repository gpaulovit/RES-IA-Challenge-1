# RES-IA-Challenge-1

Recuperação semântica de checagens de boatos políticos reciclados.

📄 Página do projeto: [gpaulovit.github.io/RES-IA-Challenge-1](https://gpaulovit.github.io/RES-IA-Challenge-1/)

## O que já dá para experimentar

Um protótipo local recebe um texto e procura exemplos parecidos em **três
checagens inteiramente fictícias**. A comparação usa palavras em comum e seus
pesos (TF-IDF). Serve para mostrar as partes conectadas; ainda não reconhece
significados diferentes com segurança e não verifica a verdade de uma notícia.

## Como executar

Pré-requisito: Python 3.11 ou superior. Confira com `python3 --version`.
Abra um terminal **na pasta deste repositório**, onde está este README.
Os comandos abaixo são para macOS/Linux; no Windows use `py -3` para criar
o ambiente e `.venv\Scripts\Activate.ps1` para ativá-lo no PowerShell.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m uvicorn checagens.api:app --host 127.0.0.1 --port 8000
```

O ambiente `.venv` mantém as ferramentas deste projeto separadas das demais.
A instalação precisa de internet; depois, a busca funciona localmente, sem
conta ou chave de acesso. Deixe esse terminal aberto. Para parar, use `Ctrl+C`.

Abra <http://127.0.0.1:8000/docs> para experimentar a API no navegador:
expanda **POST /buscar**, clique em **Try it out**, preencha o texto e clique em
**Execute**. Essa página interativa carrega recursos externos e pode precisar
de internet; as chamadas pelo terminal abaixo funcionam sem esses recursos.
O endereço `http://127.0.0.1:8000/health` informa se o programa está pronto.

## Fazer uma consulta

Em outro terminal, com o servidor ligado:

```sh
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/buscar \
  -H 'Content-Type: application/json' \
  -d '{"texto":"transporte gratuito domingos","top_k":3}'
```

`top_k` significa **quantidade máxima de resultados**. É opcional (padrão 3)
e aceita números inteiros de 1 a 10. A consulta acima retorna `demo-002`.
A resposta contém:

| Campo | Como interpretar |
| --- | --- |
| `modo` | `demonstracao`: todos os exemplos são fictícios. |
| `metodo` | `tfidf_cosseno`: comparação por palavras e seus pesos. |
| `status` | `candidatos_encontrados` ou `nao_encontrada`. |
| `aviso` | Lembra que semelhança não significa verdade. |
| `candidatos` | Exemplos encontrados, do mais parecido ao menos parecido. |

Cada candidato traz `id`, `alegacao`, `checagem`, `agencia`,
`veredito_original` e `pontuacao`. A pontuação vai de 0 a 1; somente valores
maiores que zero aparecem. Ela **não é uma probabilidade de verdade**.
O veredito pertence ao exemplo fictício, não à frase enviada.

Para mostrar uma busca sem resultado:

```sh
curl -X POST http://127.0.0.1:8000/buscar \
  -H 'Content-Type: application/json' \
  -d '{"texto":"abacaxi telescópio submarino"}'
```

Resultado esperado: `status: nao_encontrada` e `candidatos: []`. Isso significa
que a consulta não compartilhou palavras reconhecidas com os exemplos; não
significa que a alegação é verdadeira, falsa ou inédita.

## Conferir o funcionamento

Na raiz do repositório, com o ambiente ativado, execute:

```sh
python -m pytest -q
```

O servidor não precisa estar ligado para os testes. A indicação `passed`
significa que as verificações passaram. Consulte o [guia de testes](docs/testes.md)
para entender o que foi conferido e o que ainda depende de dados reais.

## Entender e apresentar

- [Semana 1 — passo a passo](docs/semana-1-engenharia.md): inspeção da base real, descobertas e exercício para aprender.
- [Semana 2 — pipeline de embeddings](docs/semana-2-engenharia.md): vetores, metadados, amostra e recuperação.
- [Semana 3 — retrieval k-NN](docs/semana-3-engenharia.md): busca exata, exemplos e dependências ainda abertas.
- [Guia da arquiteta](docs/guia-arquiteta.md): papel, dependências, pipeline e roteiro das semanas 1 a 3.
- [Organização da Engenharia](docs/engenharia.md): peças, ferramentas e ciclo semanal.
- [Funcionalidades](docs/funcionalidades.md): o que está pronto e o que falta.
- [Testes e exemplos (harness)](docs/testes.md): como conferir o funcionamento.
- [Roteiro de apresentação](docs/apresentacao.md): demonstração em cinco minutos.
- [Glossário](docs/glossario.md): termos técnicos explicados em linguagem simples.

## Se algo não funcionar

| Situação | O que fazer |
| --- | --- |
| `No module named ...` | Ative `.venv` e execute novamente o comando de instalação. |
| Não foi possível ler os exemplos | Inicie o servidor na raiz do repositório e confira `data/exemplos.json`. |
| Arquivo ou registro inválido | A mensagem indica o problema; confira os cinco campos e os ids únicos. |
| HTTP 422 na consulta | Confira a mensagem em `detail`: texto não vazio e `top_k` inteiro de 1 a 10. |
| Porta 8000 ocupada | Pare o outro servidor ou use `--port 8001` e troque a porta nos endereços. |

## Estrutura

- [src/checagens/](src/checagens/) — código da API e da busca.
- [data/](data/) — exemplos fictícios usados na demonstração.
- [tests/](tests/) — verificações automáticas.
- [docs/](docs/) — conteúdo publicado via GitHub Pages (docsify).
- [openspec/](openspec/) — propostas e specs geridas pelo [OpenSpec](https://openspec.dev).
- [refs/](refs/) — material de referência (PDFs, papers).

## Resumo

**Já é possível enviar um texto para uma API local e receber checagens fictícias
parecidas. Os guias explicam como executar, testar e apresentar. A base real,
a busca por significado e as regras de confiança continuam como próximos passos.**
