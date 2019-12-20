all: install

PACKAGE = altair_viewer

install:
	pip install .

test:
	python -m black .
	python -m flake8 $(PACKAGE)
	python -m mypy $(PACKAGE)
	rm -rf build
	python setup.py build &&\
	  cd build/lib &&\
	  python -m pytest --pyargs --doctest-modules $(PACKAGE)

test-coverage:
	python setup.py build &&\
	  cd build/lib &&\
	  python -m pytest --pyargs --doctest-modules --cov=$(PACKAGE) --cov-report term $(PACKAGE)

test-coverage-html:
	python setup.py build &&\
	  cd build/lib &&\
	  python -m pytest --pyargs --doctest-modules --cov=$(PACKAGE) --cov-report html $(PACKAGE)
