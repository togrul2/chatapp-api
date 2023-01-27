"""Module with user related models."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.models.base import CreateTimestampMixin, CustomBase

__all__ = ["Friendship", "User", "Block"]


if TYPE_CHECKING:
    # if the target of the relationship is in another module
    # that cannot normally be imported at runtime
    from src.models.chat import Chat


class User(CustomBase):
    """User model for storing user credentials & data."""

    __tablename__ = "user"
    __repr_fields__ = ("id", "username")

    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_picture = Column(String(255))

    chats: list[Chat] = relationship(
        "Chat", secondary="membership", back_populates="users"
    )


class Friendship(CreateTimestampMixin):
    """Friendship model for storing relations between users."""

    __tablename__ = "friendship"
    __table_args__ = (
        UniqueConstraint(
            "sender_id", "receiver_id", name="unique_sender_receiver"
        ),
    )
    __repr_fields__ = ("id", "sender_id", "receiver_id")

    sender_id = Column(Integer, ForeignKey("user.id"))
    receiver_id = Column(Integer, ForeignKey("user.id"))
    accepted = Column(Boolean)

    sender: User = relationship("User", foreign_keys="Friendship.sender_id")


class Block(CustomBase):
    """Block model for recording blocked users."""

    __tablename__ = "block"
    __table_args__ = (
        UniqueConstraint(
            "blocker_id", "blocked_id", name="unique_blocker_blocked_id"
        ),
    )
    __repr_fields__ = ("id", "blocker_id", "blocked_id")

    blocker_id = Column(Integer, ForeignKey("user.id"))
    blocked_id = Column(Integer, ForeignKey("user.id"))

    blocked_user: User = relationship("User", foreign_keys="Block.blocked_id")
