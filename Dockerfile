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

# Copia arquivos de configuração de pacote
COPY pyproject.toml README.md ./

# Instala o pacote e dependências (busca para camada 1 e test para validações)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e '.[test,busca]'

# Copia o código da aplicação e artefatos autocontidos (modelo e índice)
COPY src/ ./src/
COPY experiments/*.py ./experiments/
COPY data/ ./data/
COPY tests/ ./tests/
COPY models/ ./models/

# Cria diretório para logs persistentes e índices
RUN mkdir -p data/registros data/indices models

# Comando padrão: executa o bot no Azure Container Apps
CMD ["python", "-m", "checagens.bot"]

