.DEFAULT_GOAL := help


.PHONY: build
build-app: ## Builds final app Docker image
	docker build -t dim:latest-dev --target=app -f Dockerfile .

.PHONY: test
build-test: ## Builds test Docker image containing all dev requirements
	docker build -t dim:latest-test --target=test -f Dockerfile .

test: build-test ## Builds test Docker image and executes Python tests
	docker run dim:latest-test python -m pytest dim/tests/

# For setting up local environment
venv:
	if [ -d "venv" ]; then echo "venv directory already exists"; fi
	python -m venv venv

upgrade-pip:
	venv/bin/python -m pip install --upgrade pip

install-requirements:
	python -m pip install -r requirements/requirements.in

install-dev-requirements:
	python -m pip install -r requirements/dev-requirements.in

setup-local-env: venv upgrade-pip install-requirements install-dev-requirements

# help source: https://stackoverflow.com/a/64996042
.PHONY: help
help:
	@echo "Available commands:"
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'