# makefile for NBS
.PHONY: all clean test
all: test

test: export PYTHONPATH=./:./tst
test:
	@echo building test...
	python tst/run_all_tests.py

clean:
	@echo cleaning...

