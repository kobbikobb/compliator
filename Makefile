.PHONY: help install init demo collect verify test list status check-words clean

# Prefer .venv/ (created by `make install`) over the system interpreter:
# PEP 668 forbids pip installs into the system Python on macOS/Homebrew.
VENV_PY := .venv/bin/python
PYTHON := $(if $(wildcard $(VENV_PY)),$(VENV_PY),python3)

# The engine is imported from src/, not installed, so it needs src on the path.
PYTHONPATH := src

.DEFAULT_GOAL := help

# `make` or `make help` lists every target; the text after `##` is the doc.
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-12s %s\n", $$1, $$2}'

install: ## Create .venv and install the one runtime dependency (PyYAML)
	python3 -m venv .venv
	$(VENV_PY) -m pip install --quiet -r requirements.txt
	@$(VENV_PY) -c "import yaml; print('installed: PyYAML', yaml.__version__)"

init: ## Scaffold a new instance's ISMS documents (interactive)
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compliator init

demo: collect verify ## Collect evidence from the synthetic fixtures, then verify every record

collect: ## Collect evidence from the synthetic fixtures into evidence/
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compliator collect

verify: ## Re-hash and verify every record under evidence/
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compliator verify evidence

test: ## Run the unit test suite
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests

list: ## List the controls the current config defines
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compliator list

# Reports on the repository's own documents and evidence. Exits 1 when it has
# findings, so it is not part of `make demo` - a young instance is meant to have
# them.
status: ## Report whether the ISMS documents and evidence are still true
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compliator status

check-words: ## Fail if a tracked file contains banned vocabulary (scripts/slop-words.txt)
	python3 scripts/check_words.py

clean: ## Remove generated records but keep the tracked evidence/.gitkeep
	rm -rf evidence/*
	mkdir -p evidence
