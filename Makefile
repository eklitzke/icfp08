.PHONY: all clean compile test

all: clean compile test

test: 
	make -C tests

clean:
	find . -name '*.pyc' -exec rm \{\} \;

compile:
	python -c "import compileall; compileall.compile_dir('src')"
