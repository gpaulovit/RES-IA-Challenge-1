.PHONY: help install test benchmark latency sample-index sample-retrieval run-api clean

PYTHON ?= python3
VENV ?= .venv

help:
	@echo "Comandos disponíveis:"
	@echo "  make install           - Instala o pacote em modo editável com dependências de teste"
	@echo "  make test              - Executa a suíte de testes automatizados com pytest"
	@echo "  make benchmark         - Executa a avaliação automatizada de recuperação (MLOps)"
	@echo "  make latency           - Afeere a latência e tempo de resposta das 30 mensagens (RNF-01)"
	@echo "  make sample-index      - Gera o índice de embeddings com a amostra fictícia"
	@echo "  make sample-retrieval  - Executa uma busca k-NN de teste no índice da amostra"
	@echo "  make run-api           - Inicia o servidor da API local (Uvicorn) na porta 8000"
	@echo "  make clean             - Remove arquivos temporários e caches"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[test]'

test:
	$(PYTHON) -m pytest -v

benchmark:
	$(PYTHON) -m checagens.avaliacao --benchmark data/testes_benchmark.json --indice data/indices/amostra --modelo baseline-hashing --top-k 3

latency:
	$(PYTHON) scripts/medir_latencia.py

sample-index:
	$(PYTHON) -m checagens.embeddings \
		--corpus data/amostras/corpus-organizado-exemplo.json \
		--saida data/indices/amostra \
		--modelo baseline-hashing

sample-retrieval:
	$(PYTHON) -m checagens.retrieval \
		--indice data/indices/amostra \
		--modelo baseline-hashing \
		--texto "Vídeo antigo não mostra o evento desta semana" \
		--top-k 3

run-api:
	$(PYTHON) -m uvicorn checagens.api:app --host 127.0.0.1 --port 8000 --reload

clean:
	rm -rf __pycache__ .pytest_cache .coverage src/checagens/__pycache__ tests/__pycache__ *.egg-info
