# Dados do bot

> Responsável: Cibelly Lourenço (`papel: dominio-dados`). Issue
> [#35](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/35).

| Arquivo | Uso | Linhas | Período |
| --- | --- | ---: | --- |
| `data/processados/checagens/checagens.json` | busca (camada 1) | 12.245 | 2013 a 2026 |
| `data/processados/treino/treino.csv` | treino do classificador (camada 2) | 9.934 | 2009 a 15/09/2018 |
| `data/processados/treino/teste.csv` | teste do classificador | 3.295 | 16/09 a 28/10/2018 |
| `data/processados/treino/teste_curtos.csv` | teste extra, textos curtos | 297 | 2010 a 2019 |

Para gerar as bases: `dvc repro checagens treino`. O código está em `src/checagens/bases/`, e as
contagens detalhadas, em `data/relatorios/`.

## Base de checagens (camada 1)

Une 5 fontes públicas: Central de Fatos (7.035), FactPolCheckBr (1.804), Google Fact Check Tools
(1.803), FACTCK.BR (885) e FakeRecogna (718). Só entra checagem com link, data e o veredito
publicado pela própria agência, e as duplicatas saem. As de 2025-26 são atualizadas por
`scripts/atualizar_checagens_factcheck.py`.

## Base de treino (camada 2)

Notícias do Fake.br-Corpus e mensagens do FakeWhatsApp.Br, rotuladas `falso` ou `verdadeiro`. O teste
é só de WhatsApp e posterior ao treino (RN-04). Os textos não se repetem entre arquivos, e os
carimbos que entregam o rótulo ("é fake", "#boato") são removidos.

## Análise exploratória

Notebook: [`experiments/07_eda.ipynb`](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/experiments/07_eda.ipynb).

![Checagens por mês e fonte](img/eda/checagens_por_mes.png)

- 94% das checagens são `falso`, e 46% são do Boatos.org.
- Não há checagens entre dez/2022 e set/2025.
- No WhatsApp, as mensagens falsas têm o dobro do tamanho das verdadeiras.
- No Fake.br, falsas e verdadeiras são de anos diferentes: o ano sozinho já separa as classes.

## Limitações

- A busca quase sempre devolve "falso", e boatos de 2023-24 podem não ser encontrados.
- O classificador aprende o tamanho, a época e o veículo do texto, não só a desinformação
  ([relatório](relatorio-camada2.md)).
- O teste é otimista: é do mesmo canal e de semanas próximas ao treino.
- Licenças a confirmar: Fake.br-Corpus, FakeTweet.Br, Central de Fatos, FakeRecogna e Google Fact
  Check. O FactPolCheckBr é CC BY-NC-SA 4.0 (uso não comercial).
