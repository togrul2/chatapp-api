"""
Module with chat related models.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from sqlalchemy import ForeignKey, String, Text, and_, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from src.chatapp_api.base.models import CreateTimestampMixin, CustomBase
from src.chatapp_api.user.models import user_fk

if TYPE_CHECKING:
    from src.chatapp_api.user.models import User

chat_fk = Annotated[
    int, mapped_column(ForeignKey("chat.id", ondelete="cascade"))
]


class Membership(CustomBase):
    """Membership model storing m2m relation between user and chat."""

    __tablename__ = "membership"
    __repr_fields__ = ("id", "user_id", "chat_id")

    user_id: Mapped[user_fk]
    chat_id: Mapped[chat_fk]
    accepted: Mapped[bool | None]
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_owner: Mapped[bool] = mapped_column(default=False)

    user: Mapped[User] = relationship(backref="memberships", viewonly=True)


class Message(CreateTimestampMixin, CustomBase):
    """Message model."""

    __tablename__ = "message"

    body: Mapped[str] = mapped_column(Text, nullable=False)
    sender_id: Mapped[user_fk]
    chat_id: Mapped[chat_fk]

    sender: Mapped[User] = relationship(backref="messages", viewonly=True)


class Chat(CreateTimestampMixin, CustomBase):
    """Chat model."""

    __tablename__ = "chat"

    # Redefined `id` field for using in column_property
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(150))
    private: Mapped[bool]

    users: Mapped[list[User]] = relationship(
        secondary="membership", back_populates="chats"
    )
    messages: Mapped[list[Message]] = relationship(backref="chat")

    users_count: Mapped[int] = column_property(
        select(func.count(Membership.user_id))
        .where(Membership.chat_id == id)
        .scalar_subquery(),
        deferred=True,
    )
    _latest_message_date_query = (
        select(func.max(Message.created_at))
        .where(Message.chat_id == id)
        .correlate_except(Message)
        .scalar_subquery()
    )
    last_message_id: Mapped[int] = column_property(
        select(Message.id)
        .where(Message.created_at == _latest_message_date_query)
        .scalar_subquery(),
        deferred=True,
    )
    last_message_created_at: Mapped[datetime] = column_property(
        select(func.max(Message.created_at))
        .where(Message.chat_id == id)
        .correlate_except(Message)
        .scalar_subquery()
    )
    last_message: Mapped[Message] = relationship(
        primaryjoin=and_(Message.id == last_message_id, Message.chat_id == id),
        uselist=False,
        viewonly=True,
    )
