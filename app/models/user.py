"""Module with user related models."""
from sqlalchemy import (Column, Integer, String, DateTime, func, Boolean,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relationship

from db import Base


class Friendship(Base):
    __tablename__ = 'friendship'
    __table_args__ = (
        UniqueConstraint('sender_id', 'receiver_id',
                         name='unique_sender_receiver'),
    )

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('user.id'))
    receiver_id = Column(Integer, ForeignKey('user.id'))
    accepted = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return (f'Friendship(id: {self.id}, '
                f'sender: {self.sender_id}, '
                f'receiver: {self.receiver_id})')


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50), unique=True)
    email = Column(String(50), unique=True)
    password = Column(String(255))
    profile_picture = Column(String(255))

    chats = relationship('Chat', secondary='membership',
                         back_populates='users')

    def __repr__(self):
        return f'User(id: {self.id}, username: {self.username})'
