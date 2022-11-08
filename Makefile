.DEFAULT_GOAL := help

IMAGE_REPO	   := gcr.io/data-monitoring-dev
IMAGE_BASE     := dim
IMAGE_VERSION  := latest-app
IMAGE_NAME     := $(IMAGE_BASE):$(IMAGE_VERSION)
IMAGE_TARGET   := app

CONTAINER_NAME := $(IMAGE_BASE)

.PHONY: build
build-app: ## Builds final app Docker image
	@docker build -t ${IMAGE_BASE}:${IMAGE_VERSION} --target=${IMAGE_TARGET} -f Dockerfile .

build-test: ## Builds test Docker image containing all dev requirements
	@docker build -t ${IMAGE_BASE}:latest-test --target=test -f Dockerfile .

image: build-app

build: update pytest image

.PHONY: test
test-unit: build-test ## Builds test Docker image and executes Python tests
	@docker run ${IMAGE_BASE}:latest-test python -m pytest tests/

test-black: build-test
	@docker run ${IMAGE_BASE}:latest-test python -m black --check dim/ tests/

test-flake8: build-test
	@docker run ${IMAGE_BASE}:latest-test python -m flake8 dim/ tests/

test-isort: build-test
	@docker run ${IMAGE_BASE}:latest-test python -m isort --check dim/ tests/

test-mypy: build-test
	@docker run ${IMAGE_BASE}:latest-test python -m mypy dim/ tests/

test-all: build-test test-unit test-flake8 test-isort test-black #test-mypy

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
