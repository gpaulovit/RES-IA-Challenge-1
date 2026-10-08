# Cronograma

## Como editar este cronograma

Este é um documento vivo. Mover datas, mover itens entre semanas ou
reescopar uma entrega é esperado conforme a equipe aprende mais sobre o
problema, o domínio e os modelos. Ao editar:

- Mantenha a estrutura de semanas (objetivo → base → atividades → entregável).

---

## Semana 1 — Estudo de caso, do problema e do domínio [Concluída]

- **Status:** ✅ Concluída
- **Objetivo alcançado:** Levantamento de causa raiz e domínio em `perguntas.md`, exploração do corpus `FactPolCheckBr` e protótipo inicial com três exemplos fictícios para demonstração.
- **Entregável:** Relatório de cobertura e mapeamento de taxonomia de vereditos.

---

## Semana 2 — Estudo dos modelos e representação vetorial [Concluída]

- **Status:** ✅ Concluída
- **Objetivo alcançado:** Pipeline de representação vetorial e geração de embeddings com hash de manifesto (`embeddings.py`), rejeição de saídas inválidas e criação do conjunto de benchmark (`data/testes_benchmark.json`).
- **Redirecionamento:** O modelo de reincidência temporal foi descartado do escopo de produto; a representação vetorial por embeddings foi reaproveitada como a **Camada 1 (busca factual)** do bot.

---

## Semana 3 — Construção: indexação e retrieval k-NN [Concluída]

- **Status:** ✅ Concluída
- **Objetivo alcançado:** Implementação da busca exata por vizinhos mais próximos (`retrieval.py`), desempate estável por ID e módulo de avaliação automatizada de recuperação (`avaliacao.py` com Recall@1, Recall@3, Recall@5, MRR e latência).
- **Entregável:** Buscador vetorial funcionando com suíte de testes passando.

---

## Semana 4 — Reenquadramento do Produto e Requisitos [Concluída]

- **Status:** ✅ Concluída
- **Objetivo alcançado:** Reescrita completa dos requisitos em `docs/requisitos.md` e histórias em `docs/historias.md` para o produto final: **Bot no Telegram em duas camadas**.
- **Entregável:** Definição das regras de negócio (RN-01 a RN-07), requisitos funcionais (RF-01 a RF-14), critérios de go/no-go e checklist de reta final distribuído por responsável (Issues #34 a #38).

---

## Semana 5 (Reta Final) — Bot no Telegram, Testes, MLOps e Entrega (13/10) [Em Andamento]

- **Status:** 🚀 Em andamento (Entrega final em 13/10/2026)
- **Objetivo:** Bot no Telegram funcionando de ponta a ponta, com pipeline de CI/CD, testes de robustez e transparência, registros anônimos em conformidade com a LGPD e ensaios gerais para a apresentação.

**Atividades por Frente:**
- **Produto (Ana):** Textos do bot, validação dos fluxos, roteiro de pitch e apresentação (#34).
- **Dados (Cibelly):** Base consolidada de checagens (`data/processados/checagens/`) e base balanceada de treino/teste para o classificador (#35).
- **Modelos (Paulo):** Busca calibrada da Camada 1, classificador baseline da Camada 2 e relatório de métricas go/no-go (#36).
- **Engenharia (Eduarda):** Desenvolvimento do bot no Telegram, comandos `/start`, extração de links e integração das duas camadas (#37).
- **DevOps/MLOps (Ingrid):** Pipeline de CI com GitHub Actions, testes de robustez (RNF-09) e transparência (RNF-07), registro anônimo de consultas/votos (RF-13/RNF-08), versionamento DVC e infraestrutura do bot no ar (#38).

**Entregável:** Bot no ar no Telegram, suíte de testes 100% verde, vídeo de demonstração (plano B) e apresentação final do projeto.

---

## Frentes de trabalho

O grupo dividiu o trabalho em 5 frentes, uma por pessoa. As frentes
espelham os labels `papel:` usados nas issues e PRs do GitHub:

- **Engenharia** (`papel: engenharia`) — Desenvolvimento do bot no Telegram (`python-telegram-bot`), extração de links, integração das chamadas às duas camadas de decisão e interface do usuário.
- **Domínio de dados** (`papel: dominio-dados`) — Curadoria e saneamento da base de checagens históricas e das bases de treino/teste do classificador (`Fake.br`, `FakeWhatsApp.Br`).
- **Modelos de IA** (`papel: modelos-ia`) — Calibração dos limiares de semelhança da busca vetorial, treinamento do classificador baseline (TF-IDF + Regressão Logística) e relatório de go/no-go.
- **Produto e decisão** (`papel: produto-decisao`) — Especificação funcional, redação das mensagens e diálogos do bot, validação de experiência do eleitor e apresentação executiva.
- **DevOps e MLOps** (`papel: devops-mlops`) — Infraestrutura de automação (CI/CD via GitHub Actions, Makefile), testes de robustez e transparência, auditoria de privacidade (LGPD), versionamento com DVC e suporte à disponibilidade do bot.

---

## Papéis e responsabilidades

| Nome | Integrante | Foco principal | Issue da Reta Final |
| :--- | :--- | :--- | :--- |
| **Eduarda** | Eduarda | Engenharia | [#37](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/37) |
| **Cibelly** | Cibelly Lourenço | Domínio de dados | [#35](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/35) |
| **Paulo** | Paulo | Modelos de IA | [#36](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/36) |
| **Ana Júlia** | Ana Júlia | Produto e decisão | [#34](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/34) |
| **Ingrid** | Ingrid Soares | DevOps e MLOps | [#38](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/38) |
