"""
Module with chat related models.
"""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session, relationship

from src.models.base import Base, CreateTimestampMixin

__all__ = ["Membership", "Chat", "Message"]


class Membership(Base):
    """Membership model storing m2m relation between user and chat."""

    __tablename__ = "membership"
    __repr_fields__ = ("id", "user_id", "chat_id")

    user_id = Column(Integer, ForeignKey("user.id"))
    chat_id = Column(Integer, ForeignKey("chat.id"))
    accepted = Column(Boolean)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_owner = Column(Boolean, default=False, nullable=False)


class Chat(CreateTimestampMixin, Base):
    """Chat model."""

    __tablename__ = "chat"

    name = Column(String(150))
    private = Column(Boolean, nullable=False)

    users = relationship(
        "User", secondary="membership", back_populates="chats"
    )
    messages = relationship("Message", backref="chat")

    @hybrid_property
    def number_of_members(self):
        """Returns count of members in chat"""
        return (
            object_session(self)
            .query(Membership)
            .filter(Membership.chat_id == self.id)
            .count()
        )


class Message(CreateTimestampMixin, Base):
    """Message model."""

    __tablename__ = "message"

    body = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey("user.id"))
    chat_id = Column(Integer, ForeignKey("chat.id"))

    sender = relationship("User", backref="messages")
