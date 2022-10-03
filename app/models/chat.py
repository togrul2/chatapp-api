"""
Module with chat related models.
"""
from sqlalchemy import (Integer, Column, ForeignKey, Boolean, DateTime,
                        String, func, Text)
from sqlalchemy.orm import relationship

from db import Base


class Membership(Base):
    __tablename__ = 'membership'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    chat_id = Column(Integer, ForeignKey('chat.id'))
    accepted = Column(Boolean)
    is_admin = Column(Boolean, default=False, nullable=False)


class Chat(Base):
    """Chat model."""
    __tablename__ = 'chat'
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    name = Column(String(150))
    private = Column(Boolean, nullable=False)

    users = relationship('User', secondary='membership',
                         back_populates='chats')
    messages = relationship('Message', backref='chat')


class Message(Base):
    """Message model."""
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True, index=True)
    body = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey('user.id'))
    chat_id = Column(Integer, ForeignKey('chat.id'))
    created_at = Column(DateTime, server_default=func.now())
