ROOTPATH := .
DEVPATH = $(ROOTPATH)/.dev
DEVMKFILE := $(DEVPATH)/makefile
SRCPATH := $(ROOTPATH)/schemaconvertor

# ENV VARS
PYENV := env PYTHONPATH=$(SRCPATH)
PYTHON := $(PYENV) python
PEP8 := $(PYENV) pep8 --repeat --ignore=E202,E501
PYLINT := $(PYENV) pylint --disable=I0011 --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"
PYTEST := $(PYENV) py.test -v -x
PIPINSTALL := $(PYENV) pip install -i http://pypi.douban.com/simple/

-include $(DEVMKFILE)

.PHONY: dev-mk clean full-clean pylint pylint-full test requires

dev-mk:
	@echo "\033[33mmake from $(DEVMKFILE)\033[0m"

clean:
	@find . -name "__pycache__" -type d -exec rm -rf {} \; >/dev/null 2>&1 || true
	@find . -name "*.pyc" -type f -exec rm -rf {} \; >/dev/null 2>&1 || true
	@echo "\033[33mclean $(SRCPATH)\033[0m"

pylint:
	$(PEP8) $(SRCPATH)
	$(PYLINT) -E $(SRCPATH)

pylint-full:
	$(PYLINT) $(SRCPATH)

test: pylint
	$(PYTEST) $(SRCPATH)

requires: $(ROOTPATH)/requirements.txt
	$(PIPINSTALL) -r $(ROOTPATH)/requirements.txt

pypi-upload:
	pandoc README.md -o README.rst
	$(PYTHON) setup.py clean bdist_egg sdist upload
	$(PYTHON) setup.py clean
