.DEFAULT_GOAL := help

IMAGE_REPO	   := gcr.io/data-monitoring-dev
IMAGE_BASE     := dim
IMAGE_VERSION  := latest
IMAGE_NAME     := $(IMAGE_BASE):$(IMAGE_VERSION)

CONTAINER_NAME := $(IMAGE_BASE)
PYTHON_ENTRYPOINT := --entrypoint /usr/local/bin/python

.PHONY: build
build: ## Builds final app Docker image
	@docker build -t ${IMAGE_BASE}:${IMAGE_VERSION} -f Dockerfile .

.PHONY: test
test-unit: build
	@docker run ${PYTHON_ENTRYPOINT} ${IMAGE_BASE}:${IMAGE_VERSION} -m pytest tests/

test-black: build
	@docker run ${PYTHON_ENTRYPOINT} ${IMAGE_BASE}:${IMAGE_VERSION} -m black --line-length=100 --check dim/ tests/

test-flake8: build
	@docker run ${PYTHON_ENTRYPOINT} ${IMAGE_BASE}:${IMAGE_VERSION} -m flake8 --max-line-length=100 dim/ tests/

test-isort: build
	@docker run ${PYTHON_ENTRYPOINT} ${IMAGE_BASE}:${IMAGE_VERSION} -m isort --check dim/ tests/

test-mypy: build
	@docker run ${PYTHON_ENTRYPOINT} ${IMAGE_BASE}:${IMAGE_VERSION} -m mypy dim/ tests/

test-all: build test-unit test-flake8 test-isort test-black #test-mypy

format-black:
	@venv/bin/python -m black dim/ tests/

format-isort:
	@venv/bin/isort dim/ tests/

format: format-isort format-black

# For setting up local environment
setup-venv:
ifneq ($(wildcard venv/.*),)
	@echo "venv/ directory already exists to setup venv from scratch"
	@echo "run 'make clean' then re-run this command"
else
	@python -m venv venv
	@venv/bin/python -m pip install pip-tools
	@make upgrade-pip
	@make update-deps
	@make update-local-env
endif

upgrade-pip: setup-venv
	@venv/bin/python -m pip install --upgrade pip

@PHONY: pip-compile
pip-compile:
	@venv/bin/pip-compile -o - - <<< '.' | \
		grep -v 'file://' | \
    	sed 's/pip-compile.*/update_deps/' > requirements/requirements.in
	@venv/bin/pip-compile --generate-hashes -o requirements/requirements.txt requirements/requirements.in

pip-compile-dev:
	@venv/bin/pip-compile -o - - <<< '.[testing]' | \
		grep -v 'file://' | \
    	sed 's/pip-compile.*/update_deps/' > requirements/dev-requirements.in
	@venv/bin/pip-compile --generate-hashes -o requirements/dev-requirements.txt requirements/dev-requirements.in

install-requirements: setup-venv upgrade-pip pip-compile
	@venv/bin/python -m pip install -r requirements/requirements.txt
install-requirements-dev: setup-venv upgrade-pip pip-compile-dev
	@venv/bin/python -m pip install -r requirements/dev-requirements.txt

update-deps: pip-compile pip-compile-dev
update-local-env: install-requirements install-requirements-dev

.PHONY: clean
make clean:  # Removes local env
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
