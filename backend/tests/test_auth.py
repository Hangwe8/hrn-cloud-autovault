def test_login_success(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "james@hrnautoworkshop.co.za",
            "password": "HRN2024"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_login_wrong_password(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "james@hrnautoworkshop.co.za",
            "password": "WrongHRN2024"
        }
    )

    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "doesnotexist@example.com",
            "password": "WrongHRN2024"
        }
    )

    assert response.status_code == 401


def test_auth_me_success(client):
    login_response = client.post(
        "/auth/login",
        json={
            "email": "james@hrnautoworkshop.co.za",
            "password": "HRN2024"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "james@hrnautoworkshop.co.za"
    assert data["business_id"] == 1


def test_auth_me_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code in [401, 403]


def test_auth_me_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer completely-invalid-token"
        }
    )

    assert response.status_code == 401
