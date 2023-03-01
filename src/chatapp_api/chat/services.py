"""DB services for chat related models & routes."""
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any, TypedDict, cast

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import Column, and_, delete, desc, exists, func, select
from sqlalchemy.engine import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload, undefer
from typing_extensions import NotRequired

from src.chatapp_api.base import services as base_services
from src.chatapp_api.base.exceptions import NotFoundException
from src.chatapp_api.chat.exceptions import (
    BadInviteTokenException,
    ChatNameTakenException,
    UserNotAdminException,
    UserNotMemberException,
    UserNotOwnerException,
)
from src.chatapp_api.chat.models import Chat, Membership, Message
from src.chatapp_api.chat.schemas import ChatCreate, ChatUpdate
from src.chatapp_api.config import (
    CHAT_INVITE_LINK_DURATION,
    JWT_ALGORITHM,
    settings,
)
from src.chatapp_api.paginator import BasePaginator, PaginatedResponseDict


class MemberCreateDict(TypedDict):
    id: int
    is_admin: bool


class ChatCreateDict(TypedDict):
    private: bool
    users: list[MemberCreateDict]
    name: NotRequired[str]


class InvitationJWT(TypedDict):
    type: str
    chat_id: int
    expire: str


async def _create_chat(
    session: AsyncSession,
    schema_dict: ChatCreateDict,
    user_id: int | None = None,
) -> Chat:
    """Custom create method for chat model."""
    users = list(
        filter(lambda user: user["id"] != user_id, schema_dict["users"])
    )
    chat = await base_services.create(
        session,
        Chat(
            private=schema_dict["private"], name=schema_dict.get("name", None)
        ),
        commit=False,
        flush=True,
    )

    if user_id is not None:
        await base_services.create(
            session,
            Membership(
                user_id=user_id,
                chat_id=chat.id,
                is_owner=True,
                is_admin=True,
                accepted=True,
            ),
            commit=False,
        )

    # TODO: Remove error, instead ignore missing users
    for user_dict in users:
        try:
            await base_services.create(
                session,
                Membership(
                    chat_id=chat.id,
                    user_id=user_dict["id"],
                    is_admin=user_dict["is_admin"],
                    is_owner=False,
                    accepted=True,
                ),
                commit=False,
                flush=True,
            )

        except IntegrityError as exc:
            await session.rollback()
            raise NotFoundException(
                f"User with id of {user_dict['id']} does not exist."
            ) from exc

    await session.commit()
    return chat


async def _get_private_chat(
    session: AsyncSession, user_id: int, target_id: int
) -> Chat | None:
    """Returns private chat with given users' ids."""
    if user_id == target_id:
        return None

    query = select(Chat).from_statement(
        select(Chat)
        .join(Membership, Membership.chat_id == Chat.id)
        .where(Membership.user_id == user_id)
        .intersect(
            select(Chat)
            .join(Membership, Membership.chat_id == Chat.id)
            .where(Membership.user_id == target_id)
        )
    )
    return await session.scalar(query)


async def get_or_create_private_chat(
    session: AsyncSession, user1_id: int, user2_id: int
) -> tuple[Chat, bool]:
    """Returns private chat of given two users and
    boolean indicating whether it was created or not.
    If chat for given user doesn't exist, it will be created."""
    chat = await _get_private_chat(session, user1_id, user2_id)

    if chat is None:
        return (
            await _create_chat(
                session,
                {
                    "private": True,
                    "users": [
                        {"id": user1_id, "is_admin": True},
                        {"id": user2_id, "is_admin": True},
                    ],
                },
            )
        ), True

    return chat, False


async def create_message(
    session: AsyncSession, chat_id: int, sender_id: int, body: str
) -> Message:
    """Creates message at given chat from
    given sender to given receiver."""
    return await base_services.create(
        session, Message(chat_id=chat_id, sender_id=sender_id, body=body)
    )


async def list_private_chat_messages(
    session: AsyncSession,
    user_id: int,
    target_id: int,
    paginator: BasePaginator | None = None,
) -> Sequence[Message] | PaginatedResponseDict:
    """Returns messages from a private chat with a given id."""
    if (chat := await _get_private_chat(session, user_id, target_id)) is None:
        raise NotFoundException(
            "Private chat with given user has not been found."
        )

    query = (
        select(Message)
        .options(joinedload(Message.sender), defer("sender_id"))
        .where(Message.chat_id == chat.id)
        .order_by(cast(Column, Message.created_at).desc())
    )

    if paginator:
        return await paginator.get_paginated_response_for_model(query)

    return (await session.scalars(query)).all()


async def _validate_not_null_unique_chat_name(
    session: AsyncSession, name: str, chat_id: int | None = None
) -> None:
    """Validates whether there are chats with the same name as given one.
    Empty names can be duplicated, so they won't count.
    Also checks whether this name belongs to target chat if it exists.
    If some check fails raises http exception"""
    matching_chat: bool = await session.scalar(
        exists().where(and_(Chat.name == name, Chat.id != chat_id)).select()
    )

    if matching_chat:
        raise ChatNameTakenException


async def list_chats(
    session: AsyncSession,
    paginator: BasePaginator | None = None,
    keyword: str | None = None,
) -> Sequence[Row] | PaginatedResponseDict:
    """Returns list of all records.
    If keyword passed returns matching chats only."""
    query = (
        select(Chat)
        .options(undefer(Chat.users_count))
        .where(Chat.private == False)  # noqa: E712
    )

    if keyword:
        expression = keyword.upper() + "%"
        query = query.where(func.upper(Chat.name).like(expression))

    if paginator:
        return await paginator.get_paginated_response_for_model(query)

    return (await session.execute(query)).all()


async def create_public_chat(
    session: AsyncSession, user_id: int, schema: ChatCreate
) -> Row:
    """Creates chat with membership to a given user."""
    await _validate_not_null_unique_chat_name(session, schema.name)
    chat = await _create_chat(
        session,
        cast(ChatCreateDict, {**schema.dict(), "private": False}),
        user_id,
    )

    return (
        await session.execute(
            select(
                Chat.id,
                Chat.name,
                Chat.created_at,
                func.count(Membership.id).label("members"),
            )
            .join(Membership, Membership.chat_id == Chat.id)
            .where(Chat.id == chat.id)
            .group_by(Chat.id)
        )
    ).one()


async def get_public_chat_or_404(session: AsyncSession, chat_id: int) -> Chat:
    """Returns single row with chat info with given id.
    If it does not exist, returns 404 error code."""
    chat = await session.get(Chat, chat_id)

    if chat is None:
        raise NotFoundException(
            "Public chat with given id has not been found."
        )

    return chat


async def get_public_chat_with_members_or_404(
    session: AsyncSession, chat_id: int
) -> Row:
    """Returns single row with chat info with given id
    and number of its members. If it does not exist,
    returns 404 error code."""
    chat = await session.scalar(
        select(Chat)
        .options(
            undefer(Chat.users_count),
            joinedload(Chat.last_message),
        )
        .where(Chat.id == chat_id)
    )

    if chat is None:
        raise NotFoundException(
            "Public chat with given id has not been found."
        )

    return chat


async def _check_chat_member(
    session: AsyncSession,
    user_id: int,
    chat_id: int,
    role: bool | None = None,
) -> bool:
    """Returns whether set user is member of chat and
    has given role(optional) or not."""
    query = exists().where(
        and_(Membership.chat_id == chat_id, Membership.user_id == user_id)
    )

    if role:
        query = query.where(role == True)  # noqa: E712

    return (await session.scalar(query.select())) or 0


async def _is_chat_admin(
    session: AsyncSession, user_id: int, chat_id: int
) -> bool:
    """Returns whether given user is chat's admin or not."""
    return await _check_chat_member(
        session, user_id, chat_id, Membership.is_admin
    )


async def _is_chat_owner(
    session: AsyncSession, user_id: int, chat_id: int
) -> bool:
    """Returns whether given user is chat's admin or not."""
    return await _check_chat_member(
        session, user_id, chat_id, Membership.is_owner
    )


async def is_chat_member(
    session: AsyncSession, user_id: int, chat_id: int
) -> bool:
    """Returns whether given user is chat's member or not."""
    return await _check_chat_member(session, user_id, chat_id)


async def update_chat(
    session: AsyncSession, user_id: int, chat_id: int, payload: ChatUpdate
) -> Chat:
    """Updates chat's information."""
    chat = await get_public_chat_or_404(session, chat_id)

    if not await _is_chat_admin(session, user_id, chat_id):
        raise UserNotAdminException

    return await base_services.update(session, chat, payload.dict())


async def delete_chat(
    session: AsyncSession, user_id: int, chat_id: int
) -> None:
    """Deletes public chat with given id.
    If chat doesn't exist, raises 404 http exception."""
    chat = await get_public_chat_with_members_or_404(session, chat_id)

    if not await _is_chat_owner(session, user_id, chat_id):
        raise UserNotOwnerException

    await session.execute(
        delete(Membership).where(Membership.chat_id == chat.id)
    )
    await session.execute(delete(Chat).where(Chat.id == chat.id))
    await session.commit()


def _generate_invite_token(
    chat_id: int, expiration_time: int = CHAT_INVITE_LINK_DURATION
) -> str:
    """Generates invite token for given chat."""
    expire = datetime.utcnow() + timedelta(seconds=expiration_time)
    payload = {
        "type": "chat-invitation",
        "chat_id": chat_id,
        "expire": expire.isoformat(),
    }
    encoded_jwt = jwt.encode(
        payload, settings.secret_key, algorithm=JWT_ALGORITHM
    )
    return encoded_jwt


async def get_invite_link_for_chat(
    session: AsyncSession, user_id: int, chat_id: int
) -> str:
    """Generates invite link for given group.
    If requesting user is not admin, raises 403 http error."""
    if not await _is_chat_admin(session, user_id, chat_id):
        raise UserNotAdminException

    return _generate_invite_token(chat_id)


async def enroll_user_with_token(
    session: AsyncSession, user_id: int, chat_id: int, token: str
) -> Membership:
    """Enrolls user to chat. If token cannot be
    parsed or expired or is invalid, 400 http error is raised.
    If user is already in chat, 409 http error is raised."""
    if await session.scalar(
        exists()
        .where(
            and_(Membership.user_id == user_id, Membership.chat_id == chat_id)
        )
        .select()
    ):
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

    if not (is_chat_invitation_type and is_expired and is_target_chat):
        raise BadInviteTokenException

    return await base_services.create(
        session,
        Membership(
            chat_id=chat_id,
            user_id=user_id,
            is_admin=False,
            is_owner=False,
            accepted=True,
        ),
    )


async def update_membership(
    session: AsyncSession,
    chat_id: int,
    user_id: int,
    target_id: int,
    payload: Mapping[str, Any],
):
    """Updates chat member's information, his admin, owner status.
    If User is not chat admin raises 403.
    If non owner tries to make someone owner raises 403."""
    if not await _is_chat_admin(session, user_id, chat_id):
        raise UserNotAdminException

    membership = await session.scalar(
        select(Membership).where(
            and_(
                Membership.user_id == target_id, Membership.chat_id == chat_id
            )
        )
    )

    if membership is None:
        raise NotFoundException("Member not found.")

    # We make sure that admins can't edit
    # membership's foreign key fields and is_owner field
    filtered_payload = {
        k: v
        for k, v in payload.items()
        if k not in frozenset({"is_owner", "chat_id", "user_id"})
    }

    await base_services.update(session, membership, filtered_payload)
    return await session.scalar(
        select(Membership)
        .options(joinedload(Membership.user))
        .where(
            and_(
                Membership.user_id == target_id, Membership.chat_id == chat_id
            )
        )
    )


async def remove_member(
    session: AsyncSession, chat_id: int, user_id: int, target_id: int
) -> None:
    """Removes given user from chat. If user is not admin raises 403."""
    if not await _is_chat_admin(session, user_id, chat_id):
        raise UserNotAdminException

    membership = await session.scalar(
        select(Membership).where(
            and_(
                Membership.user_id == target_id, Membership.chat_id == chat_id
            )
        )
    )

    if membership is None:
        raise NotFoundException(
            "Member with given id cannot be found in chat."
        )
    elif membership.is_owner is True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner cannot be removed from group.",
        )

    await session.delete(membership)
    await session.commit()


async def list_public_chat_messages(
    session: AsyncSession,
    chat_id: int,
    user_id: int,
    paginator: BasePaginator | None = None,
) -> Sequence[Message] | PaginatedResponseDict:
    """Lists messages from public chat,
    if user is not chat member, raises 403."""
    if not await is_chat_member(session, user_id, chat_id):
        raise UserNotMemberException

    query = (
        select(Message)
        .options(joinedload(Message.sender), defer("sender_id"))
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .distinct()
    )

    if paginator:
        return await paginator.get_paginated_response_for_model(query)

    return (await session.scalars(query)).all()


async def list_chat_members(
    session: AsyncSession,
    chat_id: int,
    user_id: int,
    paginator: BasePaginator | None = None,
) -> Sequence[Row] | PaginatedResponseDict:
    """Lists chat members. If given user is not chat member, raises 403."""
    if not await is_chat_member(session, user_id, chat_id):
        raise UserNotMemberException

    list_chats_query = (
        select(Membership)
        .options(joinedload(Membership.user))
        .where(Membership.chat_id == chat_id)
        .distinct()
    )

    if paginator:
        return await paginator.get_paginated_response_for_model(
            list_chats_query
        )

    return (await session.scalars(list_chats_query)).all()


async def list_user_chats(
    session: AsyncSession,
    user_id: int,
    paginator: BasePaginator,
    keyword: str | None,
):
    """Returns target user's chats. Sorts them by the date of last message."""

    list_chats_query = (
        select(Chat)
        .join(Membership, Membership.chat_id == Chat.id)
        .options(
            joinedload(Chat.last_message).joinedload(Message.sender),
        )
        .where(Membership.user_id == user_id)
        .order_by(
            desc(func.coalesce(Chat.last_message_created_at, datetime.min)),
            desc(Chat.last_message_created_at),
        )
    )

    if keyword:
        expression = keyword + "%"
        list_chats_query = list_chats_query.where(Chat.name.like(expression))

    if paginator:
        return await paginator.get_paginated_response_for_model(
            list_chats_query
        )

    return (await session.scalars(list_chats_query)).all()
