export HUMAN_DATETIMES_LOG_LEVEL=DEBUG

OUTPUT ?= dist

build: prepare
	poetry build --output=$(OUTPUT)

test: prepare
	poetry run -- pytest --showlocals --show-capture=all

prepare: .venv
.venv: pyproject.toml poetry.lock
	poetry install
	@touch "$@"

deepclean:
	rm -rf .venv

.PHONY: build test prepare
