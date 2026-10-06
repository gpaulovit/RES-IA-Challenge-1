# Semana 4 — Produto & Decisão: Política de Decisão, Limiares e Mensagens ao Usuário

Este documento estabelece as diretrizes de negócio, as regras operacionais de decisão e a taxonomia das respostas do sistema de checagem, mapeadas de acordo com as Histórias de Usuário (**US-07 a US-10**) e alinhadas aos princípios de MLOps (observabilidade, auditabilidade e mitigação de falsos positivos).

---

## 1. Escopo e Objetivos da Política de Decisão

A política de decisão define como o resultado numérico da busca vetorial ($k$-NN por similaridade de cosseno) é traduzido em uma resposta compreensível, segura e neutra para o usuário final.

---

## 2. Mapeamento de Faixas de Similaridade (Thresholds)

Para garantir que o modelo não emita julgamentos categóricos indevidos sem o nível de confiança adequado, definem-se três faixas operacionais:

| Faixa de Similaridade | Classificação | Veredito de Produto | Ação do Sistema |
| :--- | :---: | :--- | :--- |
| **Score $\ge 0.85$** | **Alta Similaridade** | *Match* Confirmado / Recorrência de Boato | Retorna a checagem de referência correspondente com o veredito original da agência e o link da evidência. |
| **$0.60 \le \text{Score} < 0.85$** | **Média Similaridade** | Checagem Relacionada / Contexto Próximo | Apresenta a checagem como conteúdo correlato ou contextual, sem cravar equivalência exata de fatos. |
| **Score $< 0.60$** | **Baixa Similaridade** | Consulta Inédita / Sem Match | Classifica como não encontrada no acervo. Preserva o grupo de controle e evita falsos positivos ($FPR \le 5\%$). |

---

## 3. Padronização do Tom e Formato das Respostas

Conforme estabelecido pela **US-08** e pelas boas práticas de governança em IA/MLOps:
1. **Neutralidade Estrita:** O sistema não emite opiniões pessoais ou julgamentos morais; limita-se a atribuir o veredito e a checagem à fonte checadora original (ex.: Agência Lupa, Aos Fatos, G1 Fato ou Fake).
2. **Estrutura Obrigatória da Resposta:**
   * **Status da Consulta:** (*Encontrada no acervo*, *Relacionada* ou *Não encontrada*).
   * **Resumo da Alegação:** Texto curto da checagem cadastrada.
   * **Veredito da Fonte:** Classificação original dada pela agência (Falso, Distorcido, Sustentável, etc.).
   * **Evidência e Transparência:** Link direto para a matéria de verificação original e data da publicação.

---

## 4. Matriz de Rastreabilidade de Requisitos (Semana 4)

| História de Usuário | Requisitos Relacionados | Regra de Negócio / Política de Decisão Implementada |
| :--- | :--- | :--- |
| **US-07** | **RF-07, RNF-01** | Aplicação das faixas de decisão (Alta $\ge 0.85$, Média $0.60 \text{ a } 0.84$, Baixa $< 0.60$). |
| **US-08** | **RF-06, RF-08** | Exibição neutra de evidências com agência/link e isolamento de conteúdo misto (prevenção de "lavagem" de novas alegações). |
| **US-09** | **RF-05, RF-09** | Resposta neutra para consultas inéditas e apresentação transparente de divergências entre checadores. |
| **US-10** | **RF-10, RNF-04** | Normalização taxonômica de vereditos (`falsa`, `enganosa`, `verdadeira`) e garantia de completude das evidências. |

---

## Próximos Passos
Com as regras de produto formalizadas neste documento, a frente de Engenharia fica respaldada para implementar a lógica da política de decisão (`src/checagens/politica.py` / Issue #19).