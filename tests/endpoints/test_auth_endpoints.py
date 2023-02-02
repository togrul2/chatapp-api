from typing import cast

import pytest
from fastapi import status
from httpx import AsyncClient

from src.auth.exceptions import BadTokenException
from src.auth.jwt import create_access_token, create_refresh_token
from src.user.exceptions import BadCredentialsException
from src.user.models import User


@pytest.mark.asyncio
class TestToken:
    """Test token and refresh endpoint."""

    token_url = (
        "/api/token"  # nosec - ✅ token is a part of url, not a password
    )
    refresh_url = "/api/refresh"

    async def test_token_success(self, client: AsyncClient, user: User):
        """Test successful token creation endpoint"""
        user_data = {"username": user.username, "password": "Testpassword"}
        response = await client.post(self.token_url, data=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json().keys() == frozenset(
            {"access_token", "refresh_token"}
        )

    async def test_token_invalid_credentials(
        self, client: AsyncClient, user: User
    ):
        """Test token create with invalid credentials attempt."""
        user_data = {
            "username": user.username,
            "password": "Testpassword" + "wrong",
        }
        response = await client.post(self.token_url, data=user_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == BadCredentialsException.detail

    async def test_refresh_success(self, client: AsyncClient, user: User):
        """Test refresh endpoint successful attempt."""
        refresh_token = create_refresh_token(cast(int, user.id))
        response = await client.post(
            self.refresh_url, data={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json().keys() == frozenset(
            {"access_token", "refresh_token"}
        )

    async def test_refresh_bad_data(self, client: AsyncClient, user: User):
        """Test refresh endpoint with invalid refresh token."""
        refresh_token = create_access_token(cast(int, user.id))
        response = await client.post(
            self.refresh_url, data={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == BadTokenException.detail