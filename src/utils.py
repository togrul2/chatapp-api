"""Miscellaneous utils for project."""
import re
from collections.abc import Sequence
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


def parse_url(url: str) -> dict[str, str]:
    """Parses url and returns parameters from it."""

    params = parse.urlparse(url)
    return {
        "hostname": params.hostname,
        "port": params.port,
        "user": params.username,
        "password": params.password,
        "dbname": params.path[1:],
    }
