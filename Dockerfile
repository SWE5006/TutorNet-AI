# syntax=docker/dockerfile:1

############################
# Stage 1: builder (wheels)
############################
FROM python:3.12-slim AS builder


RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential gcc \
  && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.2.1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry self add poetry-plugin-export

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

RUN pip wheel --wheel-dir=/wheels -r requirements.txt

COPY . /app


############################
# Stage 2: runtime
############################
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app


COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY . /app

CMD ["/bin/sh", "-c", "gunicorn main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:7000"]
