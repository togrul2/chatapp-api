"""Module with chat related repositories"""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, desc, exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import defer, joinedload, undefer

from src.chatapp_api.base.repository import BaseRepository
from src.chatapp_api.chat.models import Chat, Membership, Message
from src.chatapp_api.paginator import BasePaginator, Page


@dataclass
class ChatRepository(BaseRepository[Chat]):
    """Chat repository class.
    Contains sqlalchemy queries and actions related to chat."""

    paginator: BasePaginator

    async def find_by_id(self, id: int) -> Chat | None:
        """Returns Chat with given id or none if not found."""
        return await self.session.get(Chat, id)

    async def commit_or_throw(self, exception: BaseException) -> None:
        """Commits to database or rollbacks and throws given
        exception if Integrity exception occurs."""
        try:
            await self.commit()
        except IntegrityError as exc:
            await self.rollback()
            raise exception from exc

    async def find_private_chat(
        self, user1_id: int, user2_id: int
    ) -> Chat | None:
        """Returns private chat of two given users."""
        return await self.session.scalar(
            select(Chat).from_statement(
                select(Chat)
                .distinct()
                .join(Membership, Membership.chat_id == Chat.id)
                .where(Membership.user_id == user1_id)
                .intersect(
                    select(Chat)
                    .join(Membership, Membership.chat_id == Chat.id)
                    .where(Membership.user_id == user2_id)
                )
            )
        )

    async def exists_chat_with_name_and_id_not(
        self, name: str, id: int | None = None
    ) -> bool:
        """Returns whether chat with given name exists or not.
        Exludes given id from search."""
        return (
            await self.session.scalar(
                exists().where(and_(Chat.name == name, Chat.id != id)).select()
            )
        ) or False

    async def find_all_chats(self) -> Page[Chat]:
        """Returns all chats from given page."""
        return await self.paginator.get_page_for_model(
            select(Chat)
            .options(undefer(Chat.users_count))
            .where(Chat.private == False)  # noqa: E712
        )

    async def find_all_chats_matching_keyword(
        self, keyword: str
    ) -> Page[Chat]:
        """Returns chats that match keyword."""
        return await self.paginator.get_page_for_model(
            select(Chat)
            .options(undefer(Chat.users_count))
            .where(
                and_(
                    Chat.private == False,  # noqa: E712
                    func.upper(Chat.name).like(f"%{keyword.upper()}%"),
                )
            )
        )

    async def find_chat_by_id_with_extra(self, id: int) -> Chat | None:
        """Returns chats by id with calculated
        with users count and last message.
        Returns None if not found."""
        return await self.session.scalar(
            select(Chat)
            .distinct()
            .options(
                undefer(Chat.users_count),
                joinedload(Chat.last_message),
            )
            .where(Chat.id == id)
        )

    async def find_chats_by_user(self, user_id: int) -> Page[Chat]:
        """Finds chats that given user is enrolled into.
        Orders messages by the date of the last message."""
        return await self.paginator.get_page_for_model(
            select(Chat)
            .distinct()
            .join(Membership, Membership.chat_id == Chat.id)
            .options(
                joinedload(Chat.last_message).joinedload(Message.sender),
            )
            .where(Membership.user_id == user_id)
            .order_by(
                desc(
                    func.coalesce(Chat.last_message_created_at, datetime.min)
                ),
                desc(Chat.last_message_created_at),
            )
        )

    async def find_chats_by_user_and_keyword(
        self, user_id: int, keyword: str
    ) -> Page[Chat]:
        """Finds chats that given user is enrolled into
        and match the given keyword. Orders messages by the
        date of the last message."""
        return await self.paginator.get_page_for_model(
            select(Chat)
            .distinct()
            .join(Membership, Membership.chat_id == Chat.id)
            .options(
                joinedload(Chat.last_message).joinedload(Message.sender),
            )
            .where(
                and_(
                    Membership.user_id == user_id,
                    func.upper(Chat.name).like(f"%{keyword.upper()}%"),
                )
            )
            .order_by(
                desc(
                    func.coalesce(Chat.last_message_created_at, datetime.min)
                ),
                desc(Chat.last_message_created_at),
            )
        )


@dataclass
class MembershipRepository(BaseRepository[Membership]):
    """Repository for membership model."""

    paginator: BasePaginator

    async def find_member_by_chat_and_user_id(
        self, user_id: int, chat_id: int
    ) -> Membership | None:
        """Returns membership from chat or None if not found."""
        return await self.session.scalar(
            select(Membership).where(
                and_(
                    Membership.chat_id == chat_id,
                    Membership.user_id == user_id,
                )
            )
        )

    async def find_members_by_chat_id(self, id: int) -> Page[Membership]:
        """Finds memberships from given chat.
        Joins membership with user entity."""
        return await self.paginator.get_page_for_model(
            select(Membership)
            .distinct()
            .options(joinedload(Membership.user))
            .where(Membership.chat_id == id)
        )


@dataclass
class MessageRepository(BaseRepository[Message]):
    """Repository for message model."""

    paginator: BasePaginator

    async def find_messages_by_private_chat_id(
        self, chat_id: int
    ) -> Page[Message]:
        """Returns messages from private chat.
        Orders by the descending message creation dates."""
        return await self.paginator.get_page_for_model(
            select(Message)
            .distinct()
            .options(joinedload(Message.sender), defer(Message.sender_id))
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
        )

    async def find_messages_by_public_chat_id(
        self, chat_id: int
    ) -> Page[Message]:
        """Returns messages from public chat.
        Orders by the descending message creation dates."""
        return await self.paginator.get_page_for_model(
            select(Message)
            .options(joinedload(Message.sender), defer(Message.sender_id))
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .distinct()
        )
