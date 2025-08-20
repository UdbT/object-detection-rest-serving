ARG PYTHON_VERSION="3.12"

FROM python:${PYTHON_VERSION}-slim-bookworm AS build
ARG PYTHON_VERSION

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
    build-essential \
    curl \
    gnupg \
    software-properties-common \
    ca-certificates \
    unzip \
    # Get Terraform repository key
    && curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg \
    # Get Node repository key
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /usr/share/keyrings/nodesource.gpg


FROM python:${PYTHON_VERSION}-slim-bookworm
ARG PYTHON_VERSION
ARG POETRY_VERSION="1.8.3"

ARG TERRAFORM_VERSION="1.5.1-1"
ARG CDKTF_VERSION="0.21.0"
ARG NODEJS_VERSION="22"

RUN pip install poetry==${POETRY_VERSION} poetry-dynamic-versioning

COPY --from=build /usr/share/keyrings/hashicorp-archive-keyring.gpg /usr/share/keyrings/hashicorp-archive-keyring.gpg
COPY --from=build /usr/share/keyrings/nodesource.gpg /usr/share/keyrings/nodesource.gpg

RUN apt-get --yes update \
    && apt-get install --no-install-recommends --yes \
    lsb-release \
    && echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list > /dev/null \
    && echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODEJS_VERSION}.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list > /dev/null \
    && apt-get update \
    && apt-get install --no-install-recommends --yes \
    terraform=${TERRAFORM_VERSION} \
    # Install NodeJs
    nodejs \
    # Install CDKTF
    && npm install --global cdktf-cli@${CDKTF_VERSION} \
    # Clean-up
    && apt-get --purge --yes autoremove \
    && rm -rf /var/lib/apt/lists/*
