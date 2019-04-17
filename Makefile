venv ?= venv
python ?= python3

unittest ?= $(venv)/bin/python -m unittest

UNITTESTS ?= \

.PHONY: all
all: test

$(venv)/bin/python:
	$(python) -m venv $(venv)
	touch $(venv)/bin/python

$(venv)/bin/pip: $(venv)/bin/python
	$(venv)/bin/pip install --upgrade pip
	touch $(venv)/bin/pip

$(venv)/.deps: $(venv)/bin/pip
$(venv)/.deps: requirements.txt
	$(venv)/bin/pip install -r requirements.txt
	touch $(venv)/.deps

.PHONY: test
test: $(UNITTESTS)

.PHONY: $(UNITTESTS)
$(UNITTESTS): $(venv)/.deps
	$(unittest) discover $@

.PHONY: clean
clean:
	rm -rf $(venv) .cache
	find . -name '*py[cod]' -or -name __pycache__ -exec rm -rf {} \+
