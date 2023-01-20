"""DB services for chat related models & routes."""
from datetime import datetime, timedelta
from typing import Any, cast
from urllib import parse

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import Boolean, Column, delete, exists, func, select
from sqlalchemy.engine import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload

from src.config import ALGORITHM, CHAT_INVITE_LINK_DURATION, settings
from src.exceptions.base import NotFound
from src.exceptions.chat import (
    ChatNameTakenException,
    UserDoesNotExist,
    UserNotAdminException,
    UserNotOwnerException,
)
from src.models.chat import Chat, Membership, Message
from src.paginator import BasePaginator
from src.schemas.base import PaginatedResponse
from src.schemas.chat import (
    ChatCreate,
    ChatReadWithMembers,
    ChatUpdate,
    MessageRead,
)
from src.services import base as base_services


async def _create_chat(
    session: AsyncSession,
    schema_dict: dict[str, Any],
    user_id: int | None = None,
) -> Chat:
    """Custom create method for chat model."""
    payload: dict[str, Any] = {**schema_dict, "private": False}
    users = list(
        filter(lambda user: user["id"] != user_id, payload.pop("users"))
    )

    chat = await base_services.create(
        session, Chat(**payload), commit=False, flush=True
    )
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
            raise UserDoesNotExist(
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
) -> Chat:
    """Returns private chat of given two users.
    If it doesn't exist, creates it."""
    chat = await _get_private_chat(session, user1_id, user2_id)

    if chat is None:
        return await _create_chat(
            session, {"private": True, "users": [user1_id, user2_id]}
        )

    return chat


async def create_message(
    session: AsyncSession, chat_id: int, sender_id: int, body: str
) -> Message:
    """Creates message at given chat from
    given sender to given receiver."""
    return await base_services.create(
        session, Message(chat_id=chat_id, sender_id=sender_id, body=body)
    )


async def get_messages_from_private_chat(
    session: AsyncSession,
    user_id: int,
    target_id: int,
    paginator: BasePaginator | None = None,
) -> PaginatedResponse[MessageRead] | list[Message]:
    """Returns messages from a private chat with a given id."""
    if (chat := await _get_private_chat(session, user_id, target_id)) is None:
        raise NotFound

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
        exists().where((Chat.name == name) & (Chat.id != chat_id)).select()
    )

    if matching_chat:
        raise ChatNameTakenException


async def list_chats(
    session: AsyncSession,
    paginator: BasePaginator | None = None,
    keyword: str | None = None,
) -> PaginatedResponse[ChatReadWithMembers] | list[Row]:
    """Returns list of all records.
    If keyword passed returns matching chats only."""
    query = (
        select(
            [
                Chat.id,
                Chat.created_at,
                Chat.name,
                func.count(Membership.id).label("members"),
            ]
        )
        .join(Membership, Chat.id == Membership.chat_id)
        .where(Chat.private == False)  # noqa: E712
        .group_by(Chat.id)
    )

    if keyword:
        expression = keyword.upper() + "%"
        query = query.where(func.upper(Chat.name).like(expression))

    if paginator:
        return await paginator.get_paginated_response_for_rows(query)

    return (await session.execute(query)).all()


async def create_public_chat(
    session: AsyncSession, user_id: int, schema: ChatCreate
) -> Row:
    """Creates chat with membership to a given user."""
    await _validate_not_null_unique_chat_name(session, schema.name)
    chat = await _create_chat(session, schema.dict(), user_id)

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


async def _get_public_chat(session: AsyncSession, chat_id: int) -> Row | None:
    """Returns public chat with given id.
    Additionally, calculates its number of members"""
    chat_query = await session.execute(
        select(
            [
                Chat.id,
                Chat.name,
                Chat.created_at,
                func.count(Membership.id).label("members"),
            ]
        )
        .join(Membership, Membership.chat_id == Chat.id)
        .where((Chat.private == False) & (Chat.id == chat_id))  # noqa: E712
        .group_by(Chat.id)
    )

    return chat_query.one_or_none()


async def get_public_chat_or_404(session: AsyncSession, chat_id: int) -> Row:
    """Returns single chat with given id.
    If it does not exists, returns 404 error code."""
    chat = await _get_public_chat(session, chat_id)

    if chat is None:
        raise NotFound

    return chat


async def _check_role(
    session: AsyncSession, user_id: int, chat_id: int, role: Column[Boolean]
) -> bool:
    """Returns whether set user has given role in chat or not."""
    query = (
        exists()
        .where(
            (Membership.chat_id == chat_id)
            & (Membership.user_id == user_id)
            & (role == True)  # noqa: E712
        )
        .select()
    )
    return await session.scalar(query)


async def _is_chat_admin(
    session: AsyncSession, user_id: int, chat_id: int
) -> bool:
    """Returns whether set user is given chat's admin or not."""
    return await _check_role(session, user_id, chat_id, Membership.is_admin)


async def _is_chat_owner(
    session: AsyncSession, user_id: int, chat_id: int
) -> bool:
    """Returns whether set user is given chat's admin or not."""
    return await _check_role(session, user_id, chat_id, Membership.is_owner)


async def update_chat(
    session: AsyncSession, user_id: int, chat_id: int, payload: ChatUpdate
) -> Chat:
    """Updates chat's information."""
    chat = await session.get(Chat, chat_id)

    if chat is None:
        raise NotFound

    if not await _is_chat_admin(session, user_id, chat_id):
        raise UserNotAdminException

    return await base_services.update(session, chat, payload.dict())


async def delete_chat(
    session: AsyncSession, user_id: int, chat_id: int
) -> None:
    """Deletes public chat with given id.
    If chat doesn't exist, raises 404 http exception."""
    chat = await get_public_chat_or_404(session, chat_id)

    if not await _is_chat_owner(session, user_id, chat_id):
        raise UserNotOwnerException

    await session.execute(
        delete(Membership).where(Membership.chat_id == chat.id)
    )
    await session.execute(delete(Chat).where(Chat.id == chat.id))
    await session.commit()


def _generate_invite_token(chat_id: int) -> str:
    """Generates invite token for given chat."""
    expire = datetime.utcnow() + timedelta(seconds=CHAT_INVITE_LINK_DURATION)
    payload = {
        "expire": expire.isoformat(),
        "type": "chat-invitation",
        "chat_id": chat_id,
    }
    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


async def get_invite_link_for_chat(
    session: AsyncSession, user_id: int, chat_id: int, base_url: str
) -> str:
    """Generates invite link for given group.
    If requesting user is not admin, raises 403 http error."""
    if not await _is_chat_admin(session, user_id, chat_id):
        raise UserNotAdminException

    token = _generate_invite_token(chat_id)
    return parse.urljoin(base_url, f"api/chats/{chat_id}/enroll?t={token}")


async def enroll_user_with_token(
    session: AsyncSession, user_id: int, chat_id: int, token: str
) -> Membership:
    """Enrolls user to chat. If token cannot be
    parsed or expired or is invalid, 400 http error is raised.
    If user is already in chat, 409 http error is raised."""

    try:
        body = jwt.decode(token, settings.secret_key, ALGORITHM)
    except JWTError as exc:
        raise HTTPException(
            status_code=400, detail="Token is either invalid or expired."
        ) from exc

    if not (
        datetime.fromisoformat(cast(str, body.get("expire")))
        <= datetime.utcnow()
        or chat_id != body.get("chat_id")
        or body.get("chat_id") != "chat-invitation"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is either invalid or expired.",
        )

    if await session.scalar(
        exists()
        .where(
            (Membership.chat_id == chat_id) & (Membership.user_id == user_id)
        )
        .select()
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already enrolled in this chat.",
        )

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
    session: AsyncSession, chat_id: int, user_id: int, target_id: int, payload
):
    return None


async def remove_member(
    session: AsyncSession, chat_id: int, user_id: int, target_id: int
):
    return None


async def list_chat_messages(
    session: AsyncSession, chat_id: int, user_id: int
):
    return None
