FROM python:3.9-slim-buster
LABEL maintainer="togrul"

ENV PYTHONUNBUFFERED 1

ARG VIRTUAL_ENV=/venv
ARG WORK_DIR=/src
ARG USERNAME=fastapiuser

# copy files and set workdir & port
COPY ./requirements.txt /tmp/requirements.txt

# install system dependencies
RUN apt-get update && \
    apt-get -y install libpq-dev netcat gcc postgresql && \
    apt-get clean

# install python dependencies
RUN python -m venv ${VIRTUAL_ENV} && \
    ${VIRTUAL_ENV}/bin/pip install --upgrade pip && \
    ${VIRTUAL_ENV}/bin/pip install -r /tmp/requirements.txt && \
    rm -rf /tmp

# adding user for app
RUN adduser --disabled-password --no-create-home ${USERNAME}

COPY . ${WORK_DIR}
WORKDIR ${WORK_DIR}

# set venv python executable as a main one
ENV PATH="${VIRTUAL_ENV}/bin/:$PATH"

# set user
USER ${USERNAME}

EXPOSE 8000
