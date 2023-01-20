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


class ParsedDBUrl(TypedDict):
    """Typed dict with keys of parsed url."""

    hostname: str
    port: int
    user: str | None
    password: str | None
    dbname: str


def parse_url(url: str) -> ParsedDBUrl:
    """Parses url and returns parameters from it."""
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

    return {
        "hostname": hostname,
        "port": port,
        "user": user,
        "password": password,
        "dbname": dbname,
    }
