"""DB services for chat related models & routes."""

from typing import Any

from sqlalchemy import Column
from sqlalchemy.orm import defer, joinedload

from exceptions.base import NotFound
from exceptions.chat import (
    ChatNameTakenException,
    UserNotAdminException,
    UserNotOwnerException,
)
from models.chat import Chat, Membership, Message
from models.user import User
from schemas.base import PaginatedResponse
from schemas.chat import ChatCreate, ChatRead, ChatUpdate, MessageRead
from services.base import CreateUpdateDeleteService, ListMixin


class ChatService(ListMixin, CreateUpdateDeleteService):
    """DB Service for chat model."""

    model = Chat
    user_id: int

    def create(self, schema_dict: dict[str, Any]) -> Chat:
        """Custom create method for chat model."""
        users = schema_dict.pop("users")

        chat = Chat(**schema_dict)

        for user_id in users:
            # TODO: Optimize, bulk create
            chat.users.append(self.session.query(User).get(user_id))

        self.session.add(chat)
        self.session.commit()
        return chat

    def set_user(self, user_id: int) -> None:
        """Setter for `user_id`"""
        self.user_id = user_id

    def _get_private_chat(self, user1_id: int, user2_id: int) -> Chat | None:
        """Returns private chat with given users' ids."""
        if user1_id == user2_id:
            return None

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
        chat = self._get_private_chat(user1_id, user2_id)

        if chat is None:
            self.create({"private": True, "users": [user1_id, user2_id]})

        return chat

    def create_message(
        self, chat_id: int, sender_id: int, body: str
    ) -> Message:
        """Creates message at given chat from
        given sender to given receiver."""
        message = Message(chat_id=chat_id, sender_id=sender_id, body=body)
        self.session.add(message)
        self.session.commit()
        return message

    def get_messages_from_private_chat(
        self, target_id: int
    ) -> PaginatedResponse[MessageRead]:
        """Returns messages from a private chat with a given id."""
        if not self.user_id:
            raise Exception("Set the authenticated user id first")

        chat = self._get_private_chat(self.user_id, target_id)

        if chat is None:
            raise NotFound

        query = (
            self.session.query(Message)
            .options(joinedload(Message.sender), defer("sender_id"))
            .filter(Message.chat_id == chat.id)
            .order_by(Message.created_at.desc())
        )

        if self._paginator:
            return self._paginator.get_paginated_response(query)

        return query.all()

    def _create_membership(
        self, membership_dict: dict[str, Any]
    ) -> Membership:
        """Creates membership based on given schema"""
        membership = Membership(**membership_dict)
        self.session.add(membership)
        self.session.commit()
        return membership

    def _validate_not_null_unique_chat_name(
        self, name: str, chat_id: int | None = None
    ) -> None:
        """Validates whether there are chats with the same name as given one.
        Empty names can be duplicated, so they won't count.
        Also checks whether this name belongs to target chat if it exists.
        If some check fails raises http exception"""
        query = self.session.query(self.model).filter(self.model.name == name)

        if chat_id:
            query.filter(self.model.id != chat_id)

        if query.first() is not None:
            raise ChatNameTakenException

    def all(self) -> PaginatedResponse[ChatRead] | list[ChatRead]:
        """Returns list of all records."""
        query = self.session.query(self.model).filter(
            self.model.private == False  # noqa: E712
        )

        if self._paginator:
            return self._paginator.get_paginated_response(query)

        return query.all()

    def search_public_chats(self, keyword: str):
        """Searches public chat matching the given keyword."""
        expression = keyword + "%"
        query = (
            self.session.query(self.model)
            .filter(self.model.private == False)  # noqa: E712
            .filter(self.model.name.like(expression))
        )

        if self._paginator:
            return self._paginator.get_paginated_response(query)

        return query.all()

    def create_public_chat(self, schema: ChatCreate) -> Chat:
        """Creates chat with membership to a given user."""
        if self.user_id in schema.users:
            schema.users.remove(self.user_id)

        self._validate_not_null_unique_chat_name(schema.name)

        payload = schema.dict()
        payload.update({"private": False})
        chat = self.create(payload)
        self._create_membership(
            {
                "user_id": self.user_id,
                "chat_id": chat.id,
                "is_owner": True,
                "is_admin": True,
                "accepted": True,
            }
        )
        return chat

    def get_public_chat(self, chat_id: int) -> Chat | None:
        """Returns single chat with given id.
        If it does not exists, returns 404 error code."""
        chat = (
            self.session.query(self.model)
            .filter(
                (self.model.id == chat_id)
                & (self.model.private == False)  # noqa: E712
            )
            .first()
        )

        if chat is None:
            raise NotFound

        return chat

    def _check_role(self, chat_id: int, role: Column) -> bool:
        """Returns whether set user has given role in chat or not."""
        query = self.session.query(Membership).filter(
            (Membership.chat_id == chat_id)
            & (Membership.user_id == self.user_id)
            & (role == True)  # noqa: E712
        )
        return query.first() is not None

    def _is_chat_admin(self, chat_id: int) -> bool:
        """Returns whether set user is given chat's admin or not."""
        return self._check_role(chat_id, Membership.is_admin)

    def _is_chat_owner(self, chat_id: int) -> bool:
        """Returns whether set user is given chat's admin or not."""
        return self._check_role(chat_id, Membership.is_owner)

    def update_chat(self, chat_id: int, payload: ChatUpdate) -> Chat | None:
        """Updates chat's information."""
        if not self._is_chat_admin(chat_id):
            raise UserNotAdminException

        return self.update(chat_id, payload.dict())

    def delete_chat(self, chat_id: int) -> None:
        """Deletes public chat with given id.
        If chat doesn't exists, raises 404 http exception."""
        if not self._is_chat_owner(chat_id):
            raise UserNotOwnerException

        self.session.query(Membership).filter(
            Membership.chat_id == chat_id
        ).delete()

        return self.delete(chat_id)
