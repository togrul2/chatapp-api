"""Miscellaneous utils for project."""
from collections.abc import MutableMapping
from typing import Any


class SingletonMeta(type):
    """Metaclass for creating singleton pattern."""

    _instances: MutableMapping[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
