"""Module with user related models."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.base.models import CustomBase

if TYPE_CHECKING:
    from src.chat.models import Chat


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
