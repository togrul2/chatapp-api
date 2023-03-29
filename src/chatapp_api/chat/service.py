"""Service for chat related models & routes."""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TypedDict, cast

from fastapi import HTTPException, status
from jose import JWTError, jwt

from src.chatapp_api.base.exceptions import NotFoundException
from src.chatapp_api.chat.exceptions import (
    BadInviteTokenException,
    ChatNameTakenException,
    UserNotAdminException,
    UserNotMemberException,
    UserNotOwnerException,
)
from src.chatapp_api.chat.models import Chat, Membership, Message
from src.chatapp_api.chat.repository import (
    ChatRepository,
    MembershipRepository,
    MessageRepository,
)
from src.chatapp_api.chat.schemas import MembershipCreate
from src.chatapp_api.config import (
    CHAT_INVITE_LINK_DURATION,
    JWT_ALGORITHM,
    settings,
)
from src.chatapp_api.paginator import Page


class InvitationJWT(TypedDict):
    """Dict with invitation token payload."""

    type: str
    chat_id: int
    expire: str


@dataclass
class ChatService:
    """Chat service with related business logic."""

    chat_repository: ChatRepository
    message_repository: MessageRepository
    membership_repository: MembershipRepository

    async def _create_private_chat(
        self, user_1_id: int, user_2_id: int
    ) -> Chat:
        """Creates private chat for given two users"""
        chat = Chat(private=True)
        self.chat_repository.add(chat)
        await self.chat_repository.flush()
        self.membership_repository.add_all(
            Membership(
                chat_id=chat.id,
                user_id=member_id,
                is_admin=True,
                is_owner=False,
            )
            for member_id in (user_1_id, user_2_id)
        )
        await self.chat_repository.commit()
        return chat

    async def get_or_create_private_chat(
        self, user1_id: int, user2_id: int
    ) -> tuple[Chat, bool]:
        """Returns private chat of given two users and
        boolean indicating whether it was created or not.
        If chat for given user doesn't exist, it will be created."""
        if (
            chat := await self.chat_repository.find_private_chat(
                user1_id, user2_id
            )
        ) is None:
            return (await self._create_private_chat(user1_id, user2_id)), True

        return chat, False

    async def create_message(
        self, chat_id: int, sender_id: int, body: str
    ) -> Message:
        """Creates message at given chat from given sender to given receiver.
        chat_id must be id of an existing chat."""
        message = Message(chat_id=chat_id, sender_id=sender_id, body=body)
        self.message_repository.add(message)
        await self.message_repository.commit()
        return message

    async def list_private_chat_messages(
        self, user_id: int, target_id: int
    ) -> Page:
        """Returns messages from a private chat with a given id."""
        if (
            chat := await self.chat_repository.find_private_chat(
                user_id, target_id
            )
        ) is None:
            raise NotFoundException(
                "Private chat with given user has not been found."
            )

        return await self.message_repository.find_messages_by_private_chat_id(
            chat.id
        )

    async def is_chat_member(self, user_id: int, chat_id: int) -> bool:
        """Returns whether given chat has given user."""
        return (
            await self.membership_repository.find_member_by_chat_and_user_id(
                user_id, chat_id
            )
        ) is not None

    async def is_chat_admin(self, user_id: int, chat_id: int) -> bool:
        """Returns whether given chat has given admin user."""
        membership = (
            await self.membership_repository.find_member_by_chat_and_user_id(
                user_id, chat_id
            )
        )
        return membership is not None and membership.is_admin is True

    async def is_chat_owner(self, user_id: int, chat_id: int) -> bool:
        """Returns whether given chat has given owner user."""
        membership = (
            await self.membership_repository.find_member_by_chat_and_user_id(
                user_id, chat_id
            )
        )
        return membership is not None and membership.is_owner is True

    async def list_chats(self, keyword: str | None = None) -> Page:
        """Returns list of all records.
        If keyword passed returns matching chats only."""
        if keyword:
            return await self.chat_repository.find_all_chats_matching_keyword(
                keyword
            )

        return await self.chat_repository.find_all_chats()

    async def create_public_chat(
        self,
        user_id: int,
        name: str,
        members: Sequence[MembershipCreate],
    ) -> Chat:
        """Creates chat with membership to a given user."""
        if await self.chat_repository.exists_chat_with_name_and_id_not(name):
            raise ChatNameTakenException

        chat = Chat(private=False, name=name)
        self.chat_repository.add(chat)
        await self.chat_repository.flush()
        self.membership_repository.add(
            Membership(
                chat_id=chat.id, user_id=user_id, is_admin=True, is_owner=True
            )
        )
        self.membership_repository.add_all(
            Membership(
                chat_id=chat.id,
                user_id=member.id,
                is_admin=member.is_admin,
            )
            for member in filter(lambda member: member.id != user_id, members)
            # Add all users from members but exclude if owner is there
        )

        await self.chat_repository.commit_or_throw(
            NotFoundException("Nonexistent user passed as a member.")
        )

        return chat

    async def get_public_chat_with_members_count_or_404(
        self, chat_id: int
    ) -> Chat:
        """Returns single row with chat info with given id
        and number of its members. If it does not exist,
        returns 404 error code."""
        chat = await self.chat_repository.find_chat_by_id_with_extra(chat_id)

        if chat is None:
            raise NotFoundException(
                "Public chat with given id has not been found."
            )

        return chat

    async def update_chat(
        self, user_id: int, chat_id: int, name: str | None = None
    ) -> Chat:
        """Updates chat's information."""
        if (chat := await self.chat_repository.find_by_id(chat_id)) is None:
            raise NotFoundException(
                "Public chat with given id has not been found."
            )

        if not await self.is_chat_admin(user_id, chat_id):
            raise UserNotAdminException

        if name:
            chat.name = name

        await self.chat_repository.commit()
        await self.chat_repository.refresh(chat)
        return chat

    async def delete_chat(self, user_id: int, chat_id: int) -> None:
        """Deletes public chat with given id.
        If chat doesn't exist, raises 404 http exception."""
        if not await self.is_chat_owner(user_id, chat_id):
            raise UserNotOwnerException

        if (chat := await self.chat_repository.find_by_id(chat_id)) is None:
            raise NotFoundException

        await self.chat_repository.delete(chat)
        await self.chat_repository.commit()

    def _generate_invite_token(
        self, chat_id: int, expiration_time: int = CHAT_INVITE_LINK_DURATION
    ) -> str:
        """Generates invite token for given chat."""
        expire = datetime.utcnow() + timedelta(seconds=expiration_time)
        payload = {
            "type": "chat-invitation",
            "chat_id": chat_id,
            "expire": expire.isoformat(),
        }
        return jwt.encode(
            payload, settings.secret_key, algorithm=JWT_ALGORITHM
        )

    async def get_invite_link_for_chat(
        self, user_id: int, chat_id: int
    ) -> str:
        """Generates invite link for given group.
        If requesting user is not admin, raises 403 http error."""
        if not await self.is_chat_member(user_id, chat_id):
            raise UserNotAdminException

        return self._generate_invite_token(chat_id)

    async def enroll_user_with_token(
        self, user_id: int, chat_id: int, token: str
    ) -> Membership:
        """Enrolls user to chat. If token cannot be
        parsed or expired or is invalid, 400 http error is raised.
        If user is already in chat, 409 http error is raised."""
        if await self.is_chat_member(user_id, chat_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already enrolled in this chat.",
            )

        try:
            body = cast(
                InvitationJWT,
                jwt.decode(token, settings.secret_key, JWT_ALGORITHM),
            )
        except JWTError as exc:
            raise BadInviteTokenException from exc

        is_chat_invitation_type = body["type"] == "chat-invitation"
        is_expired = datetime.fromisoformat(body["expire"]) > datetime.utcnow()
        is_target_chat = chat_id == body["chat_id"]

        if not all([is_chat_invitation_type, is_expired, is_target_chat]):
            raise BadInviteTokenException

        membership = Membership(
            chat_id=chat_id,
            user_id=user_id,
            is_admin=False,
            is_owner=False,
            accepted=True,
        )
        self.membership_repository.add(membership)
        await self.membership_repository.commit()
        return membership

    async def update_membership(
        self,
        chat_id: int,
        user_id: int,
        target_id: int,
        is_admin: bool | None = None,
    ):
        """Updates chat member's information, his admin, owner status.
        If User is not chat admin raises 403.
        If non owner tries to make someone owner raises 403."""
        if not await self.is_chat_admin(user_id, chat_id):
            raise UserNotAdminException

        membership = (
            await self.membership_repository.find_member_by_chat_and_user_id(
                target_id, chat_id
            )
        )

        if membership is None:
            raise NotFoundException("Member not found.")

        if is_admin:
            membership.is_admin = is_admin

        self.membership_repository.add(membership)
        await self.membership_repository.commit()
        await self.membership_repository.refresh(membership)
        return membership

    async def remove_member(
        self, chat_id: int, user_id: int, target_id: int
    ) -> None:
        """Removes given user from chat. If user is not admin raises 403."""
        if user_id != target_id or not self.is_chat_admin(user_id, chat_id):
            raise UserNotAdminException

        membership = (
            await self.membership_repository.find_member_by_chat_and_user_id(
                target_id, chat_id
            )
        )

        if membership is None:
            raise NotFoundException(
                "Member with given id cannot be found in chat."
            )
        if membership.is_owner is True:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner cannot be removed from group.",
            )

        await self.membership_repository.delete(membership)
        await self.membership_repository.commit()

    async def list_public_chat_messages(
        self, chat_id: int, user_id: int
    ) -> Page:
        """Lists messages from public chat,
        if user is not chat member, raises 403."""
        if not await self.is_chat_member(user_id, chat_id):
            raise UserNotMemberException

        return await self.message_repository.find_messages_by_public_chat_id(
            chat_id
        )

    async def list_chat_members(self, chat_id: int, user_id: int) -> Page:
        """Lists chat members. If given user is not chat member, raises 403."""
        if not await self.is_chat_member(user_id, chat_id):
            raise UserNotMemberException

        return await self.membership_repository.find_members_by_chat_id(
            chat_id
        )

    async def list_user_chats(
        self,
        user_id: int,
        keyword: str | None,
    ) -> Page:
        """Returns target user's chats.
        Sorts them by the date of last message."""
        if keyword:
            return await self.chat_repository.find_chats_by_user_and_keyword(
                user_id, keyword
            )
        return await self.chat_repository.find_chats_by_user(user_id)
