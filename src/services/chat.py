"""DB services for chat related models & routes."""

from typing import Optional

from sqlalchemy.orm import defer, joinedload

from models.chat import Chat, Membership, Message
from models.user import User
from schemas.chat import ChatCreate
from services.base import CreateUpdateDeleteService


class ChatService(CreateUpdateDeleteService):
    """DB Service for chat model."""

    model = Chat
    user_id: int

    def create(self, schema: ChatCreate) -> Chat:
        """Custom create method for chat model."""
        schema_dict = schema.dict()
        users = schema_dict.pop("users")

        chat = Chat(**schema_dict)

        for user_id in users:
            chat.users.append(self.session.query(User).get(user_id))

        self.session.add(chat)
        self.session.commit()
        return chat

    def set_user(self, user_id: int):
        """Setter for `user_id`"""
        self.user_id = user_id

    def _get_chat(self, user1_id: int, user2_id: int) -> Optional[Chat]:
        """Returns private chat with given users' ids."""
        return (
            self.session.query(self.model)
            .filter(
                (Membership.chat_id == self.model.id)
                & (Membership.user_id == user1_id)
            )
            .intersect(
                self.session.query(self.model).filter(
                    (Membership.chat_id == self.model.id)
                    & (Membership.user_id == user2_id)
                )
            )
            .first()
        )

    def get_or_create_private_chat(self, user1_id: int, user2_id: int) -> Chat:
        """Returns private chat of given two users.
        If it doesn't exist, creates it."""
        chat = self._get_chat(user1_id, user2_id)

        if chat is None:
            self.create(
                ChatCreate.construct(private=True, users=[user1_id, user2_id])
            )

        return chat

    def create_message(self, chat_id: int, sender_id: int, body: str):
        """Creates message at given chat from
        given sender to given receiver."""
        message = Message(chat_id=chat_id, sender_id=sender_id, body=body)
        self.session.add(message)
        self.session.commit()
        return message

    def get_messages_with_user(self, target_id: int):
        """Returns messages with given user."""
        if not self.user_id:
            raise Exception("Set the authenticated user id first")

        chat = self._get_chat(self.user_id, target_id)
        query = (
            self.session.query(Message)
            .options(joinedload(Message.sender), defer("sender_id"))
            .filter(Message.chat_id == chat.id)
        )

        if self._paginator:
            return self._paginator.get_paginated_response(query)

        return query.all()
