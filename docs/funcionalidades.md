# Funcionalidades

Uma funcionalidade (*feature*) é algo que o programa permite fazer.
“Verificada” abaixo significa coberta por testes automáticos do protótipo,
não validada como solução para checagens reais.

| Funcionalidade | Para que serve | Exemplo | Situação |
| --- | --- | --- | --- |
| Conferir se está pronto | Saber se a base foi carregada e o servidor iniciou | `GET /health` | Implementada e coberta por teste |
| Procurar exemplos parecidos | Encontrar palavras compartilhadas com a consulta | “transporte gratuito domingos” retorna `demo-002` | Implementada e coberta por teste |
| Limitar os resultados | Escolher quantos candidatos deseja ver | `top_k: 1` retorna no máximo um | Implementada e coberta por teste |
| Mostrar a origem | Ler alegação, checagem, agência e veredito do exemplo | Campos dentro de `candidatos` | Implementada e coberta por teste |
| Informar ausência de resultado | Mostrar que não houve palavras reconhecidas em comum | “abacaxi telescópio submarino” | Implementada e coberta por teste |
| Explicar erros de entrada | Ajudar a corrigir consultas inválidas | Texto vazio recebe HTTP 422 | Implementada e coberta por teste |
| Trocar a representação | Permitir integrar outra técnica de comparação | Teste com vetores controlados | Implementada e coberta por teste |
| Buscar por significado em dados reais | Reconhecer reescritas do mesmo boato | Sinônimos e gírias | Planejada, depende de validação e escolha do modelo |
| Mostrar faixas de confiança | Diferenciar candidatos prováveis e confirmados | Limites definidos por avaliação real | Planejada |
| Tratar partes não checadas e divergências | Evitar conclusões indevidas | Agências com vereditos diferentes | Planejada |

## Como interpretar o resultado

`candidatos_encontrados` significa que existem exemplos com semelhança lexical
maior que zero. `nao_encontrada` significa lista vazia nesta base demonstrativa.
Nenhum desses estados classifica a verdade da consulta.

Os candidatos vêm do maior para o menor valor de `pontuacao`; empates usam o
`id` em ordem crescente. Há no máximo três resultados porque a base tem três
registros, mesmo que a pessoa peça dez.

O programa não oferece tela própria, histórico, banco de dados ou acesso público
à API. O site do projeto contém documentação; não executa o servidor Python.

## Resumo

**O protótipo recebe consultas, busca exemplos fictícios, mostra suas fontes e
explica erros. Reconhecimento de significado e confiança ficam para as próximas etapas.**
