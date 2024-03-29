"""Tests for user endpoints."""
import os
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper  # noqa
from typing import cast
from urllib import parse

import pytest
from fastapi import status
from httpx import AsyncClient, Headers
from PIL import Image
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.auth.jwt import create_access_token
from src.chatapp_api.user.models import User
from src.chatapp_api.user.schemas import UserRead
from tests.conftest import TEST_STATIC_ROOT
from tests.utils import AssertionErrors, validate_dict


@pytest.mark.asyncio
class TestRegisterUser:
    """Class for testing register endpoint."""

    url = "/api/users"
    user_data = {
        "username": "peterdoe",
        "email": "peterdoe@example.com",
        "first_name": "Peter",
        "last_name": "Doe",
        "password": "Testpassword",
    }

    async def test_register_success(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Test successful user register."""
        response = await client.post(self.url, json=self.user_data)
        body = response.json()

        assert (
            response.status_code == status.HTTP_201_CREATED
        ), AssertionErrors.HTTP_NOT_201_CREATED
        assert validate_dict(UserRead, body), AssertionErrors.INVALID_BODY
        assert body["username"] == self.user_data["username"]
        assert body["email"] == self.user_data["email"]
        assert body["first_name"] == self.user_data["first_name"]
        assert body["last_name"] == self.user_data["last_name"]

        # Teardown, delete registered user
        await session.execute(
            delete(User).where(User.username == body["username"])
        )
        await session.commit()

    async def test_register_missing_fields(self, client: AsyncClient):
        """Test user register with bad data"""
        response = await client.post(
            self.url, json={"username": "peterdoe", "password": "dummy_pass"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_register_user_with_existing_username(
        self, client: AsyncClient, user: User
    ):
        """Test registering user with existing username."""
        payload = {**self.user_data, "username": user.username}
        response = await client.post(self.url, json=payload)

        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_register_user_with_existing_email(
        self, client: AsyncClient, user: User
    ):
        """Test registering user with existing email."""
        payload = {**self.user_data, "email": user.email}
        response = await client.post(self.url, json=payload)

        assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
class TestUsersMe:
    """Test authenticated user endpoint."""

    url = "/api/users/me"
    image_url = "/api/users/me/image"

    @pytest.fixture()
    def profile_picture(self):
        """Profile picture creation fixture.
        Returns simple image file with jpg extension"""
        with NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            yield image_file

    async def test_get_user_successful(self, auth_client: AsyncClient):
        """Tests get logged in user endpoint successful"""
        response = await auth_client.get(self.url)

        assert (
            response.status_code == status.HTTP_200_OK
        ), AssertionErrors.HTTP_NOT_200_OK

    async def test_get_user_unauthenticated(self, client: AsyncClient):
        """Tests unauthorized user getting 401"""
        response = await client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_modify_user(self, auth_client: AsyncClient):
        """Tests logged-in user's update method."""
        payload = {
            "username": "johndoe_new",
            "email": "johndoe_new@gmail.com",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = await auth_client.put(self.url, json=payload)
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        for field, value in payload.items():
            assert body[field] == value

    async def test_partial_modify_user(self, auth_client: AsyncClient):
        """Tests logged-in user's partial update method."""
        payload = {
            "username": "johndoe2",
        }
        response = await auth_client.patch(self.url, json=payload)
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert body["username"] == payload["username"]

    async def test_image_upload(
        self,
        user: User,
        auth_client: AsyncClient,
        profile_picture: _TemporaryFileWrapper,
    ):
        """Tests logged-in user's image upload method."""
        files = {
            "profile_picture": (
                profile_picture.name,
                profile_picture,
                "image/jpeg",
            )
        }
        response = await auth_client.post(self.image_url, files=files)
        body = response.json()
        filename = body["profile_picture"].split("/")[-1]
        path = TEST_STATIC_ROOT / "users" / str(user.id) / "pfp" / filename

        assert response.status_code == status.HTTP_200_OK
        assert os.path.exists(path)

    async def test_image_remove(self, auth_client: AsyncClient):
        """Tests logged-in user's image remove method."""
        response = await auth_client.delete(self.image_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_user(
        self, user: User, client: AsyncClient, session: AsyncSession
    ):
        """Tests logged-in user deletion."""
        user = User(  # nosec # noqa: S106
            username="marrydoe",
            email="marrydoe@example.com",
            password="Testpassword",
            # hashing is not needed here, we will
            # generate jwt token based on user's id
        )
        session.add(user)
        await session.commit()
        client.headers = Headers(
            {"Authorization": f"Bearer {create_access_token(user.id)}"}
        )
        response = await client.delete(self.url)

        assert (
            response.status_code == status.HTTP_204_NO_CONTENT
        ), AssertionErrors.HTTP_NOT_204_NO_CONTENT
        assert await session.get(User, user.id) is None, "User is not deleted"


@pytest.mark.asyncio
class TestListUsers:
    """Test user listing api."""

    url = "/api/users"

    async def test_list_users(self, client: AsyncClient, user: User):
        """Test listing all users."""
        response = await client.get(self.url)
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(body["results"]) == 1
        assert body["results"][0]["id"] == user.id

    async def test_list_users_with_keyword(
        self, client: AsyncClient, user: User
    ):
        """Tests listing users with filtering options.
        Basically searching for users."""
        params = parse.urlencode({"keyword": "john"})
        response = await client.get(self.url, params=params)
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(body["results"]) == 1
        assert body["results"][0]["id"] == user.id


@pytest.mark.asyncio
class TestRetrieveUser:
    """Tests user detail endpoints."""

    @staticmethod
    def get_url(username: str):
        """Returns url for user with given username."""
        return f"api/users/{username}"

    async def test_retrieve_user(self, client: AsyncClient, user: User):
        """Tests user detail endpoint."""
        response = await client.get(self.get_url(cast(str, user.username)))

        assert response.status_code == status.HTTP_200_OK

    async def test_retrieve_user_not_found(self, client: AsyncClient):
        """Tests getting detail for user with username which does not exist."""
        response = await client.get(self.get_url("dummyuser"))

        assert response.status_code == status.HTTP_404_NOT_FOUND
