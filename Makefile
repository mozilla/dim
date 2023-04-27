.DEFAULT_GOAL := help

IMAGE_REPO	   := gcr.io/data-monitoring-dev
IMAGE_BASE     := dim
IMAGE_VERSION  := latest
IMAGE_NAME     := $(IMAGE_BASE):$(IMAGE_VERSION)

CONTAINER_NAME := $(IMAGE_BASE)

.PHONY: build
build: ## Builds final app Docker image
	@docker build -t ${IMAGE_BASE}:${IMAGE_VERSION} -f Dockerfile .

.PHONY: test
test-unit: build ## Runs python unit tests for dim and tests directories
	@docker run ${IMAGE_BASE}:${IMAGE_VERSION} python -m pytest dim/ tests/

test-black: build ## Runs black check against python code inside dim and tests directories
	@docker run ${IMAGE_BASE}:${IMAGE_VERSION} python -m black --line-length=100 --check dim/ tests/

test-flake8: build ## Runs flake8 against python code inside dim and tests directories
	@docker run ${IMAGE_BASE}:${IMAGE_VERSION} python -m flake8 --max-line-length=100 dim/ tests/

test-isort: build ## Runs isort check against python code inside dim and tests directories
	@docker run ${IMAGE_BASE}:${IMAGE_VERSION} python -m isort --check dim/ tests/

test-mypy: build ## Runs mypy against python code inside dim and tests directories
	@docker run ${IMAGE_BASE}:${IMAGE_VERSION} python -m mypy dim/ tests/

test-all: build test-unit test-flake8 test-isort test-black #test-mypy ## Runs all make test-* commands

format-black: ## Runs black against python code inside dim and tests directories
	@venv/bin/python -m black --line-length=100 dim/ tests/

format-isort: ## Runs black against python code inside dim and tests directories
	@venv/bin/isort dim/ tests/

format: format-isort format-black ## Runs black and isort formatting against python code inside dim and tests directories

# For setting up local environment
setup-venv: ## Sets up local venv directory and installs python package dependencies in that environment
ifneq ($(wildcard venv/.*),)
	@echo "venv/ directory already exists to setup venv from scratch"
	@echo "run 'make clean' then re-run this command"
else
	@python python -m venv venv
	@venv/bin/python python -m pip install pip-tools
	@make upgrade-pip
	@make update-deps
	@make update-local-env
endif

upgrade-pip: setup-venv ## Upgrades pip version inside the virtual environment
	@venv/bin/python python -m pip install --upgrade pip

@PHONY: pip-compile
pip-compile: ## Runs pip-compile and stores the output inside requirements/requirements.txt
	@venv/bin/pip-compile -o - - <<< '.' | \
		grep -v 'file://' | \
    	sed 's/pip-compile.*/update_deps/' > requirements/requirements.in
	@venv/bin/pip-compile --generate-hashes -o requirements/requirements.txt requirements/requirements.in

pip-compile-dev: ## Runs pip-compile and stores the output inside requirements/dev-requirements.txt
	@venv/bin/pip-compile -o - - <<< '.[testing]' | \
		grep -v 'file://' | \
    	sed 's/pip-compile.*/update_deps/' > requirements/dev-requirements.in
	@venv/bin/pip-compile --generate-hashes -o requirements/dev-requirements.txt requirements/dev-requirements.in

install-requirements: setup-venv upgrade-pip pip-compile ## Install packages defined inside requirements/requirements.txt inside the virtual env
	@venv/bin/python python -m pip install -r requirements/requirements.txt
install-requirements-dev: setup-venv upgrade-pip pip-compile-dev ## Install packages defined inside requirements/dev-requirements.txt inside the virtual env
	@venv/bin/python python -m pip install -r requirements/dev-requirements.txt

update-deps: pip-compile pip-compile-dev ## Runs pip-compile commands for both requirement files
update-local-env: install-requirements install-requirements-dev ## Installs all python packages defined inside both requirement files inside the virtuan env

.PHONY: clean
make clean:  ## Removes venv directory and all its contents
	@rm -rf venv/


DIM_CHECKS_FOLDER := dim/models/dim_check_type
DIM_CHECKS_SQL_FOLDER := $(DIM_CHECKS_FOLDER)/templates

# # source: https://stackoverflow.com/a/14061796
new-dim-test-type:
ifndef TEST_TYPE
	$(error No value provided for TEST_TYPE)
endif

	@echo "Creating files for new dim check type: $(TEST_TYPE)	"
	@cp $(DIM_CHECKS_SQL_FOLDER)/template.sql.jinja $(DIM_CHECKS_SQL_FOLDER)/$(TEST_TYPE).sql.jinja
	@echo Created new sql template: $(DIM_CHECKS_SQL_FOLDER)/$(TEST_TYPE).sql

	@cp $(DIM_CHECKS_FOLDER)/template.py $(DIM_CHECKS_FOLDER)/$(TEST_TYPE).py
	@echo Created new python module: $(DIM_CHECKS_FOLDER)/$(TEST_TYPE).py

# help source: https://stackoverflow.com/a/64996042
.PHONY: helppush
help:
	@echo "Available commands:"
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

run:
	docker run -v /Users/alekhya/Downloads/data-monitoring-dev-4b8f7f96a12e.json:/test_service_account.json \
		-e GOOGLE_APPLICATION_CREDENTIALS="/test_service_account.json" \
		--rm \
		 ${IMAGE_NAME}

shell:
	docker run -it --entrypoint=/bin/bash --rm --name ${CONTAINER_NAME} ${IMAGE_NAME}

stop:
	docker stop ${CONTAINER_NAME}

push:
	docker tag ${IMAGE_NAME} ${IMAGE_REPO}/${IMAGE_NAME}
	docker push ${IMAGE_REPO}/${IMAGE_NAME}
