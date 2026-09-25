# Testes e exemplos: como conferir o funcionamento

O *harness* é o conjunto de exemplos, ferramentas e testes usado para conferir
o programa de forma repetível. Aqui, ele reúne os três registros fictícios,
os testes em `tests/` e o comando abaixo.

## Como executar

Depois de seguir a instalação no [README do repositório](https://github.com/gpaulovit/RES-IA-Challenge-1#como-executar),
abra o terminal na raiz do projeto:

```sh
source .venv/bin/activate
python -m pytest -q
```

No Windows, ative com `.venv\Scripts\Activate.ps1`. Não é preciso ligar Uvicorn:
os testes usam uma versão da API dentro do próprio processo de teste.

Os testes de organização também conferem a preservação dos sete campos
originais, datas e lacunas explícitas, duplicações, integridade da fonte e
repetibilidade dos arquivos gerados.

Os testes do pipeline de embeddings conferem a ligação entre vetor e metadados,
rejeitam saídas inválidas de modelos, verificam os hashes dos artefatos e usam
um modelo falso pequeno para não depender de downloads durante a suíte.

Os testes do retrieval conferem a busca exata, o primeiro resultado de uma
consulta idêntica, desempate por id, modelo compatível e rejeição de arquivos
alterados. Esses testes técnicos não medem a acurácia de um modelo semântico.

## O que é conferido

| Verificação | Resultado esperado |
| --- | --- |
| Texto idêntico ao exemplo | O exemplo correto aparece primeiro, com pontuação próxima de 1. |
| Consulta relacionada | “transporte gratuito domingos” encontra `demo-002`. |
| Sem vocabulário conhecido | Lista vazia, inclusive para uma consulta só com pontuação. |
| Quantidade e ordem | Respeita o limite; organiza por pontuação e depois id. |
| Dados de origem | A resposta preserva a alegação, checagem, agência e veredito original. |
| Entrada inválida | Texto vazio, quantidade inválida e JSON malformado recebem HTTP 422. |
| Arquivo inválido | Falta de arquivo, lista vazia, campos inválidos e ids repetidos impedem iniciar. |
| Troca de técnica | Outra representação de textos funciona sem mudar a API. |
| Caminho completo | Uma chamada HTTP passa pela comparação real TF-IDF e retorna candidatos. |

`passed` significa que os testes passaram. `failed` significa que alguma
expectativa não foi atendida: leia o nome do teste e os valores esperado e
recebido. `error` costuma indicar que o teste nem conseguiu iniciar; confira
instalação e mensagem de erro. Não altere a expectativa apenas para fazer passar:
confira o comportamento combinado na proposta.

## Conferência manual

Com o servidor ligado, execute as duas consultas do README ou do
[roteiro de apresentação](apresentacao.md). Confira também `/health` e `/docs`.
Os testes verificam a entrega técnica; a apresentação permite avaliar se as
explicações fazem sentido para o grupo.

## Limites e registro

Passar nesses testes não prova reconhecimento de paráfrases, precisão em dados
reais, acerto de vereditos nem recorrência temporal. Essas avaliações estão nas
tarefas futuras do OpenSpec.

Ao entregar uma mudança, registre o comando executado, o resultado, a versão
de Python (`python --version`) e eventuais limitações. Isso permite à próxima
pessoa repetir a conferência. Os intervalos de dependências em `pyproject.toml`
não congelam todas as versões; registre-as com `python -m pip freeze` se precisar
comparar dois ambientes.

## Registro da primeira verificação

Em 22/09/2026, a instalação em ambiente virtual novo foi conferida com Python
3.14.6. O comando `python -m pytest -q` passou nos **41 testes** e
`python -m pip check` não encontrou incompatibilidades de dependências.
As três chamadas do README também foram executadas contra o servidor local:
saúde, consulta com `demo-002` e consulta com lista vazia.

O ambiente testado usou FastAPI 0.141.1, scikit-learn 1.9.1, Pydantic 2.13.5,
Uvicorn 0.53.0, pytest 9.1.1 e HTTPX 0.28.1. Surgiram dois avisos de futura
mudança em dependências de testes (Starlette/HTTPX e AnyIO); não impediram
a execução. Python 3.11–3.13 e Windows não foram executados nesta verificação.

Os links locais dos guias foram conferidos. Os documentos OpenSpec foram
revisados diretamente; a validação pelo comando OpenSpec não foi executada
porque essa ferramenta não estava instalada no ambiente.

## Resumo

**Um único comando confere a busca e a API automaticamente. Os testes protegem
o funcionamento da demonstração; a qualidade da busca real ainda será avaliada.**
