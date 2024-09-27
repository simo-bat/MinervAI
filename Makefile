.PHONY: install
install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt -U
	pip install -e . --no-deps

.PHONY: ruff
ruff:
	ruff format .
	ruff check . --fix

.PHONY: isort
isort:
	isort src --profile black --line-length=120
	isort tests --profile black --line-length=120

.PHONY: flake8
flake8:
	flake8 src --count --show-source --statistics

.PHONY: mypy
mypy:
	mypy --install-types --ignore-missing-imports --non-interactive

.PHONY: pytest
pytest:
	pytest tests/

.PHONY: format
format:
	make ruff
	make isort
	make mypy

.PHONY: test
test:
	make install
	make isort
	make black
	make flake8
	make mypy
	make pytest

.PHONY: run
run:
	streamlit run src/minervai/app.py --theme.primaryColor="FFF700" --theme.base="dark"