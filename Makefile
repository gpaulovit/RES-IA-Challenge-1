.PHONY: help install test latency clean

PYTHON ?= python3
VENV ?= .venv

help:
	@echo "Comandos disponíveis:"
	@echo "  make install           - Instala o pacote em modo editável com dependências de teste"
	@echo "  make test              - Executa a suíte de testes automatizados com pytest"
	@echo "  make latency           - Afeere a latência e tempo de resposta das 30 mensagens (RNF-01)"
	@echo "  make clean             - Remove arquivos temporários e caches"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[test]'

test:
	$(PYTHON) -m pytest -v

latency:
	$(PYTHON) scripts/medir_latencia.py

clean:
	rm -rf __pycache__ .pytest_cache .coverage src/*/__pycache__ tests/__pycache__ *.egg-info
