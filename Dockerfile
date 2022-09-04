FROM python:3.9-slim-buster
LABEL maintainer="togrul"

ENV PYTHONUNBUFFERED 1

# copy files and set workdir & port
COPY ./requirements.txt /tmp/requirements.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

# install system dependencies
RUN apt-get update && \
    apt-get -y install libpq-dev netcat gcc postgresql && \
    apt-get clean

# install python dependencies
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    rm -rf /tmp

# adding user for app
RUN adduser \
    --disabled-password \
    --no-create-home \
    fastapiuser

ENV PATH="/py/bin/:$PATH"
USER fastapiuser
