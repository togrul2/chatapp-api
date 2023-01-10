"""Miscellaneous utils for project."""
import re
from collections.abc import MutableMapping
from typing import Any
from urllib import parse


class SingletonMeta(type):
    """Metaclass for creating singleton pattern."""

    _instances: MutableMapping[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def split_path(path: str) -> list[str]:
    """Splits path by `/` or `\\`. Basically universal
    full path splitter for both windows and unix like systems.

    Example:
        >>> split_path('C:\\Windows\\Temp\\some_file.txt')
        ['C:', 'Windows', 'Temp', 'some_file.txt']

        >>> split_path('/tmp/some_file.txt')
        ['tmp', 'some_file.txt']
    """
    return list(filter(None, re.split("[/\\\\]", path)))


def split_filename(file: str) -> tuple[str, str]:
    """Splits filename into name and extension part.

    Example:
        >>> split_filename("hello.py")
        ('hello', 'py')

        >>> split_filename("hello.world.py")
        ('hello.world', 'py')

        >>> split_filename(".gitignore")
        ('.gitignore',)
    """
    filename, ext = file.rsplit(".", 1)

    if not (filename and ext):
        return (file,)

    return filename, ext


def parse_url(url: str) -> dict[str, str]:
    """Parses url and returns parameters from it.

    Example:
        >>> URL = 'postgresql+psycopg2://someuser:somepassword@localhost:5432/somedb'  # noqa
        >>> parse_url(URL)
        {'hostname': 'localhost', 'port': 5432, 'user': 'someuser', 'password': 'somepassword', 'dbname': 'somedb'}

    """

    params = parse.urlparse(url)
    return {
        "hostname": params.hostname,
        "port": params.port,
        "user": params.username,
        "password": params.password,
        "dbname": params.path[1:],
    }
