"""
Module with chat related models.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.models.base import CreateTimestampMixin, CustomBase

__all__ = ["Membership", "Chat", "Message"]

if TYPE_CHECKING:
    from src.models.user import User


class Membership(CustomBase):
    """Membership model storing m2m relation between user and chat."""

    __tablename__ = "membership"
    __repr_fields__ = ("id", "user_id", "chat_id")

    user_id = Column(Integer, ForeignKey("user.id"))
    chat_id = Column(Integer, ForeignKey("chat.id"))
    accepted = Column(Boolean)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_owner = Column(Boolean, default=False, nullable=False)


class Message(CreateTimestampMixin, CustomBase):
    """Message model."""

    __tablename__ = "message"

    body = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey("user.id"))
    chat_id = Column(Integer, ForeignKey("chat.id"))

    sender: list[User] = relationship("User", backref="messages")


class Chat(CreateTimestampMixin, CustomBase):
    """Chat model."""

    __tablename__ = "chat"

    name = Column(String(150))
    private = Column(Boolean, nullable=False)

    users: list[User] = relationship(
        "User", secondary="membership", back_populates="chats"
    )
    messages: list[Message] = relationship("Message", backref="chat")
