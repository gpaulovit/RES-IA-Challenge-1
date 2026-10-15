# Glossário

Termos que aparecem nos documentos do projeto, explicados de forma simples. Para quem é de outra área, a ideia é esta: o bot compara a mensagem que você recebeu com checagens que já foram feitas por sites de checagem, e diz o quanto elas se parecem.

## Termos do bot

| Termo | O que significa |
| --- | --- |
| **Bot** | Programa que responde no Telegram. Aqui, o `@checaai_bot`. |
| **Checagem** | Uma notícia que um site de checagem já analisou, com o resultado (veredito). |
| **Agência / site de checagem** | Quem fez a checagem, por exemplo Aos Fatos, Lupa, Comprova ou Boatos.org. |
| **Veredito** | O resultado dado pela agência, por exemplo "Falso" ou "Verdadeiro". |
| **Alegação** | A afirmação que foi checada, resumida em uma frase. |
| **Semelhança** | Um número entre 0 e 1 que mostra o quanto a sua mensagem se parece com uma checagem. Não é a chance de a notícia ser falsa. |
| **Limiar** | O valor de semelhança que separa uma faixa da outra. Por exemplo, acima de 0,85 a notícia é "já conferida". Os valores atuais são provisórios até a calibração ser aprovada por Produto e Modelos. |
| **Faixa** | O grupo em que a resposta cai, de acordo com a semelhança: já conferida, parecida ou sem correspondência. |
| **Já conferida** | A notícia é praticamente a mesma de uma checagem existente. |
| **Relacionada** | Parecida com uma checagem, mas pode não ser exatamente a mesma coisa. |
| **Sem correspondência** | Nenhuma checagem parecida foi encontrada. Isso não quer dizer que a notícia é verdadeira. |
| **Sinais de fake news** | Sinais no texto que costumam aparecer em fake news, como "URGENTE", "compartilhe" ou muitos "!!!". |
| **Camada 1 (busca)** | Parte do bot que procura checagens parecidas com a mensagem. |
| **Camada 2 (alerta)** | Parte do bot que olha só o texto e procura sinais de fake news. Fica desligada até Produto aprovar. |
| **Modo de teste** | Um jeito de ver as respostas do bot com resultados inventados, sem depender da busca real. |
| **Registro anônimo** | Guarda só dados como data, tipo da mensagem e resultado. Não guarda nome, usuário nem número. |

## Termos de projeto

| Termo | O que significa |
| --- | --- |
| **Repositório** | A pasta do projeto guardada no GitHub, com todos os arquivos e o histórico. |
| **Commit** | Uma "foto" salva do trabalho, com uma mensagem explicando o que mudou. |
| **Branch** | Uma linha de trabalho separada. Cada pessoa trabalha na sua, sem mexer na versão principal. |
| **Main** | A versão principal do projeto, que todo mundo usa. Não se trabalha direto nela. |
| **Pull request (PR)** | Um pedido para juntar a sua branch na `main`. O grupo revisa antes de aceitar. |
| **Issue** | Um cartão de tarefa no GitHub, com a descrição do que precisa ser feito. |
| **Teste automatizado** | Um programa que confere se o código faz o que deveria, sempre que ele muda. |
| **CI (integração contínua)** | Robô que roda os testes automaticamente quando alguém sobe mudanças. |
| **Arquivo `.env`** | Arquivo com configurações secretas, como o token do bot. Nunca vai para o GitHub. |
| **Token** | Uma senha que deixa o programa conversar com o Telegram. |
| **Regex** | Uma forma de procurar padrões em um texto, por exemplo "tudo que começa com https://". |
| **RF / RN / RNF** | Requisito funcional (algo que o sistema faz), regra de negócio (regra que ele segue) e requisito não funcional (qualidade, como privacidade e velocidade). Estão em [Requisitos](requisitos.md). |
| **Benchmark** | Um conjunto de perguntas com respostas conhecidas, usado para medir se o sistema acerta. |
| **Recall@5** | Medida de quantas vezes a resposta certa aparece entre os 5 primeiros resultados. |
| **Dataset** | Uma base de dados organizada para análise ou treino. |
