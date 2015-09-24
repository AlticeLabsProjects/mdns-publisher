all:
	find . -name '*.py' -type f ! -executable -exec python -m compileall {} \;

clean:
	find . -name '*.pyc' -type f -delete
