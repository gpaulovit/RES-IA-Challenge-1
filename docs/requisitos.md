# Especificação de Requisitos do Sistema (RES-IA-Challenge-1)

Documento de especificação de Requisitos Funcionais (RF), Requisitos Não-Funcionais (RNF) e Restrições de Arquitetura do sistema de detecção e recuperação semântica de desinformação eleitoral reciclada, alinhado às Histórias de Usuário (US-01 a US-10) e aos padrões de MLOps.

---

## 1. Requisitos Funcionais (RF)

*Descrevem as capacidades, comportamentos e ações ativas que o sistema deve executar em resposta às consultas dos usuários.*

| Código | Requisito Funcional | Descrição Detalhada | Histórias de Usuário (US) |
| :--- | :--- | :--- | :--- |
| **RF-01** | **Busca Semântica por Alegações** | O sistema deve permitir a entrada de textos livres em linguagem natural (mensagens de WhatsApp, trechos de notícias ou boatos) e recuperar as checagens correspondentes no acervo por similaridade vetorial $k$-NN. | **US-03, US-04** |
| **RF-02** | **Resiliência a Variações Adversariais** | O sistema deve recuperar a checagem original referente a alegações recicladas mesmo quando apresentarem variações de formato (gírias, erros de digitação, apelidos de figuras públicas ou paráfrases). | **US-03, US-04** |
| **RF-03** | **Tratamento de Inversão de Negação** | O sistema deve identificar e diferenciar sentenças com mudança de polaridade ou negação (ex: *"Lula NÃO fez X"* vs. *"Lula fez X"*), evitando atribuições incorretas de correspondência positiva. | **US-03, US-05** |
| **RF-04** | **Reconhecimento de Reincidência Temporal** | O sistema deve reconhecer boatos antigos (distância $\ge 180$ dias) apresentados com nova roupagem como a mesma alegação catalogada, sem classificá-los como inéditos. | **US-01, US-04** |
| **RF-05** | **Filtro do Grupo de Controle (Falsos Positivos)** | O sistema deve identificar consultas referentes a notícias legítimas e verdadeiras do dia a dia (imprensa) e classificá-las como `sem_match` ou `inédito` quando a similaridade estiver abaixo do limiar predefinido. | **US-02, US-05** |
| **RF-06** | **Exibição Neutra e Completa de Evidências** | O sistema deve exibir o top-5 candidatos contendo obrigatoriamente o texto da alegação de origem, o veredito normalizado, a agência de checagem e o link oficial, sem emitir vereditos automatizados sumários sem respaldo das fontes. | **US-06, US-10** |
| **RF-07** | **Atribuição de Faixas de Confiança** | O sistema deve atribuir os resultados a faixas claras de confiança (`confirmado`, `provável`, `sem match`, `inédito`), encaminhando correspondências duvidosas (zona cinzenta) para revisão humana. | **US-07** |
| **RF-08** | **Isolamento de Conteúdo Misto** | O sistema deve garantir que o veredito de um boato antigo checado não seja aplicado indevidamente a trechos novos adicionados à mensagem (evitar "lavagem" de afirmação nova). | **US-08** |
| **RF-09** | **Exposição de Divergências entre Agências** | O sistema deve identificar e exibir simultaneamente os dois lados quando agências de checagem distintas possuírem vereditos divergentes sobre a mesma alegação, sem escolher um lado em silêncio. | **US-09, US-10** |
| **RF-10** | **Normalização Taxonômica de Vereditos** | O sistema deve mapear e padronizar os diferentes rótulos das agências de origem para uma taxonomia única (`falsa`, `enganosa`, `verdadeira`, `inconclusiva`). | **US-10** |

---

## 🛡️ 2. Requisitos Não-Funcionais (RNF) & Restrições

*Descrevem as propriedades de qualidade, critérios de desempenho, segurança, rastreabilidade e restrições arquiteturais do produto.*

### A. Atributos de Qualidade e Desempenho

* **RNF-01 (Limiar de Decisão e Taxa de Falso Positivo):** O modelo de retrieval deve aplicar o limiar de similaridade semântica de 60% (0.60) para classificação de correspondência (`match_confirmado`), garantindo uma taxa de falso-positivo FPR ≤ 5% no grupo de controle de notícias reais. *(Vinculado a **US-05, US-07**)*
* **RNF-02 (Acurácia de Retrieval / Recall@5):** O sistema deve atingir Recall@5 ≥ 70% no conjunto global de testes de benchmark e Recall@5 ≥ 60% especificamente em pares com reincidência temporal ≥ 180 dias. *(Vinculado a **US-03, US-04**)*
* **RNF-03 (Latência da Busca):** O mecanismo de recuperação semântica $k$-NN em memória deve processar a consulta e retornar o Top-5 de evidências em tempo inferior a 2 segundos. *(Vinculado a **US-03, US-06**)*
* **RNF-04 (Completude das Evidências):** 100% dos resultados retornados no Top-5 devem apresentar a estrutura de campos obrigatórios completa (texto original + veredito + agência + link). *(Vinculado a **US-06**)*

### B. Restrições e Arquitetura (Constraints & MLOps)

* **RNF-05 (Arquitetura Simplificada em Memória):** O sistema deve operar via busca vetorial $k$-NN exata direta em memória para o volume atual do corpus, dispensando a complexidade e o custo de manutenção de um banco vetorial dedicado nesta fase do MVP. *(Vinculado a **US-01, US-03**)*
* **RNF-06 (Rastreabilidade e Versioneamento de MLOps):** Todo o pipeline de geração de embeddings, a bancada de testes de benchmark (`data/testes_benchmark.json`) e a suíte de testes devem ser estritamente versionados via Git/DVC e reprodutíveis via esteira de automação (`pytest`). *(Vinculado a **US-02, US-03**)*
* **RNF-07 (Privacidade e Segurança de Dados):** O sistema não deve armazenar ou persistir dados pessoais identificáveis (PII) eventualmente presentes nas consultas submetidas pelos usuários finais. *(Vinculado a **US-03, US-05**)*