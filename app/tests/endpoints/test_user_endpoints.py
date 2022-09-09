import os
import tempfile
from urllib import parse

import pytest
from PIL import Image

from config import BASE_DIR
from jwt import create_refresh_token, create_access_token
from tests.conftest import user_password


class TestRegisterUser:
    """Class for testing `/api/register` endpoint."""
    url = "/api/register"
    user_data = {
        "username": "peterdoe",
        "email": "peterdoe@example.com",
        "first_name": "Peter",
        "last_name": "Doe",
        "password": user_password
    }

    def test_register_success(self, client):
        """Test successful user register."""
        response = client.post(self.url, json=self.user_data)

        assert response.status_code == 201
        body = response.json()

        assert body['username'] == self.user_data['username']
        assert body['email'] == self.user_data['email']
        assert body['first_name'] == self.user_data['first_name']
        assert body['last_name'] == self.user_data['last_name']

    def test_register_missing_fields(self, client):
        """Test user register with bad data"""
        response = client.post(self.url, json={
            "username": "peterdoe",
            "password": "dummy_pass"
        })

        assert response.status_code == 422

    def test_register_user_with_existing_username(self, client, user):
        """Test registering user with existing username."""
        response = client.post(self.url, json={
            **self.user_data,
            "email": "peterdoe2@example.com",
        })

        assert response.status_code == 400
        assert (response.json()['detail'] ==
                "User with given username already exists.")

    def test_register_user_with_existing_email(self, client, user):
        """Test registering user with existing email."""
        response = client.post(self.url, json={
            **self.user_data,
            "username": "peterdoe2"
        })

        assert response.status_code == 400
        assert (response.json()['detail'] ==
                "User with given email already exists.")


class TestToken:
    """Test token and refresh endpoint."""
    token_url = "/api/token"
    refresh_url = "/api/refresh"

    def test_token_success(self, client, user):
        """Test successful token creation endpoint"""
        user_data = {
            "username": user.username,
            "password": user_password
        }
        response = client.post(self.token_url, data=user_data)

        assert response.status_code == 201
        assert response.json().keys() == frozenset({"access_token",
                                                    "refresh_token"})

    def test_token_invalid_credentials(self, client, user):
        """Test token create with invalid credentials attempt."""
        user_data = {
            "username": user.username,
            "password": user_password + "wrong"
        }
        response = client.post(self.token_url, data=user_data)

        assert response.status_code == 400
        assert response.json()['detail'] == "Invalid username or password"

    def test_refresh_success(self, client, user):
        """Test refresh endpoint successful attempt."""
        refresh_token = create_refresh_token(user.id)
        response = client.post(self.refresh_url,
                               data={"refresh_token": refresh_token})

        assert response.status_code == 201
        assert response.json().keys() == frozenset({"access_token",
                                                    "refresh_token"})

    def test_refresh_bad_data(self, client, user):
        """Test refresh endpoint with invalid refresh token."""
        refresh_token = create_access_token(user.id)
        response = client.post(self.refresh_url,
                               data={"refresh_token": refresh_token})

        assert response.status_code == 401
        assert response.json()['detail'] == "Could not validate credentials"


class TestUsersMe:
    """Test authenticated user endpoint."""
    url = "/api/users/me"
    image_url = "/api/users/me/image"

    @pytest.fixture(scope="function")
    def profile_picture(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            yield image_file
            os.remove(image_file.name)

    def test_get_user_successful(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == 200

    def test_get_user_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == 401

    def test_modify_user(self, auth_client):
        payload = {
            "username": "johndoe_new",
            "email": "johndoe_new@gmail.com",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = auth_client.put(self.url, json=payload)

        assert response.status_code == 200
        body = response.json()
        for field in payload:
            assert body[field] == payload[field]

    def test_partial_modify_user(self, auth_client):
        payload = {
            "username": "johndoe2",
        }
        response = auth_client.patch(self.url, json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["username"] == payload["username"]

    def test_image_upload(self, user, auth_client, profile_picture):
        files = {"profile_picture": profile_picture}
        response = auth_client.post(self.image_url, files=files)

        assert response.status_code == 200
        body = response.json()
        path = BASE_DIR / ("app" + body['profile_picture'])
        assert os.path.exists(path)

        # teardown
        os.remove(path)
        dir_path = BASE_DIR / "app" / "static" / str(user.id)
        os.rmdir(dir_path)

    def test_delete_user(self, auth_client):
        response = auth_client.delete(self.url)

        assert response.status_code == 204


class TestListUsers:
    url = "/api/users"

    def test_list_users(self, client):
        response = client.get(self.url)
        assert response.status_code == 200

    def test_list_users_with_keyword(self, user, client):
        # TODO needs to be more functional
        params = parse.urlencode({'keyword': 'john'})
        response = client.get(self.url, params=params)

        assert response.status_code == 200


class TestRetrieveUser:
    def test_retrieve_user(self, client, user):
        # TODO needs to be more functional
        url = f"/api/users/{user.id}"
        client.get(url)
