all: test

init:
	@pip3 install -r requirements.txt

lint:
	@flake8 .

unit:
	@python3 -m unittest

coverage:
	@coverage run --omit='*/**/tests/*,*/**/bitstring.py' -m unittest
	@coverage report

test: lint unit
