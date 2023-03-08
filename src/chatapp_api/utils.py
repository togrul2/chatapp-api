"""Miscellaneous utils for project."""
import re
from collections.abc import Sequence
from typing import TypedDict
from urllib import parse


def split_path(path: str) -> Sequence[str]:
    """Splits path by `/` or `\\`. Basically universal
    full path splitter for both windows and unix like systems.
    """
    return tuple(filter(None, re.split("[/\\\\]", path)))


def split_filename(file: str) -> tuple[str, str]:
    """Splits filename into name and extension part."""
    filename, ext = file.rsplit(".", 1)

    if not (filename and ext):
        return file, "."

    return filename, ext


class ParsedRDBUrl(TypedDict):
    """Typed dict with keys of parsed url of relational database."""

    hostname: str
    port: int
    user: str
    password: str
    dbname: str


class ParsedMessageBrokerUrl(TypedDict):
    """Typed dict with keys of parsed url of message broker."""

    hostname: str
    port: int
    db: int


def parse_rdb_url(url: str) -> ParsedRDBUrl:
    """Parses relational database url and returns parameters from it."""
    params = parse.urlparse(url)

    hostname = params.hostname
    port = params.port
    user = params.username
    password = params.password
    dbname = params.path[1:]

    if not hostname:
        raise ValueError("Invalid hostname, make sure passed url is correct.")

    if not port:
        raise ValueError("Invalid port, make sure passed url is correct.")

    if not user:
        raise ValueError("Invalid user, make sure passed url is correct.")

    if not password:
        raise ValueError("Invalid password, make sure passed url is correct.")

    return {
        "hostname": hostname,
        "port": port,
        "user": user,
        "password": password,
        "dbname": dbname,
    }


def parse_message_broker_url(url: str) -> ParsedMessageBrokerUrl:
    """Parses message broker url and returns parameters from it."""
    params = parse.urlparse(url)

    hostname = params.hostname
    port = params.port
    db = params.path[1:]

    if not hostname:
        raise ValueError("Invalid hostname, make sure passed url is correct.")

    if not port:
        raise ValueError("Invalid port, make sure passed url is correct.")

    if not db.isnumeric():
        raise ValueError("Invalid db number, must be numeric")

    return {"hostname": hostname, "port": port, "db": int(db)}
