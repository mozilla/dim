.DEFAULT_GOAL := help


.PHONY: build
build-app: ## Builds final app Docker image
	@docker build -t dim:latest-dev --target=app -f Dockerfile .

test: build-test ## Builds test Docker image and executes Python tests
	@docker run dim:latest-test python -m pytest dim/tests/

.PHONY: test
build-test: ## Builds test Docker image containing all dev requirements
	@docker build -t dim:latest-test --target=test -f Dockerfile .

test-black: build-test
	@docker run dim:latest-test python -m black --check dim/

test-flake8: build-test
	@docker run dim:latest-test python -m flake8 dim/

test-mypy: build-test
	@docker run dim:latest-test python -m mypy dim/

test-all: build-test test test-black test-flake8 test-mypy

# For setting up local environment
setup-venv:
ifneq ($(wildcard venv/.*),)
	@echo "venv/ directory already exists to setup venv from scratch"
	@echo "run 'make clean' then re-run this command"
else
	@python -m venv venv
endif

upgrade-pip: setup-venv
	@venv/bin/python -m pip install --upgrade pip

install-requirements: setup-venv
	@venv/bin/python -m pip install -r requirements/requirements.in

install-dev-requirements: setup-venv
	@python -m pip install -r requirements/dev-requirements.in

setup-local-env: setup-venv upgrade-pip install-requirements install-dev-requirements

.PHONY: clean
make clean:  # Removes local env
	@rm -rf venv/

# help source: https://stackoverflow.com/a/64996042
.PHONY: help
help:
	@echo "Available commands:"
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'