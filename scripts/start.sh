#!/bin/bash

cd /app
poetry run alembic upgrade head

poetry run uvicorn src.main:app \
       --reload \
       --workers 1 \
       --host 0.0.0.0 \
       --port 8000
