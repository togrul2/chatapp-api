"""Tests for friendship endpoints."""
import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.base.schemas import PaginatedResponse
from src.chatapp_api.friendship.models import Friendship
from src.chatapp_api.friendship.schemas import FriendshipRead
from src.chatapp_api.user.models import User
from src.chatapp_api.user.schemas import UserRead
from tests.utils import AssertionErrors, validate_dict


@pytest.mark.asyncio
class TestFriendshipRequestList:
    """Test endpoints related to listing friendship requests"""

    url = "/api/friendship/requests"

    async def test_get_pending_requests(
        self, auth_client: AsyncClient, friendship_request: Friendship
    ):
        """Test friendship requests listing endpoint"""
        response = await auth_client.get(self.url)
        body = response.json()

        assert (
            response.status_code == status.HTTP_200_OK
        ), "Status code is not successful."
        assert len(body["results"]) == 1
        assert friendship_request.id == body["results"][0]["id"]


@pytest.mark.asyncio
class TestFriendshipRequestDetail:
    """
    Test endpoints related friendship request detail methods
    such as get, accept, reject.
    """

    url = "/api/friendship/requests/users/{target_id}"

    async def test_send_friendship_request(
        self,
        user: User,
        sender_user: User,
        auth_client: AsyncClient,
        session: AsyncSession,
    ):
        """Test sending friendship request to a target user."""
        response = await auth_client.post(
            self.url.format(target_id=sender_user.id)
        )
        body = response.json()

        created_friendship = (
            await session.scalars(
                select(Friendship).where(
                    and_(
                        Friendship.sender_id == user.id,
                        Friendship.receiver_id == sender_user.id,
                    )
                )
            )
        ).one_or_none()

        assert (
            response.status_code == status.HTTP_201_CREATED
        ), AssertionErrors.HTTP_NOT_201_CREATED
        assert body["sender_id"] == user.id
        assert body["receiver_id"] == sender_user.id

        assert created_friendship is not None, "Friendship is not created."

        # teardown, delete created friendship
        await session.execute(
            delete(Friendship).where(
                and_(
                    Friendship.sender_id == user.id,
                    Friendship.receiver_id == sender_user.id,
                )
            )
        )
        await session.commit()

    async def test_reject_friendship_request(
        self,
        user: User,
        sender_user: User,
        auth_client: AsyncClient,
        session: AsyncSession,
    ):
        """Test rejecting friendship request from a target user."""
        friendship = Friendship(
            sender_id=sender_user.id, receiver_id=user.id, accepted=False
        )
        session.add(friendship)
        await session.commit()
        reject_url = self.url.format(target_id=sender_user.id) + "/decline"
        response = await auth_client.post(reject_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert (
            await session.scalars(
                select(Friendship).where(Friendship.id == friendship.id)
            )
        ).one_or_none() is None, "Friendship is not deleted after rejection"

    async def test_accept_friendship_request(
        self,
        sender_user: User,
        auth_client: AsyncClient,
        friendship_request: Friendship,
        session: AsyncSession,
    ):
        """Test accepting friendship request from a target user."""
        accept_url = self.url.format(target_id=sender_user.id) + "/accept"
        response = await auth_client.post(accept_url)
        friendship = (
            await session.scalars(
                select(Friendship).where(
                    and_(
                        Friendship.id == friendship_request.id,
                        Friendship.accepted == True,  # noqa: E712
                    )
                )
            )
        ).one_or_none()

        assert (
            response.status_code == status.HTTP_200_OK
        ), AssertionErrors.HTTP_NOT_200_OK
        assert (
            friendship is not None
        ), "Target friendship is deleted or does not exist"


@pytest.mark.asyncio
@pytest.mark.usefixtures("friendship")
async def test_list_friends(auth_client: AsyncClient):
    """Tests listing authenticated user's friends."""
    url = "/api/friendship/friends"
    response = await auth_client.get(url)

    assert (
        response.status_code == status.HTTP_200_OK
    ), AssertionErrors.HTTP_NOT_200_OK
    body = response.json()
    assert validate_dict(
        PaginatedResponse[UserRead], body
    ), AssertionErrors.INVALID_BODY
    assert len(body["results"]) == 1, AssertionErrors.INVALID_NUM_OF_ROWS


@pytest.mark.asyncio
@pytest.mark.usefixtures("friendship")
async def test_get_friendship(auth_client: AsyncClient, sender_user: User):
    """Test getting friendship request."""
    url = "/api/friendship/friends/{target_id}"
    response = await auth_client.get(url.format(target_id=sender_user.id))
    body = response.json()

    assert (
        response.status_code == status.HTTP_200_OK
    ), AssertionErrors.HTTP_NOT_200_OK
    assert validate_dict(FriendshipRead, body), AssertionErrors.INVALID_BODY
    assert body["accepted"] is True, "Unaccepted friendship returned"
