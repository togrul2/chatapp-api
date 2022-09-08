from jwt import create_refresh_token, create_access_token
from tests.conftest import user_password


class TestRegisterUser:
    """Class for testing `/api/register` endpoint."""
    url = "/api/register"
    user_data = {
        "username": "johndoe",
        "email": "johndoe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": user_password
    }

    def test_register_success(self, client):
        """Test successful user register."""
        response = client.post(self.url, json=self.user_data)

        assert response.status_code == 201
        body = response.json()

        assert body['username'] == 'johndoe'
        assert body['email'] == 'johndoe@example.com'
        assert body['first_name'] == 'John'
        assert body['last_name'] == 'Doe'

    def test_register_missing_fields(self, client):
        """Test user register with bad data"""
        response = client.post(self.url, json={
            "username": "johndoe",
            "password": "dummy_pass"
        })

        assert response.status_code == 422

    def test_register_user_with_existing_username(self, client, user):
        """Test registering user with existing username."""
        response = client.post(self.url, json={
            **self.user_data,
            "email": "johndoe2@example.com",
        })

        assert response.status_code == 400
        assert (response.json()['detail'] ==
                "User with given username already exists.")

    def test_register_user_with_existing_email(self, client, user):
        """Test registering user with existing email."""
        response = client.post(self.url, json={
            **self.user_data,
            "username": "johndoe2"
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
                               json={"refresh_token": refresh_token})

        assert response.status_code == 201
        assert response.json().keys() == frozenset({"access_token",
                                                    "refresh_token"})

    def test_refresh_bad_data(self, client, user):
        """Test refresh endpoint with invalid refresh token."""
        refresh_token = create_access_token(user.id)
        response = client.post(self.refresh_url,
                               json={"refresh_token": refresh_token})

        # assert response.status_code == 401
        assert response.json()['detail'] == "Could not validate credentials"


class TestUsersMe:
    url = "/api/users/me"
