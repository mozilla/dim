FROM python:3.10.7-slim

LABEL maintainer="kignasiak@mozilla.com"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        make \
        wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY requirements/ /tmp/.
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt \
    && python -m pip install --no-cache-dir -r /tmp/dev-requirements.txt \
    && rm /tmp/dev-requirements.txt

COPY pyproject.toml .
COPY dim/ dim
RUN python -m pip install --no-cache-dir .

COPY dim_checks/ dim_checks
COPY tests/ tests
