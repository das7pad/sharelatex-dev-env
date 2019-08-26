venv ?= venv
python ?= python3

unittest ?= $(venv)/bin/python -m unittest

UNITTESTS ?= \
	generator/tests \

.PHONY: all
all: test

$(venv)/bin/python:
	$(python) -m venv $(venv)

$(venv)/bin/pip: $(venv)/bin/python
	$(venv)/bin/pip install --upgrade pip
	touch $(venv)/bin/pip

$(venv)/bin/generate: $(venv)/bin/pip
$(venv)/bin/generate: requirements.txt
$(venv)/bin/generate: setup.py
$(venv)/bin/generate: $(shell find generator -name '*.py' -not -name version.py)
	$(venv)/bin/pip install --upgrade --editable .

$(venv)/.deps: $(venv)/bin/pip
$(venv)/.deps: requirements.txt
	$(venv)/bin/pip install -r requirements.txt
	touch $(venv)/.deps

.PHONY: install
install: $(venv)/bin/generate

.PHONY: test
test: $(UNITTESTS)

.PHONY: $(UNITTESTS)
$(UNITTESTS): $(venv)/.deps
	$(unittest) discover $@

.PHONY: clean
clean:
	rm -rf $(venv) .cache
	find . -name '*py[cod]' -or -name __pycache__ -exec rm -rf {} \+
