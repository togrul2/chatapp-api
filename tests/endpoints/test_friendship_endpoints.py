"""Tests for friendship endpoints."""


class TestFriendshipRequestList:
    """Test endpoints related to listing friendship requests"""
    url = '/api/friendship/requests'

    def test_get_pending_requests(self):
        """Test friendship requests listing endpoint"""


class TestFriendshipRequestDetail:
    """
    Test endpoints related friendship request detail methods
    such as get, accept, reject.
    """
    @staticmethod
    def get_url(target_id: int):
        return f'/api/friendship/requests/{target_id}'

    def test_get_friendship_request(self):
        """Test getting friendship request."""

    def test_send_friendship_request(self):
        """Test sending friendship request to a target user."""

    def test_reject_friendship_request(self):
        """Test rejecting friendship request from a target user."""

    def test_accept_friendship_request(self):
        """Test accepting friendship request from a target user."""
