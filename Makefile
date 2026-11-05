# =============================================================================
# Disboard-NGNL — atajos de operación
# =============================================================================
.DEFAULT_GOAL := help
PY ?= python3
PIP ?= $(PY) -m pip

.PHONY: help install install-dev lint format test test-fast console web web-dev \
        dashboard check-models status healthcheck clean precommit \
        docker-build docker-up docker-down tunnel speech-test

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# --- Instalación -----------------------------------------------------------
install: ## Instala dependencias de runtime
	$(PIP) install -r requirements.txt

install-dev: ## Instala dependencias de desarrollo
	$(PIP) install -e ".[dev]"
	pre-commit install

install-speech: ## Instala dependencias opcionales de STT/TTS local
	$(PIP) install -e ".[speech]"

# --- Calidad ---------------------------------------------------------------
lint: ## Ejecuta ruff (lint)
	ruff check .

format: ## Ejecuta ruff (formato)
	ruff format .

precommit: ## Ejecuta pre-commit sobre todos los archivos
	pre-commit run --all-files

# --- Pruebas ---------------------------------------------------------------
test: ## Ejecuta la suite completa
	pytest

test-fast: ## Ejecuta solo pruebas rápidas
	pytest -m "not slow and not integration and not antigravity and not speech"

# --- Operación -------------------------------------------------------------
console: ## Abre la consola HITL de Tet
	$(PY) -m console.main

web: ## Levanta el servidor web local (LangGraph + dashboard)
	uvicorn web.server:app --host $${WEB_HOST:-127.0.0.1} --port $${WEB_PORT:-8000}

web-dev: ## Servidor web con recarga automática
	uvicorn web.server:app --reload --host $${WEB_HOST:-127.0.0.1} --port $${WEB_PORT:-8000}

dashboard: ## Arranca el servidor y abre el dashboard en el navegador
	$(PY) -c "import webbrowser, threading; threading.Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:8000')).start()" && \
		uvicorn web.server:app --host $${WEB_HOST:-127.0.0.1} --port $${WEB_PORT:-8000}

check-models: ## Inspección de modelos de Suniaster
	$(PY) -m console.main check-models

status: ## Estado global de Elkia
	$(PY) -m console.main status

healthcheck: ## Verifica entorno, dependencias y servicios
	$(PY) scripts/healthcheck.py

tunnel: ## Levanta Cloudflare Tunnel contra el servidor local
	cloudflared tunnel run disboard-ngnl

speech-test: ## Prueba STT/TTS local (requiere pip install -e ".[speech]")
	$(PY) -m tools.speech_input --test
	$(PY) -m tools.speech_output --test

# --- Docker ----------------------------------------------------------------
docker-build: ## Construye la imagen del devcontainer
	docker compose build

docker-up: ## Levanta los servicios (devcontainer, web, postgres)
	docker compose up -d

docker-down: ## Detiene los servicios
	docker compose down

# --- Limpieza --------------------------------------------------------------
clean: ## Limpia cachés y artefactos locales
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
