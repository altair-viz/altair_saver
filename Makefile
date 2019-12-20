test :
	black .
	flake8 .
	mypy .
	rm -rf build
	python setup.py build &&\
	  cd build/lib &&\
	  python -m pytest --pyargs --doctest-modules altair_savechart

test-coverage:
	python setup.py build &&\
	  cd build/lib &&\
	  python -m pytest --pyargs --doctest-modules --cov=altair_savechart --cov-report term altair_savechart

test-coverage-html:
	python setup.py build &&\
	  cd build/lib &&\
	  python -m pytest --pyargs --doctest-modules --cov=altair_savechart --cov-report html altair_savechart
