#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

python << END
import asyncio
import sys
import time

import asyncpg

REASONABLE_WAIT_TIME=30  # in seconds
start = time.time()

async def connect_to_db() -> None:
    sys.stdout.write("Connecting to Postgres database.\n")

    while True:
        try:
            await asyncpg.connect(
                database="${POSTGRES_DB}",
                user="${POSTGRES_USER}",
                password="${POSTGRES_PASSWORD}",
                host="${POSTGRES_HOST}",
                port="${POSTGRES_PORT}",
            )
            sys.stdout.write("Successfully connected to postgres database.\n")
            sys.exit(0)
        except asyncpg.exceptions.CannotConnectNowError:
            sys.stdout.write("Postgres Database system is setting up...\n")
        except ConnectionRefusedError:
            sys.stderr.write("Connection failed, trying again.\n")
            if time.time() - start > REASONABLE_WAIT_TIME:
                sys.stderr.write("Couldn't connect to postgres database within "
                                 "an expected time, something seems to be wrong. "
                                 "Recheck the postgres related env variables.\n")
                time.sleep(1)
                sys.exit(1)


asyncio.run(connect_to_db())

END

exec "$@"
