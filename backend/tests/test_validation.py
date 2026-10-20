def test_login_rejects_empty_json(client):
    response = client.post("/auth/login", json={})

    assert response.status_code == 422


def test_login_rejects_missing_password(client):
    response = client.post(
        "/auth/login",
        json={"email": "test-user@example.com"}
    )

    assert response.status_code == 422


def test_login_rejects_missing_email(client):
    response = client.post(
        "/auth/login",
        json={"password": "TestPassword123!"}
    )

    assert response.status_code == 422


def test_login_rejects_malformed_json(client):
    response = client.post(
        "/auth/login",
        content='{"email":',
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
