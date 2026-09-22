# Organização da Engenharia

A Engenharia conecta as entregas do grupo para que o programa funcione do começo
ao fim. Hoje, essa conexão usa três exemplos fictícios e uma comparação simples.

## Caminho de uma consulta

```text
Texto enviado --> API --> Transformação em números --> Busca --> Resposta
                                  ^                     ^
                                  |                     |
                       Vocabulário dos exemplos     Base preparada
```

Ao iniciar, o programa lê os exemplos e prepara seus números uma única vez.
Quando chega uma consulta, usa o mesmo vocabulário e compara com todos os exemplos.
Nenhum arquivo é alterado pela consulta e nenhum texto é enviado a serviços externos.

## Onde cada coisa fica

| Local | Responsabilidade |
| --- | --- |
| `src/checagens/dados.py` | Ler o JSON e conferir campos, textos e identificadores. |
| `src/checagens/representacao.py` | Transformar palavras em números usando TF-IDF. |
| `src/checagens/busca.py` | Comparar os números e ordenar os resultados. |
| `src/checagens/api.py` | Receber consultas e devolver respostas e erros em português. |
| `data/exemplos.json` | Guardar os três exemplos inteiramente fictícios. |
| `tests/` | Conferir automaticamente se o comportamento esperado continua funcionando. |
| `openspec/` | Registrar requisitos, decisões e tarefas antes de alterar o programa. |

## Ferramentas e escolhas

| Ferramenta | Para que serve aqui |
| --- | --- |
| Python | Linguagem em que o programa foi escrito. |
| FastAPI | Define os endereços que recebem consultas e gera a página interativa. |
| Uvicorn | Mantém o servidor local ligado para atender às consultas. |
| scikit-learn | Calcula TF-IDF e semelhança por cosseno. |
| Pydantic | Confere os campos recebidos e os dados dos exemplos. |
| pytest e HTTPX | Executam testes, incluindo chamadas à API sem abrir um servidor externo. |

TF-IDF dá peso às palavras conforme sua presença nos exemplos. O cosseno compara
os conjuntos de números produzidos. Palavras comuns como “de” também podem gerar
semelhança: esta versão não decide se duas frases dizem a mesma coisa. Negação,
sinônimos, gírias e afirmações misturadas ainda exigem trabalho futuro.

## Como receber novas entregas

Cada exemplo contém cinco textos obrigatórios: `id`, `alegacao`, `checagem`,
`agencia` e `veredito_original`. Os ids não podem se repetir. Mudanças nos
exemplos exigem reiniciar o servidor para preparar novamente a busca.

A parte que representa textos oferece três pontos de ligação: `metodo`
(nome da técnica), `preparar(textos)` (prepara a base) e `transformar(textos)`
(prepara consultas). Os dois últimos devolvem matrizes numéricas compatíveis
com a comparação por cosseno. Um teste mostra a troca dessa parte sem mudar a API.

Esse formato é um ponto de partida para integração. A base real pode precisar
de campos adicionais, como data e origem; isso será alinhado com a frente de dados
no OpenSpec antes da integração. Não basta colocar dados reais no arquivo de
exemplos: a autorização atual cobre apenas a demonstração fictícia.

## Ciclo semanal

1. Consultar as issues e PRs do repositório por frente e identificar entregas disponíveis.
2. Combinar o que entra e o que sai de cada parte: dados com Domínio de dados,
   técnica de comparação com Modelos de IA e comportamento com Produto e decisão.
3. Conferir se a mudança cabe na proposta; atualizar os documentos se necessário.
4. Conectar a entrega e executar os testes e as consultas de demonstração.
5. Registrar resultado, limitações e dependências em issue ou PR com `papel: engenharia`.
6. Atualizar guias e preparar uma demonstração do que realmente está funcionando.

Modelo curto para esse registro:

```text
Entrega da semana:
Frente de origem e link:
O que mudou para quem usa:
Como executar ou demonstrar:
O que foi testado e resultado:
O que falta e de quem depende:
Documento OpenSpec relacionado:
```

## Próximos passos

A demonstração é uma exceção limitada à etapa de validação, chamada de *gate*.
As seções 1–4 da proposta continuam pendentes: validar recorrência nos dados reais,
escolher o modelo e definir regras de confiança. O protótipo não prova essas hipóteses.

## Resumo

**A Engenharia liga dados, comparação, busca e API. Cada peça tem uma função
separada, testes e documentação para facilitar a integração das entregas do grupo.**
