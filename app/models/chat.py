"""
Module with chat related models.
"""
from models.base import Base, CreateTimestampMixin
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

__all__ = ["Membership", "Chat", "Message"]


class Membership(Base):
    """Membership model storing m2m relation between user and chat."""

    __tablename__ = "membership"
    __repr_fields__ = ("id", "user_id", "chat_id")

    user_id = Column(Integer, ForeignKey("user.id"))
    chat_id = Column(Integer, ForeignKey("chat.id"))
    accepted = Column(Boolean)
    is_admin = Column(Boolean, default=False, nullable=False)


class Chat(CreateTimestampMixin, Base):
    """Chat model."""

    __tablename__ = "chat"

    name = Column(String(150))
    private = Column(Boolean, nullable=False)

    users = relationship(
        "User", secondary="membership", back_populates="chats"
    )
    messages = relationship("Message", backref="chat")


class Message(CreateTimestampMixin, Base):
    """Message model."""

    __tablename__ = "message"

    body = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey("user.id"))
    chat_id = Column(Integer, ForeignKey("chat.id"))
