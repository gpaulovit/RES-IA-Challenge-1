# Apresentação em cinco minutos

## Antes de começar

Siga a instalação no [README do repositório](https://github.com/gpaulovit/RES-IA-Challenge-1#como-executar),
execute `python -m pytest -q` e inicie o servidor na raiz do projeto:

```sh
python -m uvicorn checagens.api:app --host 127.0.0.1 --port 8000
```

Deixe um segundo terminal aberto para as consultas. Se tiver internet, também
pode usar <http://127.0.0.1:8000/docs>, em **POST /buscar → Try it out → Execute**.

## 0:00–1:00 — Problema e objetivo

“Queremos ajudar a encontrar checagens anteriores de boatos que voltam a circular.
Hoje vamos mostrar o primeiro passo: as partes do programa funcionando juntas.
Os três exemplos são inventados e não representam fatos reais.”

## 1:00–2:00 — Consulta com resultado

```sh
curl -X POST http://127.0.0.1:8000/buscar \
  -H 'Content-Type: application/json' \
  -d '{"texto":"transporte gratuito domingos","top_k":3}'
```

Mostre `demo-002`, a alegação original, o texto da checagem e a agência fictícia.
Explique: “A pontuação mede palavras parecidas. Ela não diz se minha pergunta é
verdadeira. O veredito mostrado pertence somente ao exemplo.”

## 2:00–3:00 — Consulta sem resultado

```sh
curl -X POST http://127.0.0.1:8000/buscar \
  -H 'Content-Type: application/json' \
  -d '{"texto":"abacaxi telescópio submarino"}'
```

Mostre `nao_encontrada` e a lista vazia. Explique: “Essas palavras não aparecem
na nossa pequena base. Não encontrar não significa que uma afirmação seja nova
ou verdadeira.”

## 3:00–4:00 — Organização da Engenharia

Mostre o desenho no [guia de Engenharia](engenharia.md): dados → representação
em números → busca → resposta pela API. Explique: “As partes estão separadas
para receber os dados e o modelo que as outras frentes entregarem. Os testes
ajudam a perceber se alguma troca quebrou o funcionamento.”

## 4:00–5:00 — Limites e próximos passos

“Ainda usamos palavras compartilhadas, sem compreensão de significado.
Precisamos validar os dados reais, comparar modelos e definir regras de
confiança. A demonstração de hoje prepara essa integração.”

Mostre a tabela de [funcionalidades](funcionalidades.md) para distinguir o
que já funciona do que está planejado. Termine com o resultado dos testes.

## Resumo

**Apresente uma busca com resultado, outra sem resultado e o desenho das peças.
Explique que tudo é fictício e que os próximos passos são dados, modelo e confiança.**
