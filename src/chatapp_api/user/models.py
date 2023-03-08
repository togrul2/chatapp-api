"""Module with user related models."""
from __future__ import annotations

from typing import Annotated

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.chatapp_api.base.models import CustomBase

str50 = Annotated[str, 50]
str255 = Annotated[str, 255]
user_fk = Annotated[
    int, mapped_column(ForeignKey("user.id", ondelete="cascade"))
]


class User(CustomBase):
    """User model for storing user credentials & data."""

    __tablename__ = "user"
    __repr_fields__ = ("id", "username")

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str50 | None]
    last_name: Mapped[str50 | None]
    username: Mapped[str50] = mapped_column(unique=True, nullable=False)
    email: Mapped[str50] = mapped_column(unique=True, nullable=False)
    password: Mapped[str255]
    profile_picture: Mapped[str255 | None]


class Block(CustomBase):
    """Block model for recording blocked users."""

    __tablename__ = "block"
    __table_args__ = (
        UniqueConstraint(
            "blocker_id", "blocked_id", name="unique_blocker_blocked_id"
        ),
    )
    __repr_fields__ = ("id", "blocker_id", "blocked_id")

    blocker_id: Mapped[user_fk]
    blocked_id: Mapped[user_fk]

    blocked_user: Mapped[User] = relationship(foreign_keys="Block.blocked_id")

    def __str__(self):
        return f"User(id={self.blocker_id}) blocked Used({self.blocked_user})"
