FROM python:3.9-slim-buster as config
LABEL maintainer="togrul"

ENV PYTHONUNBUFFERED 1

ARG FASTAPI_ENV=dev

ARG USERNAME=fastapi_app
ARG UID=1000
ARG GID=1000

RUN mkdir /app

ENV FASTAPI_ENV=${FASTAPI_ENV} \
    # python
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    # pip:
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    # poetry:
    POETRY_VERSION=1.2.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local'

FROM config as dev-build

RUN apt-get update && \
    apt-get install --no-install-recommends --yes build-essential

RUN apt install -y curl netcat && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python - -y
ENV PATH="${PATH}:/root/.local/bin"

RUN groupadd --gid ${GID} ${USERNAME} && \
    useradd --create-home --gid ${GID} --uid ${UID} ${USERNAME} && \
    chown ${USERNAME} /app

USER ${USERNAME}

COPY pyproject.toml poetry.lock /app

FROM dev-build as python

WORKDIR /app

RUN poetry install --no-root --no-interaction

COPY . /app



COPY * /app/*

ENTRYPOINT ["uvicorn", "main:app"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
