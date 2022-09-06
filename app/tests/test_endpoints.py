from fastapi.testclient import TestClient


from main import app

client = TestClient(app)


class TestRegisterUser:
    url = "/api/register"

    def test_register_success(self):
        response = client.post(self.url, json={
            "username": "johndoe",
            "email": "johndoe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "memunlar"
        })
        assert response.status_code == 201
        assert response.json() == {
            "username": "johndoe",
            "email": "johndoe@example.com",
            "first_name": "John",
            "last_name": "Doe",
        }
        # with Session(engine) as session:
        #     session.query(User).delete()

    def test_register_missing_fields(self):
        response = client.post(self.url, json={
            "username": "johndoe",
            "password": "memunlar"
        })
        assert response.status_code == 422
        assert response.json() == {}
