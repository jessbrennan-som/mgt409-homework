.PHONY: install test demo lab clean

VENV := .venv
PY := $(VENV)/bin/python

install:
	bash .cursor/install.sh

test:
	$(PY) -m pytest

demo:
	$(PY) scripts/demo_analysis.py

lab:
	$(VENV)/bin/jupyter lab --no-browser --ip=0.0.0.0 --port=8888

clean:
	rm -rf $(VENV) artifacts .pytest_cache src/*.egg-info
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
