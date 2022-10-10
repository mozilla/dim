FROM python:3.10.7-slim-buster AS base

LABEL maintainer="kignasiak@mozilla.com"

WORKDIR /dim_app

RUN apt-get update && \
    apt-get install -y --no-install-recommends wkhtmltopdf && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app
WORKDIR /app
ENV PYTHONPATH "${PYTHONPATH}:/app"
COPY . .

RUN python -m pip install --no-cache-dir .

ENTRYPOINT ["dim"]
CMD ["run"]
