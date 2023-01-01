"""Tests for friendship endpoints."""
from typing import cast

from fastapi import status

from models.user import Friendship
from tests.conftest import TestDatabase, test_db_url


class TestFriendshipRequestList:
    """Test endpoints related to listing friendship requests"""

    url = "/api/friendship/requests"

    def test_get_pending_requests(self, auth_client, friendship_request):
        """Test friendship requests listing endpoint"""
        response = auth_client.get(self.url)
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert friendship_request.id == body[0]["id"]


class TestFriendshipRequestDetail:
    """
    Test endpoints related friendship request detail methods
    such as get, accept, reject.
    """

    @staticmethod
    def get_url(target_id: int):
        """Returns url for target user's friendship."""
        return f"/api/friendship/requests/users/{target_id}"

    def test_get_friendship_request(
        self, user, sender_user, auth_client, friendship_request
    ):
        """Test getting friendship request."""
        response = auth_client.get(self.get_url(cast(int, sender_user.id)))
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert body["id"] == friendship_request.id
        assert body["sender_id"] == sender_user.id
        assert body["receiver_id"] == user.id
        assert body["accepted"] is None

    def test_send_friendship_request(self, user, sender_user, auth_client):
        """Test sending friendship request to a target user."""
        response = auth_client.post(self.get_url(cast(int, sender_user.id)))
        body = response.json()

        assert response.status_code == status.HTTP_201_CREATED
        assert body["sender_id"] == user.id
        assert body["receiver_id"] == sender_user.id
        with TestDatabase(test_db_url).session_maker() as session:
            friendship = (
                session.query(Friendship)
                .filter(
                    (Friendship.sender_id == user.id)
                    & (Friendship.receiver_id == sender_user.id)
                )
                .first()
            )
            assert friendship is not None
            session.delete(friendship)
            session.commit()

    def test_reject_friendship_request(
        self, sender_user, auth_client, friendship_request
    ):
        """Test rejecting friendship request from a target user."""
        # target id must be preserved
        # since after rejection friendship record will be deleted
        target_id = sender_user.id
        response = auth_client.delete(self.get_url(cast(int, sender_user.id)))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        with TestDatabase(test_db_url).session_maker() as session:
            assert (
                session.query(Friendship)
                .filter(Friendship.id == target_id)
                .first()
            ) is None

    def test_accept_friendship_request(
        self, sender_user, auth_client, friendship_request
    ):
        """Test accepting friendship request from a target user."""
        response = auth_client.patch(self.get_url(cast(int, sender_user.id)))

        assert response.status_code == status.HTTP_200_OK
        with TestDatabase(test_db_url).session_maker() as session:
            assert (
                session.query(Friendship)
                .filter(
                    (Friendship.id == friendship_request.id)
                    & (Friendship.accepted == True)  # noqa: E712
                )
                .first()
            ) is not None
