ARG PYTHON_VERSION="3.12"

FROM python:${PYTHON_VERSION}-slim-bullseye AS builder
ARG PYTHON_VERSION
ARG POETRY_VERSION="1.8.3"

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
    build-essential \
    && pip install poetry==${POETRY_VERSION} poetry-dynamic-versioning \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root

COPY poetry.lock pyproject.toml ./

RUN pip install --upgrade pip==24.* setuptools==70.* wheel==0.43.* && \
    poetry config virtualenvs.create false && \
    poetry install --without dev --no-cache && \
    poetry run pip cache purge && \
    rm -rf ~/.cache/pypoetry/artifacts


FROM python:${PYTHON_VERSION}-slim-bullseye AS dev
ARG PYTHON_VERSION
WORKDIR /root

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Only copy necessary files from builder
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY configs/ configs/
COPY src/ src/
COPY resources/ resources/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "warning", "--reload"]