"""Miscellaneous utils for project."""


class SingletonMeta(type):
    """Metaclass for creating singleton pattern."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances.keys():
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
