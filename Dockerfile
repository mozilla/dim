FROM python:3.10.7-slim-buster AS base

LABEL maintainer="kignasiak@mozilla.com"

WORKDIR /dim_app

COPY requirements/requirements.in /tmp/requirements.in
RUN python -m pip install --no-cache-dir -r /tmp/requirements.in \
    && rm /tmp/requirements.in

COPY dim/[^test]* dim

# test staged used for running tests only
FROM base AS test

COPY requirements/dev-requirements.in /tmp/dev-requirements.in
RUN python -m pip install --no-cache-dir -r /tmp/dev-requirements.in \
    && rm /tmp/dev-requirements.in

COPY dim/tests dim/tests

# final stage for running in prod
FROM base AS app
