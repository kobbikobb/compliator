.PHONY: help next install install-dev framework start init new-risk status check collect verify list demo test check-words clean-evidence lint format typecheck coverage security ci

# Prefer .venv/ (created by `make install`) over the system interpreter:
# PEP 668 forbids pip installs into the system Python on macOS/Homebrew.
VENV_PY := .venv/bin/python
PYTHON := $(if $(wildcard $(VENV_PY)),$(VENV_PY),python3)

# The engine is imported from src/, not installed, so it needs src on the path.
PYTHONPATH := src

.DEFAULT_GOAL := next

# Runs the engine quietly (@).
COMPLIATOR := @PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compliator

##@ Start here
# ## documents a target; ##@ starts a help section.
help: ## List every target, in the order you use them
	@awk 'BEGIN {FS = ":.*?## "} /^##@/ {printf "\n%s\n", substr($$0, 5)} /^[a-zA-Z0-9_-]+:.*?## / {printf "  make %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo

next: ## Name the one thing to do now (the default target)
	$(COMPLIATOR) next

install: ## Create .venv and install the one runtime dependency (PyYAML)
	@python3 -m venv .venv
	@$(VENV_PY) -m pip install --quiet -r requirements.txt
	@$(VENV_PY) -c "import yaml; print('installed: PyYAML', yaml.__version__)"
	@echo "Next: make next"

##@ Set up (in order)
framework: ## Choose or add a framework (a short menu); FRAMEWORK=... skips it
	$(COMPLIATOR) framework $(if $(FRAMEWORK),--set $(FRAMEWORK))

start: ## A few questions, then draft the scope, risks, policies and statement of applicability
	$(COMPLIATOR) init $(if $(FRAMEWORK),--framework $(FRAMEWORK))

init: start ## Same as start

new-risk: ## Add the next risk (RISK-NNN); TITLE="..." skips the question
	$(COMPLIATOR) new-risk $(if $(TITLE),--title "$(TITLE)")

##@ Check for gaps
# Exit 1 (findings) is expected on a young instance; only exit 2 fails.
status: ## Report every gap: unfinished documents, broken links, stale evidence
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compliator status || [ $$? -eq 1 ]

check: ## Like status, but fail on any finding (for CI)
	$(COMPLIATOR) status

collect: ## Collect evidence into evidence/
	$(COMPLIATOR) collect

verify: ## Re-hash and verify every record under evidence/
	$(COMPLIATOR) verify evidence

list: ## List the controls the config defines
	$(COMPLIATOR) list

##@ Develop
demo: collect verify ## Collect from the synthetic fixtures, then verify every record

test: ## Run the unit test suite
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests

install-dev: install ## Add the developer tools (ruff, mypy, coverage, bandit, pip-audit)
	@$(VENV_PY) -m pip install --quiet -r requirements-dev.txt

lint: ## Ruff lint and format check (what CI runs)
	@$(PYTHON) -m ruff check src tests scripts
	@$(PYTHON) -m ruff format --check src tests scripts

format: ## Apply ruff's fixes and formatting
	@$(PYTHON) -m ruff check --fix src tests scripts
	@$(PYTHON) -m ruff format src tests scripts

typecheck: ## Static type check of src/ with mypy
	@$(PYTHON) -m mypy

coverage: ## Run the tests with warnings as errors and enforce the coverage floor
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -W error -m coverage run -m unittest discover -s tests
	@$(PYTHON) -m coverage report

security: ## Static security scan (bandit) and known-vulnerable dependencies (pip-audit)
	@$(PYTHON) -m bandit -q -c pyproject.toml -r src
	@$(PYTHON) -m pip_audit -r requirements.txt

ci: lint typecheck coverage security check-words ## Everything CI gates on, locally

check-words: ## Fail if a tracked file contains banned vocabulary (scripts/slop-words.txt)
	@python3 scripts/check_words.py

clean-evidence: ## Delete everything under evidence/ (keeps evidence/.gitkeep)
	rm -rf evidence/*
	mkdir -p evidence
