"""Module with user related models."""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.chatapp_api.base.models import CustomBase

str50 = Annotated[str, mapped_column(String(50))]
str255 = Annotated[str, mapped_column(String(255))]
user_fk = Annotated[
    int, mapped_column(ForeignKey("user.id", ondelete="cascade"))
]


if TYPE_CHECKING:
    from src.chatapp_api.chat.models import Chat


class User(CustomBase):
    """User model for storing user credentials & data."""

    __tablename__ = "user"
    __repr_fields__ = ("id", "username")

    first_name: Mapped[str50 | None]
    last_name: Mapped[str50 | None]
    username: Mapped[str50] = mapped_column(unique=True)
    email: Mapped[str50] = mapped_column(unique=True)
    password: Mapped[str255]
    profile_picture: Mapped[str255 | None]

    chats: Mapped[list[Chat]] = relationship(
        "Chat", secondary="membership", back_populates="users"
    )


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
