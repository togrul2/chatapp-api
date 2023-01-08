"""Tests for user endpoints."""
import os
import tempfile
from typing import cast
from urllib import parse

import pytest
from fastapi import status
from PIL import Image

from authentication import create_access_token, create_refresh_token
from exceptions.user import (
    EmailAlreadyTaken,
    HTTPBadTokenException,
    UsernameAlreadyTaken,
)
from models.user import User
from tests.conftest import TEST_STATIC_ROOT, TestDatabase, test_db_url


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

    def test_register_success(self, client):
        """Test successful user register."""
        response = client.post(self.url, json=self.user_data)
        body = response.json()

        assert response.status_code == status.HTTP_201_CREATED
        assert body["username"] == self.user_data["username"]
        assert body["email"] == self.user_data["email"]
        assert body["first_name"] == self.user_data["first_name"]
        assert body["last_name"] == self.user_data["last_name"]

        # Teardown, delete registered user
        with TestDatabase(test_db_url).session_maker() as session:
            session.query(User).filter_by(username=body["username"]).delete()
            session.commit()

    def test_register_missing_fields(self, client):
        """Test user register with bad data"""
        response = client.post(
            self.url, json={"username": "peterdoe", "password": "dummy_pass"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_with_existing_username(self, client, user: User):
        """Test registering user with existing username."""
        response = client.post(
            self.url,
            json={
                **self.user_data,
                "username": user.username,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == UsernameAlreadyTaken.detail

    def test_register_user_with_existing_email(self, client, user: User):
        """Test registering user with existing email."""
        response = client.post(
            self.url, json={**self.user_data, "email": user.email}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == EmailAlreadyTaken.detail


class TestToken:
    """Test token and refresh endpoint."""

    token_url = "/api/token"
    refresh_url = "/api/refresh"

    def test_token_success(self, client, user: User):
        """Test successful token creation endpoint"""
        user_data = {"username": user.username, "password": "Testpassword"}
        response = client.post(self.token_url, data=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json().keys() == frozenset(
            {"access_token", "refresh_token"}
        )

    def test_token_invalid_credentials(self, client, user):
        """Test token create with invalid credentials attempt."""
        user_data = {
            "username": user.username,
            "password": "Testpassword" + "wrong",
        }
        response = client.post(self.token_url, data=user_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == HTTPBadTokenException.detail

    def test_refresh_success(self, client, user):
        """Test refresh endpoint successful attempt."""
        refresh_token = create_refresh_token(user.id)
        response = client.post(
            self.refresh_url, data={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json().keys() == frozenset(
            {"access_token", "refresh_token"}
        )

    def test_refresh_bad_data(self, client, user):
        """Test refresh endpoint with invalid refresh token."""
        refresh_token = create_access_token(user.id)
        response = client.post(
            self.refresh_url, data={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == HTTPBadTokenException.detail


class TestUsersMe:
    """Test authenticated user endpoint."""

    url = "/api/users/me"
    image_url = "/api/users/me/image"

    @pytest.fixture()
    def profile_picture(self):
        """Profile picture creation fixture.
        Returns simple image file with jpg extension"""
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            yield image_file

    def test_get_user_successful(self, auth_client):
        """Tests get logged in user endpoint successful"""
        response = auth_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK

    def test_get_user_unauthenticated(self, client):
        """Tests unauthorized user getting 401"""
        response = client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_modify_user(self, auth_client):
        """Tests logged in user's update method."""
        payload = {
            "username": "johndoe_new",
            "email": "johndoe_new@gmail.com",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = auth_client.put(self.url, json=payload)
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        for field, value in payload.items():
            assert body[field] == value

    def test_partial_modify_user(self, auth_client):
        """Tests logged in user's partial update method."""
        payload = {
            "username": "johndoe2",
        }
        response = auth_client.patch(self.url, json=payload)
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert body["username"] == payload["username"]

    def test_image_upload(self, user, auth_client, profile_picture):
        """Tests logged-in user's image upload method."""
        files = {
            "profile_picture": (
                profile_picture.name,
                profile_picture,
                "image/jpeg",
            )
        }
        response = auth_client.post(self.image_url, files=files)
        body = response.json()
        filename = body["profile_picture"].split("/")[-1]
        path = TEST_STATIC_ROOT / "users" / str(user.id) / "pfp" / filename

        assert response.status_code == status.HTTP_200_OK
        assert os.path.exists(path)

    def test_image_remove(self, auth_client):
        """Tests logged-in user's image remove method."""
        response = auth_client.delete(self.image_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_user(self, user, auth_client):
        """Tests logged-in user deletion."""
        target_id = user.id
        response = auth_client.delete(self.url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        with TestDatabase(test_db_url).session_maker() as session:
            assert (
                session.query(User).filter(User.id == target_id).first()
            ) is None


class TestListUsers:
    """Test user listing api."""

    url = "/api/users"

    def test_list_users(self, client, user: User):
        """Test listing all users."""
        response = client.get(self.url)
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(body["results"]) == 1
        assert body["results"][0]["id"] == user.id

    def test_list_users_with_keyword(self, user: User, client):
        """Tests listing users with filtering options.
        Basically searching for users."""
        params = parse.urlencode({"keyword": "john"})
        response = client.get(self.url, params=params)
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(body["results"]) == 1
        assert body["results"][0]["id"] == user.id


class TestRetrieveUser:
    """Tests user detail endpoints."""

    url = "api/users/"

    def get_url(self, username: str):
        """Returns url for user with given username."""
        return self.url + username

    def test_retrieve_user(self, client, user: User):
        """Tests user detail endpoint."""
        response = client.get(self.get_url(cast(str, user.username)))

        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_user_not_found(self, client):
        """Tests getting detail for user with username which does not exist."""
        response = client.get(self.get_url("dummyuser"))

        assert response.status_code == status.HTTP_404_NOT_FOUND
