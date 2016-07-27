# makefile for NBS
.PHONY: all clean test
all: test

test: export PYTHONPATH=./:./utest
test:
	@echo building test...
	python utest/run_all_tests.py

clean:
	@echo cleaning...

