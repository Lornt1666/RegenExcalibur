.PHONY: install test conformance corpus wheel verify

install:
	python -m pip install .

test:
	python -m unittest discover -s tests -v

conformance:
	promptos conformance --output conformance-report.json

corpus:
	promptos corpus --output-dir generated-corpus

wheel:
	python -m pip wheel . --no-deps --wheel-dir dist

verify: install test conformance corpus wheel
