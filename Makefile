src_dirs = src
obfuscate_dirs = obfuscate
test_dirs = tests
all_dirs = $(src_dirs) $(test_dirs)

.PHONY: all help pre-commit format lint pytest test ci-test clean-pyc clean-test clean poetry-setup run build restart-api obfuscate clean-obfuscate python-obfuscate

help:
	@echo "gen_api_spec - generate OpenAPI spec"
	@echo "build - build docker image"
	@echo "run - run docker image"
	@echo "format - format Python code with isort/Black"
	@echo "lint - check style with pylint"
	@echo "mypy - run the static type checker"
	@echo "check - run all static checks and analyzers"
	@echo "commitlint - run the git hooks"
	@echo "pytest - run the tests and measure the code coverage"
	@echo "test - run the code formatter, linter, type checker, tests and coverage"
	@echo "ci-test - run the Continuous Integration (CI) pipeline (check-only)"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "clean - remove test and coverage artifacts"
	@echo "pytest-obfuscate - run the tests with the obfuscated source code"
	@echo "obfuscate - obfuscate the source code"
	@echo "clean-obfuscate - remove the obfuscated source code"

pre-commit:
	pre-commit install

poetry-setup:
	poetry lock --no-update
	poetry install --no-root --no-interaction

build:
	docker compose -f docker/docker-compose.yaml build

build-dev:
	docker compose -f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml build

run: build
	docker compose -f docker/docker-compose.yaml up

run-dev: build-dev
	docker compose -f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml up

restart-api: build
	docker compose \
		-f docker/docker-compose.yaml up -d api_core

restart-api-dev: build-dev
	docker compose \
		-f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml up -d api_core

gen_api_spec:
	poetry run python -m scripts.gen_openapi --output-dir . --version 1.0.0
	
format:
	poetry run ruff format $(all_dirs)

lint:
	poetry run ruff check $(src_dirs) --fix

pytest:
	poetry run pytest $(test_dirs)

ci-test: lint
	make pytest

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} + || true
	find . -name '*.pyo' -exec rm -f {} + || true
	find . -name '*~' -exec rm -f {} + || true
	find . -name '__pycache__' -exec rm -fr {} + || true
	find . -name '.pytest_cache' -exec rm -fr {} + || true

clean-test:
	rm -rf reports || true
	rm -f .coverage || true
	rm -f coverage.xml || true
	rm -fr htmlcov || true

clean: clean-pyc clean-test clean-obfuscate

export CDKTF_IMAGE ?= object-detection-infra

build-cdktf-image:
	cd infra && docker build \
		-t $(CDKTF_IMAGE) \
		-f docker/Dockerfile .

run-cdktf-env: build-cdktf-image
	docker run \
		--rm \
		-it \
		-v $(PWD):/app \
		-w /app \
		$(CDKTF_IMAGE) \
		bash -c "cd infra && poetry install && bash"

cdktf-plan:
	cdktf plan ObjectDetectionStack

cdktf-deploy:
	cdktf deploy ObjectDetectionStack --auto-approve