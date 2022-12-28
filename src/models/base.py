"""Base model class and utils."""
from typing import Sequence

from sqlalchemy import Column, DateTime, Integer, func

import db


class Base(db.Base):
    """Base class for models"""

    __abstract__ = True
    __repr_fields__: Sequence[str] = ("id",)

    id = Column(Integer, primary_key=True)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        attrs = ", ".join(
            tuple(
                f"{field}: {getattr(self, field)}"
                for field in self.__repr_fields__
            )
        )
        return f"{__class__.__name__}({attrs})"


class CreateTimestampMixin:
    """
    Mixin for adding created at field to the model.

    Must come before the `Base` class in mro().
    """

    created_at = Column(DateTime, server_default=func.now())


class CreateUpdateTimestampMixin(CreateTimestampMixin):
    """
    Mixin for adding created at and updated at field to the model.

    Must come before the `Base` class in mro().
    """

    modified_at = Column(DateTime, onupdate=func.now())
