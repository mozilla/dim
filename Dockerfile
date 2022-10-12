FROM python:3.10.7-slim-buster AS base

LABEL maintainer="kignasiak@mozilla.com"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        make \
        wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY requirements/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY dim/ dim

# test stage used for running tests only
FROM base AS test

COPY requirements/dev-requirements.txt /tmp/dev-requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/dev-requirements.txt \
    && rm /tmp/dev-requirements.txt

COPY tests/ tests

# final stage for running in prod
FROM base AS app

COPY pyproject.toml .
RUN python -m pip install --no-cache-dir .

ENTRYPOINT ["dim"]
CMD ["run"]
