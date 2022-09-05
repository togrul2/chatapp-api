"""
db module with database models declaration.
"""
from sqlalchemy import Column, Integer, String

from db import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50), unique=True)
    email = Column(String(50), unique=True)
    password = Column(String)
    profile_picture = Column(String, nullable=True)
