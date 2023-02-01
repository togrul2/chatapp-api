"""Module with friendship model."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from src.base.models import CreateTimestampMixin

if TYPE_CHECKING:
    from src.user.models import User


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
