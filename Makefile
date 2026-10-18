.PHONY: demo collect verify test list clean

demo: collect verify

collect:
	python3 -m compliator collect

verify:
	python3 -m compliator verify evidence

test:
	python3 -m unittest discover -s tests

list:
	python3 -m compliator list

clean:
	rm -rf evidence
	mkdir -p evidence
