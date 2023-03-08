"""DB services for chat related models & routes."""
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import TypedDict, cast

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import and_, desc, exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload, undefer

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
from src.chatapp_api.chat.schemas import MembershipCreate
from src.chatapp_api.config import (
    CHAT_INVITE_LINK_DURATION,
    JWT_ALGORITHM,
    settings,
)
from src.chatapp_api.paginator import BasePaginator, PaginatedResponseDict


class InvitationJWT(TypedDict):
    type: str
    chat_id: int
    expire: str


async def _create_private_chat(
    session: AsyncSession, user_1_id: int, user_2_id: int
) -> Chat:
    """Creates private chat for given two users"""
    chat = Chat(private=True)
    session.add(chat)
    await session.flush()
    session.add_all(
        Membership(
            chat_id=chat.id,
            user_id=member_id,
            is_admin=True,
            is_owner=False,
        )
        for member_id in (user_1_id, user_2_id)
    )
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
    if (chat := await _get_private_chat(session, user1_id, user2_id)) is None:
        return (await _create_private_chat(session, user1_id, user2_id)), True

    return chat, False


async def create_message(
    session: AsyncSession, chat_id: int, sender_id: int, body: str
) -> Message:
    """Creates message at given chat from given sender to given receiver.
    chat_id must be id of an existing chat."""
    return await base_services.create(
        session, Message(chat_id=chat_id, sender_id=sender_id, body=body)
    )


async def list_private_chat_messages(
    session: AsyncSession,
    user_id: int,
    target_id: int,
    paginator: BasePaginator,
) -> PaginatedResponseDict:
    """Returns messages from a private chat with a given id."""
    if (chat := await _get_private_chat(session, user_id, target_id)) is None:
        raise NotFoundException(
            "Private chat with given user has not been found."
        )

    query = (
        select(Message)
        .options(joinedload(Message.sender), defer(Message.sender_id))
        .where(Message.chat_id == chat.id)
        .order_by(Message.created_at.desc())
    )

    return await paginator.get_paginated_response_for_model(query)


async def _validate_not_null_unique_chat_name(
    session: AsyncSession, name: str, chat_id: int | None = None
) -> None:
    """Validates whether there are chats with the same name as given one.
    Empty names can be duplicated, so they won't count.
    Also checks whether this name belongs to target chat if it exists.
    If some check fails raises http exception"""
    if await session.scalar(
        exists().where(and_(Chat.name == name, Chat.id != chat_id)).select()
    ):
        raise ChatNameTakenException


async def list_chats(
    paginator: BasePaginator,
    keyword: str | None = None,
) -> PaginatedResponseDict:
    """Returns list of all records.
    If keyword passed returns matching chats only."""
    query = (
        select(Chat)
        .options(undefer(Chat.users_count))
        .where(Chat.private == False)  # noqa: E712
    )

    if keyword:
        expression = "%" + keyword.upper() + "%"
        query = query.where(func.upper(Chat.name).like(expression))

    return await paginator.get_paginated_response_for_model(query)


async def create_public_chat(
    session: AsyncSession,
    user_id: int,
    name: str,
    members: Sequence[MembershipCreate],
) -> Chat:
    """Creates chat with membership to a given user."""
    await _validate_not_null_unique_chat_name(session, name)

    chat = Chat(private=False, name=name)
    session.add(chat)
    await session.flush()

    session.add(
        Membership(
            chat_id=chat.id, user_id=user_id, is_admin=True, is_owner=True
        )
    )
    session.add_all(
        Membership(
            chat_id=chat.id,
            user_id=member.id,
            is_admin=member.is_admin,
        )
        for member in filter(lambda member: member.id != user_id, members)
        # Add all users from members but exclude if owner is there
    )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise NotFoundException(
            "Nonexistent user passed as a member."
        ) from exc

    return chat


async def get_public_chat_with_members_count_or_404(
    session: AsyncSession, chat_id: int
) -> Chat:
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


async def _get_chat_member(
    session: AsyncSession,
    user_id: int,
    chat_id: int,
) -> Membership | None:
    """Returns whether set user is member of chat and
    has given role(optional) or not."""
    query = select(Membership).where(
        and_(Membership.chat_id == chat_id, Membership.user_id == user_id)
    )

    return await session.scalar(query)


async def is_chat_member(
    session: AsyncSession, user_id: int, chat_id: int
) -> bool:
    """Returns whether given user is chat's member or not."""
    return await _get_chat_member(session, user_id, chat_id) is not None


async def _is_chat_admin(
    session: AsyncSession, user_id: int, chat_id: int
) -> bool:
    """Returns whether given user is chat's admin or not."""
    membership = await _get_chat_member(session, user_id, chat_id)
    return membership is not None and membership.is_admin is True


async def _is_chat_owner(
    session: AsyncSession, user_id: int, chat_id: int
) -> bool:
    """Returns whether given user is chat's admin or not."""
    membership = await _get_chat_member(session, user_id, chat_id)
    return membership is not None and membership.is_owner is True


async def update_chat(
    session: AsyncSession, user_id: int, chat_id: int, name: str | None = None
) -> Chat:
    """Updates chat's information."""
    if (chat := await session.get(Chat, chat_id)) is None:
        raise NotFoundException(
            "Public chat with given id has not been found."
        )

    if not await _is_chat_admin(session, user_id, chat_id):
        raise UserNotAdminException

    if name:
        chat.name = name

    await session.commit()
    await session.refresh(chat)
    return chat


async def delete_chat(
    session: AsyncSession, user_id: int, chat_id: int
) -> None:
    """Deletes public chat with given id.
    If chat doesn't exist, raises 404 http exception."""
    if not await _is_chat_owner(session, user_id, chat_id):
        raise UserNotOwnerException

    chat = await session.get(Chat, chat_id)
    await session.delete(chat)
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
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


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
    if await is_chat_member(session, user_id, chat_id):
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
    session.add(membership)
    await session.commit()
    return membership


async def update_membership(
    session: AsyncSession,
    chat_id: int,
    user_id: int,
    target_id: int,
    is_admin: bool | None = None,
    is_owner: bool | None = None,
):
    """Updates chat member's information, his admin, owner status.
    If User is not chat admin raises 403.
    If non owner tries to make someone owner raises 403."""
    if not await _is_chat_admin(session, user_id, chat_id):
        raise UserNotAdminException

    # We make sure that admins can't edit is_owner field
    if _is_chat_owner(session, user_id, chat_id) and is_owner is not None:
        raise UserNotOwnerException

    membership = await _get_chat_member(session, target_id, chat_id)

    if membership is None:
        raise NotFoundException("Member not found.")

    if is_admin:
        membership.is_admin = is_admin

    if is_owner:
        membership.is_owner = is_owner

    session.add(membership)
    await session.commit()
    await session.refresh(membership)
    return membership


async def remove_member(
    session: AsyncSession, chat_id: int, user_id: int, target_id: int
) -> None:
    """Removes given user from chat. If user is not admin raises 403."""
    is_user_admin = await _is_chat_admin(session, user_id, chat_id)

    if user_id != target_id and is_user_admin is False:
        raise UserNotAdminException

    membership = await _get_chat_member(session, target_id, chat_id)

    if membership is None:
        raise NotFoundException(
            "Member with given id cannot be found in chat."
        )
    if membership.is_owner is True:
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
    paginator: BasePaginator,
) -> PaginatedResponseDict:
    """Lists messages from public chat,
    if user is not chat member, raises 403."""
    if not await is_chat_member(session, user_id, chat_id):
        raise UserNotMemberException

    query = (
        select(Message)
        .options(joinedload(Message.sender), defer(Message.sender_id))
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .distinct()
    )

    return await paginator.get_paginated_response_for_model(query)


async def list_chat_members(
    session: AsyncSession,
    chat_id: int,
    user_id: int,
    paginator: BasePaginator,
) -> PaginatedResponseDict:
    """Lists chat members. If given user is not chat member, raises 403."""
    if not await is_chat_member(session, user_id, chat_id):
        raise UserNotMemberException

    list_chats_query = (
        select(Membership)
        .options(joinedload(Membership.user))
        .where(Membership.chat_id == chat_id)
        .distinct()
    )

    return await paginator.get_paginated_response_for_model(list_chats_query)


async def list_user_chats(
    user_id: int,
    paginator: BasePaginator,
    keyword: str | None,
) -> PaginatedResponseDict:
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
        expression = "%" + keyword + "%"
        list_chats_query = list_chats_query.where(Chat.name.like(expression))

    return await paginator.get_paginated_response_for_model(list_chats_query)
