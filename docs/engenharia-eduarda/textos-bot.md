# Textos do bot

> Responsável: Ana Júlia (`papel: produto-decisao`). Atualizado em 08/10/2026.
> Para: Engenharia (Eduarda). Implementa RF-02, RF-04, RF-07 a RF-11, RN-01 e RNF-06.
> Mudanças de texto passam por Produto; mudanças de código, não.

Os textos estão prontos para colar. Use `parse_mode="HTML"` e `disable_web_page_preview=True`
(senão o Telegram abre uma prévia gigante do primeiro link). O que está entre chaves (`{agencia}`)
é preenchido pelo código; passe cada valor por `html.escape()` antes.

## Como uma resposta é montada

| Situação | Mensagem enviada |
| --- | --- |
| semelhança ≥ 0,85 | **Já checado** + **Aviso e links** |
| semelhança entre 0,60 e 0,85 | **Checagem relacionada** + a **faixa curta** + **Aviso e links** |
| semelhança < 0,60 | uma **faixa de alerta** + **Aviso e links** |
| semelhança < 0,60 e camada 2 em `no-go` (RN-04) | **Não encontrei checagem** + **Aviso e links** |
| link que não abre, mídia, texto curto, erro interno | só a **mensagem de erro**, sem aviso e links |

Tudo vai numa única mensagem, separado por uma linha em branco. Os botões 👍/👎 (RF-12) ficam
embaixo da mensagem de resultado, nunca embaixo das mensagens de erro.

**Regras de escrita (RN-01, RNF-06):**

- Linguagem para qualquer nível de leitura: frases curtas, palavras do dia a dia ("conferir",
  "site de checagem", "fake news"), sem termos técnicos ("alegação", "semelhança", "desinformação").
- Sem porcentagem ou número de pontuação.
- O bot pode dizer que uma mensagem **tem sinais de** fake news, nunca que ela **é** fake news,
  verdade ou mentira. "Falso" ou "verdadeiro" só aparecem como resultado de um site de checagem
  (`{veredito_original}`).
- Cada texto abaixo tem menos de 600 caracteres antes dos links.

## /start e /ajuda (RF-02)

`/start`

```html
Olá! Eu te ajudo a conferir se uma notícia pode ser fake news.
Cole aqui o link da notícia ou a mensagem que você recebeu.
```

`/ajuda`

```html
<b>Como usar:</b> cole o link ou a mensagem. Também pode encaminhar direto do grupo.
<b>Como eu confiro:</b> vejo se um site de checagem já conferiu essa notícia. Se não achar, vejo se o texto tem sinais de fake news.
<b>Importante:</b> eu não dou a palavra final. Quem confere os fatos são os sites de checagem.
<b>Não leio</b> áudio, foto, vídeo nem print. Só texto e link.
<b>Não guardo</b> seu nome, seu número nem seu usuário.
```

## Camada 1: checagem encontrada (RF-07)

**Já checado** (semelhança ≥ 0,85)

```html
🔎 <b>Essa notícia já foi conferida.</b>
O site {agencia} conferiu uma notícia igual a essa em {data}.
Notícia: “{alegacao}”
Resultado: <b>{veredito_original}</b>
Veja a explicação completa: {link}
```

**Checagem relacionada** (semelhança entre 0,60 e 0,85, ou quando a consulta e a checagem
divergem em negação)

```html
🔎 <b>Achei uma notícia parecida que já foi conferida.</b>
Atenção: pode não ser exatamente a mesma coisa que você recebeu.
Notícia: “{alegacao}”
Resultado do site {agencia}: <b>{veredito_original}</b>
Veja a explicação: {link}
```

- `{veredito_original}` é o rótulo como a agência publicou ("Falso", "Distorcido", "Verdadeiro").
  Não troque pelo rótulo normalizado: o rótulo é da agência, não nosso (RN-01).
- `{data}` no formato `dd/mm/aaaa`. Sem data na base, apague " em {data}".
- `{alegacao}` cortada em 160 caracteres, terminando com "…", para caber no limite de 600.

## Camada 2: faixas de alerta (RF-08)

`{trechos}` são 2 ou 3 palavras ou expressões do texto da pessoa que mais puxaram o
classificador para o lado de alerta (maior coeficiente × TF-IDF entre os termos presentes),
entre aspas e separadas por vírgula: `“urgente”, “compartilhe”, “a mídia esconde”`. Se não houver
nenhuma com peso positivo, apague a linha das palavras.

**Muitos sinais de alerta**

```html
⚠️ <b>Atenção: essa mensagem tem muitos sinais de fake news.</b>
Nenhum site de checagem conferiu essa notícia ainda, mas o jeito que ela foi escrita lembra outras fake news.
Palavras que chamaram atenção: {trechos}
Antes de repassar, veja se algum jornal conhecido deu a mesma notícia.
```

**Incerto**

```html
❔ <b>Não dá para saber só pelo texto.</b>
Nenhum site de checagem conferiu essa notícia ainda, e o jeito que ela foi escrita não ajuda a decidir.
Palavras que chamaram atenção: {trechos}
Na dúvida, não repasse antes de conferir.
```

**Poucos sinais de alerta**

```html
🟦 <b>Poucos sinais de fake news.</b>
Nenhum site de checagem conferiu essa notícia ainda, e o jeito que ela foi escrita não lembra fake news.
Mas isso não garante que ela seja verdade.
Se for repassar, veja se algum jornal conhecido deu a mesma notícia.
```

Na faixa "poucos sinais" não mostre palavras: elas fariam o alerta parecer maior do que é.

**Faixa curta** (só depois de uma checagem relacionada, para a mensagem caber em 600 caracteres)

```html
Sobre a sua mensagem: <b>{faixa}</b>
Palavras que chamaram atenção: {trechos}
```

`{faixa}` = `tem muitos sinais de fake news.`, `não dá para saber só pelo texto.` ou
`tem poucos sinais de fake news.` Na faixa "poucos sinais", apague a linha das palavras.

**Não encontrei checagem** (camada 2 desligada pelo RN-04)

```html
🔎 <b>Nenhum site de checagem conferiu essa notícia ainda.</b>
Isso não quer dizer que ela é verdade nem mentira. Pode ser um assunto novo.
Antes de repassar, veja se algum jornal conhecido deu a mesma notícia.
```

## Aviso e links (RF-09)

Vai no fim de toda mensagem de resultado (camada 1, faixas e "não encontrei").

```html
ℹ️ Sou um robô e posso errar. Quem confere os fatos são os sites de checagem.
<b>Confira você também:</b>
• Fato ou Boato, da Justiça Eleitoral: https://www.justicaeleitoral.jus.br/fato-ou-boato
• Aos Fatos: https://www.aosfatos.org
• Agência Lupa: https://www.agencialupa.org
• Comprova: https://projetocomprova.com.br
• Fato ou Fake, do g1: https://g1.globo.com/fato-ou-fake/
```

Links conferidos em 08/10/2026. A lista de agências parceiras está na página
[Fato ou Boato](https://www.justicaeleitoral.jus.br/fato-ou-boato) da Justiça Eleitoral.

## Mensagens de erro (RF-04, RF-10, RF-11)

**Link que não abre** (RF-04): página fora do ar, bloqueada, exige login ou não tem texto.

```html
Não consegui abrir esse link. 😕
Pode copiar e colar aqui o texto da notícia? Só o título e o começo já ajudam.
```

**Áudio, foto, vídeo, figurinha, documento ou localização** (RF-10)

```html
Por enquanto eu só leio texto e link. Não consigo ouvir áudio nem ver foto, vídeo ou print.
Se a mensagem tinha texto, cole aqui. Se for um vídeo da internet, mande o link.
```

Se a foto ou o vídeo vier com legenda, use a legenda como texto e siga o fluxo normal.

**Texto com menos de 5 palavras** (RF-11)

```html
Essa mensagem é muito curta para eu conferir.
Pode mandar a mensagem inteira, do jeito que ela chegou para você?
```

**Erro interno** (RNF-09): qualquer exceção na busca, no classificador ou na extração.

```html
Deu um problema aqui e não consegui conferir agora. Tente de novo daqui a pouco.
```

**Resposta ao 👍/👎** (RF-12): edite a mensagem só para tirar os botões e responda com:

```html
Obrigado! Sua resposta ajuda a melhorar o bot.
```
