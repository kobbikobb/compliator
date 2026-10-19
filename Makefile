.PHONY: demo collect verify test list status check-words clean

# The engine is imported from src/, not installed, so it needs src on the path.
PYTHONPATH := src

demo: collect verify

collect:
	PYTHONPATH=$(PYTHONPATH) python3 -m compliator collect

verify:
	PYTHONPATH=$(PYTHONPATH) python3 -m compliator verify evidence

test:
	PYTHONPATH=$(PYTHONPATH) python3 -m unittest discover -s tests

list:
	PYTHONPATH=$(PYTHONPATH) python3 -m compliator list

# Reports on the repository's own documents and evidence. Exits 1 when it has
# findings, so it is not part of `make demo` - a young instance is meant to have
# them.
status:
	PYTHONPATH=$(PYTHONPATH) python3 -m compliator status

# remove generated records but keep the tracked .gitkeep: `rm -rf evidence`
# would delete a version-controlled file along with the output
clean:
	rm -rf evidence/*
	mkdir -p evidence

# Banned vocabulary gate; the list is scripts/slop-words.txt.
check-words:
	python3 scripts/check_words.py
