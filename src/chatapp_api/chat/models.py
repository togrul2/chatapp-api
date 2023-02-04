"""
Module with chat related models.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    and_,
    func,
    select,
)
from sqlalchemy.orm import column_property, relationship

from src.chatapp_api.base.models import CreateTimestampMixin, CustomBase

if TYPE_CHECKING:
    from src.chatapp_api.user.models import User


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

    sender: User = relationship(
        "User", backref="messages", uselist=False, viewonly=True
    )


class Chat(CreateTimestampMixin, CustomBase):
    """Chat model."""

    __tablename__ = "chat"

    # Redefined `id` field for using in column_property
    id = Column(Integer, primary_key=True)
    name = Column(String(150))
    private = Column(Boolean, nullable=False)

    users: list[User] = relationship(
        "User", secondary="membership", back_populates="chats"
    )
    users_count: int = column_property(
        select([func.count(Membership.user_id)])
        .where(Membership.chat_id == id)
        .scalar_subquery(),
        deferred=True,
    )

    messages: list[Message] = relationship("Message", backref="chat")
    last_message_id: int = column_property(
        select(Message.id)
        .where(
            Message.created_at
            == select([func.max(Message.created_at)])
            .where(Message.chat_id == id)
            .correlate_except(Message)
            .scalar_subquery()
        )
        .scalar_subquery(),
        deferred=True,
    )
    last_message_created_at: datetime = column_property(
        select([func.max(Message.created_at)])
        .where(Message.chat_id == id)
        .correlate_except(Message)
        .scalar_subquery()
    )
    last_message: Message = relationship(
        Message,
        primaryjoin=and_(Message.id == last_message_id, Message.chat_id == id),
        uselist=False,
        viewonly=True,
    )
