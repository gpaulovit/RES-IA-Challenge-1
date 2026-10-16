# Imagem base oficial leve com Python 3.11
FROM python:3.11-slim

# Evita criação de arquivos .pyc e buffer de saída
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de configuração de pacote e código fonte
COPY pyproject.toml README.md params.yaml ./
COPY src/ ./src/

# Instala o pacote e dependências (busca para camada 1 e test para validações)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e '.[test,busca]'

# Pré-carrega e faz cache dos modelos de IA no build (evita download de 1GB e estouro de memória em runtime)
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', revision='e8f8c211226b894fcb81acc59f3b34ba3efd5f42'); \
CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1', revision='1427fd652930e4ba29e8149678df786c240d8825')"

# Copia experimentos, dados, testes e artefatos
COPY experiments/*.py ./experiments/
COPY data/ ./data/
COPY tests/ ./tests/
COPY models/ ./models/

# Cria diretório para logs persistentes e índices
RUN mkdir -p data/registros data/indices models

# Comando padrão: executa o bot no Azure Container Apps
CMD ["python", "-m", "checagens.bot"]

