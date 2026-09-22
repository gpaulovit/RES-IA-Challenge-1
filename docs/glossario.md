# Glossário em linguagem simples

| Termo | Significado neste projeto |
| --- | --- |
| Alegação | Uma afirmação que alguém quer comparar com checagens existentes. |
| Checagem | Texto que examina uma alegação; nesta demonstração, é inventado. |
| Veredito | Conclusão da checagem de origem. Não é automaticamente a conclusão sobre a consulta. |
| API | Porta de entrada do programa para receber pedidos e devolver respostas. |
| HTTP | Forma de comunicação usada para chamar a API. |
| Endpoint | Endereço de uma função da API, como `/buscar`. |
| GET / POST | Tipos de pedido HTTP: aqui, GET consulta a saúde e POST envia texto para busca. |
| JSON | Formato de texto com campos e valores, como `{"texto":"transporte"}`. |
| Feature | Funcionalidade: algo que o programa permite fazer. |
| Harness | Conjunto de ferramentas, exemplos e testes para conferir o funcionamento. |
| Teste automatizado | Verificação que o computador repete e compara com o resultado esperado. |
| Corpus | Conjunto de textos usados no estudo ou na busca. |
| Modelo | Método que transforma dados ou produz resultados; o modelo semântico futuro ainda será escolhido. |
| Vetor | Lista de números usada para representar um texto. |
| Embedding | Representação numérica de um texto; modelos semânticos tentam aproximar textos de significado parecido. |
| TF-IDF | Método que atribui peso às palavras conforme sua presença nos documentos. |
| Similaridade por cosseno | Cálculo para comparar a direção de dois vetores; aqui mede a proximidade dos textos representados. |
| Busca lexical | Comparação baseada nas palavras presentes nos textos, usada neste protótipo. |
| Busca semântica | Busca por significado, mesmo quando as palavras mudam; ainda é uma etapa futura. |
| top-k / `top_k` | Quantidade máxima de candidatos a apresentar. |
| Pipeline | Sequência de etapas: receber, transformar, comparar e responder. |
| Gate / go/no-go | Decisão, com base em evidências, de continuar ou rever a proposta. |
| OpenSpec / spec | Organização dos documentos que descrevem o que construir e como conferir a entrega. |
| Issue / PR | Registro de trabalho ou problema / proposta de alteração no repositório. |
| Ambiente virtual | Pasta que mantém as dependências Python deste projeto separadas das demais. |

## Resumo

**O programa recebe uma alegação pela API, transforma palavras em números e
busca exemplos parecidos. Os testes conferem esse caminho; o OpenSpec registra o combinado.**
