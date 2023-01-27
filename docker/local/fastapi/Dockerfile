FROM python:3.10-slim-buster
LABEL maintainer="togrul"

ARG USERNAME=fastapi_user
ARG GROUPNAME=fastapi_group
ARG UID=1000
ARG GID=1000

ENV \
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
    POETRY_VERSION=1.3.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local'

# Install ubuntu dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends --yes build-essential

# Install curl & poetry
RUN apt install -y curl netcat && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python - -y

# Set PATH variable
ENV PATH="${PATH}:/root/.local/bin"

# Create custom user
RUN groupadd --gid $GID $GROUPNAME && \
    useradd --create-home --gid $GID --uid $UID $USERNAME

# Set working directory
WORKDIR /app

# Copy poetry related files
COPY pyproject.toml poetry.lock /app/

# Install poetry dependencies
RUN poetry install --no-root --no-interaction

# Copy scripts
COPY --chown=$USERNAME:$GROUPNAME \
    --chmod=+x \
    ./scripts/start.sh /start

COPY --chown=$USERNAME:$GROUPNAME \
    --chmod=+x \
    ./scripts/wait_for_db.sh /wait_for_db

# Copy rest of files
COPY --chown=$USERNAME:$GROUPNAME . /app

USER $USERNAME

# Entrypoint command
ENTRYPOINT ["/wait_for_db"]
