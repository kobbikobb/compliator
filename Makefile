.PHONY: help install init demo collect verify test list status check-words clean

# The engine is imported from src/, not installed, so it needs src on the path.
PYTHONPATH := src

.DEFAULT_GOAL := help

# `make` or `make help` lists every target; the text after `##` is the doc.
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-12s %s\n", $$1, $$2}'

install: ## Install the one runtime dependency (PyYAML)
	python3 -m pip install -r requirements.txt

init: ## Scaffold a new instance's ISMS documents (interactive)
	PYTHONPATH=$(PYTHONPATH) python3 -m compliator init

demo: collect verify ## Collect evidence from the synthetic fixtures, then verify every record

collect: ## Collect evidence from the synthetic fixtures into evidence/
	PYTHONPATH=$(PYTHONPATH) python3 -m compliator collect

verify: ## Re-hash and verify every record under evidence/
	PYTHONPATH=$(PYTHONPATH) python3 -m compliator verify evidence

test: ## Run the unit test suite
	PYTHONPATH=$(PYTHONPATH) python3 -m unittest discover -s tests

list: ## List the controls the current config defines
	PYTHONPATH=$(PYTHONPATH) python3 -m compliator list

# Reports on the repository's own documents and evidence. Exits 1 when it has
# findings, so it is not part of `make demo` - a young instance is meant to have
# them.
status: ## Report whether the ISMS documents and evidence are still true
	PYTHONPATH=$(PYTHONPATH) python3 -m compliator status

check-words: ## Fail if a tracked file contains banned vocabulary (scripts/slop-words.txt)
	python3 scripts/check_words.py

clean: ## Remove generated records but keep the tracked evidence/.gitkeep
	rm -rf evidence/*
	mkdir -p evidence
