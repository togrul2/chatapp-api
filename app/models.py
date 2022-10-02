"""
Models module with database models declaration.
"""
from sqlalchemy import (Column, Integer, String, DateTime, func, Boolean,
                        Table, ForeignKey, Text)
from sqlalchemy.orm import relationship

from db import Base

# Here are files that will be imported with asterisk
__all__ = [
    'Membership',
    'Friendship',
    'User',
    'Chat',
    'Message',
]

Membership = Table(
    'membership',
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('chat_id', Integer, ForeignKey('chat.id')),
    Column('accepted', Boolean),
    Column('is_admin', Boolean, default=False, nullable=False),
)

Friendship = Table(
    'friendship',
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('sender_id', Integer, ForeignKey('user.id')),
    Column('receiver_id', Integer, ForeignKey('user.id')),
    Column('accepted', Boolean),
    Column('created_at', DateTime, server_default=func.now())
)


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
        return f"User(id: {self.id}, username: {self.username})"


class Chat(Base):
    """Chat model"""
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
