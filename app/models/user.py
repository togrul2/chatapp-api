"""Module with user related models."""
from models.base import Base, CreateTimestampMixin
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

__all__ = ["Friendship", "User"]


class Friendship(CreateTimestampMixin, Base):
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


class User(Base):
    __tablename__ = "user"
    __repr_fields__ = ("id", "username")

    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_picture = Column(String(255))

    chats = relationship(
        "Chat", secondary="membership", back_populates="users"
    )
