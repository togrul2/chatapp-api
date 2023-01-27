"""Module with Chat API Routes & Websockets"""
import asyncio

from fastapi import APIRouter, Depends, Form, Request, WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import broadcaster
from src.dependencies import (
    get_current_user_id_from_bearer,
    get_current_user_id_from_cookie,
    get_db,
    get_paginator,
)
from src.paginator import BasePaginator
from src.schemas.base import DetailMessage, PaginatedResponse
from src.schemas.chat import (
    ChatCreate,
    ChatRead,
    ChatReadWithMembers,
    ChatUpdate,
    MemberRead,
    MembershipBase,
    MembershipUpdate,
    MessageRead,
)
from src.services import chat as chat_services
from src.websocket_managers.chat import (
    ChatMessagesManager,
    PrivateMessageManager,
)

router = APIRouter(prefix="/api", tags=["chat"])


@router.websocket("/chats/privates/connect")
async def private_messages(
    websocket: WebSocket,
    user_id: int = Depends(get_current_user_id_from_cookie),
    session: AsyncSession = Depends(get_db),
):
    """Websocket for sending and receiving private messages."""

    manager = PrivateMessageManager(broadcaster, session, user_id)
    await websocket.accept()
    await asyncio.wait(
        [
            asyncio.create_task(manager.receiver(websocket)),
            asyncio.create_task(manager.sender(websocket)),
        ],
        return_when=asyncio.FIRST_COMPLETED,
    )


@router.get(
    "/chats/users/{target_id}/messages",
    response_model=PaginatedResponse[MessageRead],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Chat with target user does not exist.",
        }
    },
)
async def get_private_messages_from_user(
    target_id: int,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Returns messages with target user."""
    return await chat_services.list_private_chat_messages(
        session, user_id, target_id, paginator
    )


@router.websocket("/chats/connect/{chat_id}")
async def chat_messages_websocket_route(
    chat_id: int,
    websocket: WebSocket,
    user_id: int = Depends(get_current_user_id_from_cookie),
    session: AsyncSession = Depends(get_db),
):
    """Websocket route for sending and receiving public chat messages."""
    manager = ChatMessagesManager(broadcaster, session, user_id, chat_id)
    await manager.accept(websocket)
    await asyncio.wait(
        [
            asyncio.create_task(manager.receiver(websocket)),
            asyncio.create_task(manager.sender(websocket)),
        ],
        return_when=asyncio.FIRST_COMPLETED,
    )


@router.get("/chats", response_model=PaginatedResponse[ChatReadWithMembers])
async def list_public_chats(
    keyword: str | None = None,
    session: AsyncSession = Depends(get_db),
    paginator: BasePaginator = Depends(get_paginator),
):
    """List public chats as well as search through them."""
    return await chat_services.list_chats(session, paginator, keyword)


@router.post(
    "/chats",
    response_model=ChatReadWithMembers,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": DetailMessage,
            "description": "Chat name is taken.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "User with given id does not exist.",
        },
    },
)
async def create_public_chat(
    chat: ChatCreate,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db),
):
    """Create public chat. Makes creator of chat owner."""
    return await chat_services.create_public_chat(session, user_id, chat)


@router.get(
    "/chats/{chat_id}",
    response_model=ChatReadWithMembers,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Chat is not found.",
        }
    },
)
async def get_public_chat(
    chat_id: int, session: AsyncSession = Depends(get_db)
):
    """Get public chat detail with given id.
    If no public chat is found returns 404."""
    return await chat_services.get_public_chat_with_members_or_404(
        session, chat_id
    )


@router.put(
    "/chats/{chat_id}",
    response_model=ChatRead,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "User is not group admin.",
        }
    },
)
async def update_public_chat(
    chat_id: int,
    data: ChatUpdate,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db),
):
    """Update public chat info. If user is not admin, returns 403."""
    return await chat_services.update_chat(session, user_id, chat_id, data)


@router.delete(
    "/chats/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "User is not group owner.",
        }
    },
)
async def delete_public_chat(
    chat_id: int,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db),
):
    """Deletes chat with given id. If user is not owner, returns 403."""
    await chat_services.delete_chat(session, user_id, chat_id)


@router.post(
    "/chats/{chat_id}/invite-link",
    response_model=str,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "Authenticated user is not chat admin.",
        }
    },
)
async def get_invite_link_for_chat(
    chat_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Generates and returns invite link for chat with expiration link."""
    return await chat_services.get_invite_link_for_chat(
        session, user_id, chat_id, str(request.base_url)
    )


@router.post(
    "/chats/{chat_id}/enroll",
    response_model=MembershipBase,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DetailMessage,
            "description": "Token is invalid or expired.",
        },
        status.HTTP_409_CONFLICT: {
            "model": DetailMessage,
            "description": "User is already enrolled into the chat.",
        },
    },
)
async def enroll_into_chat(
    chat_id: int,
    token: str = Form(alias="t"),
    session: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Enrolls user into chat.
    If token is expired or incorrect returns 400 error code."""
    return await chat_services.enroll_user_with_token(
        session, user_id, chat_id, token
    )


@router.patch("/chats/{chat_id}/members/{target_id}")
async def update_user_membership(
    chat_id: int,
    target_id: int,
    payload: MembershipUpdate,
    session: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Updates user membership info in chat (is_admin).
    If non admin user, returns 403 error code."""
    return await chat_services.update_membership(
        session, chat_id, user_id, target_id, payload.dict()
    )


@router.delete("/chats/{chat_id}/members/{target_id}")
async def remove_user_from_chat(
    chat_id: int,
    target_id: int,
    session: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Removes user from chat. If non admin user, returns 403 error code."""
    await chat_services.remove_member(session, chat_id, user_id, target_id)


@router.get(
    "/chats/{chat_id}/messages",
    response_model=PaginatedResponse[MessageRead],
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "User is not chat member.",
        }
    },
)
async def list_chat_messages(
    chat_id: int,
    session: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id_from_bearer),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Lists chat messages. If user is not chat member,
    returns 403 http error code."""
    return await chat_services.list_public_chat_messages(
        session, chat_id, user_id, paginator
    )


@router.get(
    "/chats/{chat_id}/members",
    response_model=PaginatedResponse[MemberRead],
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "User is not chat member.",
        }
    },
)
async def list_chat_members(
    chat_id: int,
    session: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id_from_bearer),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Lists chat members. If user is not chat member,
    returns 403 http error code."""
    return await chat_services.list_chat_members(
        session, chat_id, user_id, paginator
    )
