"""Module with friendship model."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from src.chatapp_api.base.models import CreateTimestampMixin
from src.chatapp_api.user.models import user_fk

if TYPE_CHECKING:
    from src.chatapp_api.user.models import User


class Friendship(CreateTimestampMixin):
    """Friendship model for storing relations between users."""

    __tablename__ = "friendship"
    __table_args__ = (
        UniqueConstraint(
            "sender_id", "receiver_id", name="unique_sender_receiver"
        ),
    )
    __repr_fields__ = ("id", "sender_id", "receiver_id")

    sender_id: Mapped[user_fk]
    receiver_id: Mapped[user_fk]
    accepted: Mapped[bool | None]

    sender: Mapped[User] = relationship(foreign_keys="Friendship.sender_id")
