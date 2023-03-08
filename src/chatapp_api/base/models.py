"""Base model class and utils."""
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# from typing import Annotated


# int_pk = Annotated[int, mapped_column(primary_key=True)]


class CustomBase(DeclarativeBase):
    """Base class for models"""

    __abstract__ = True
    __repr_fields__: tuple[str, ...] = ("id",)

    id: Mapped[int] = mapped_column(primary_key=True)
    # id: Mapped[int_pk]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        attrs = ", ".join(
            f"{field}: {getattr(self, field)}"
            for field in self.__repr_fields__
        )
        return f"{self.__class__.__name__}({attrs})"


class CreateTimestampMixin(CustomBase):
    """
    Mixin for adding created at field to the model.

    Must come before the `Base` class in mro().
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class CreateUpdateTimestampMixin(CreateTimestampMixin):
    """
    Mixin for adding created at and updated at field to the model.

    Must come before the `Base` class in mro().
    """

    __abstract__ = True

    modified_at: Mapped[datetime | None] = mapped_column(onupdate=func.now())
