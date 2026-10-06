# Glossário em linguagem simples

| Termo | Significado neste projeto |
| --- | --- |
| Alegação | Uma afirmação que circula e pode ser checada. |
| Checagem | Texto de uma agência que examina uma alegação e dá um veredito. |
| Veredito | Conclusão da agência sobre a alegação checada. O projeto nunca dá veredito sobre uma notícia nova. |
| Narrativa | A história de fundo de vários boatos parecidos (ex.: "fraude na urna"), mesmo com alegações diferentes. |
| Corpus | Conjunto de textos usado no estudo. |
| Rótulo | Classe de cada exemplo usado no treino: falsa ou verdadeira. |
| Carimbo de agência | Marca como "É #FAKE" ou "#boato" que entrega o rótulo; é removida para o modelo não aprendê-la. |
| Vetor / embedding | Lista de números que representa o sentido de um texto. |
| TF-IDF | Representação pelas palavras do texto e seus pesos; é a linha de base léxica. |
| Similaridade por cosseno | Medida de proximidade entre dois vetores. |
| Regressão logística | Modelo simples que transforma os números do texto numa probabilidade. |
| Linha de base | Modelo simples que o modelo principal precisa superar para se justificar. |
| Controle de atalho | Modelo que só vê a fonte e o ano. Se ele acerta tanto quanto o modelo de texto, o modelo aprendeu o veículo, não a narrativa. |
| AUC | De 0,5 (acaso) a 1 (separação perfeita): o quanto o modelo põe as falsas acima das verdadeiras. |
| Calibração / ECE | Se o modelo diz 70%, cerca de 70% desses casos devem ser falsos; o ECE mede o erro dessa promessa. |
| Brier skill score | Quanto o modelo melhora sobre sempre prever a proporção de falsas do treino. |
| Holdout temporal | Treinar com um período e avaliar com um período posterior, nunca misturando os dois. |
| Gate / go/no-go | Decisão, com critério escrito antes de rodar, de continuar ou rever a proposta. |
| Pré-registro | Escrever (e commitar) os critérios antes de ver os resultados. |
| DVC | Ferramenta que versiona os dados grandes fora do git. |
| OpenSpec / spec | Organização dos documentos que descrevem o que construir e como conferir. |
| Issue / PR | Registro de trabalho / proposta de alteração no repositório. |
| Ambiente virtual | Pasta `.venv` que mantém as dependências deste projeto separadas das demais. |
