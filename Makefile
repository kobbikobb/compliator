.PHONY: demo collect verify test list clean

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

clean:
	rm -rf evidence
	mkdir -p evidence
