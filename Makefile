BIN := venv/bin
PYTHON := $(BIN)/python

venv: requirements.txt
	virtualenv venv
	$(BIN)/pip install -r requirements.txt

.PHONY: clean
clean:
	rm -rf venv
	tmux -S transfer_socket kill-session -a init

setup:
	tmux -S transfer_socket new -s init -d

