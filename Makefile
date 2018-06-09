BIN := venv/bin
PYTHON := $(BIN)/python

venv: requirements.txt
	virtualenv -ppython3 venv
	$(BIN)/pip install -r requirements.txt

.PHONY: clean
clean:
	rm -rf venv
