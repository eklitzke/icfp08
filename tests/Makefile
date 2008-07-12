.PHONY: all test_message test_turning

all:
	for unit_test in $$(find . -name 'test_*.py'); do PYTHONPATH=.:../src python $$unit_test; done

test_message:
	PYTHONPATH=.:../src python test_message.py

test_turning:
	PYTHONPATH=.:../src python test_turning.py
