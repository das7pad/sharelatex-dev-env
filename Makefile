python ?= python3

unittest ?= $(python) -m unittest

UNITTESTS ?= \
	generator/tests \

.PHONY: all
all: test

.PHONY: install
install:
	@$(python) -c 'import jinja2' \
	|| echo "\n\n  please install python-jinja2 manually"

.PHONY: test
test: $(UNITTESTS)

.PHONY: $(UNITTESTS)
$(UNITTESTS):
	$(unittest) discover $@

.PHONY: clean
clean:
	find . -name '*py[cod]' -or -name __pycache__ -exec rm -rf {} \+
