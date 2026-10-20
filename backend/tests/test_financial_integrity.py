def get_auth_headers(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "test-user@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_zero_payment_is_rejected(client, test_user):
    headers = get_auth_headers(client)

    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "invoice_id": 1,
            "amount": "0.00",
            "payment_method": "CASH"
        }
    )

    assert response.status_code == 422


def test_negative_payment_is_rejected(client, test_user):
    headers = get_auth_headers(client)

    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "invoice_id": 1,
            "amount": "-100.00",
            "payment_method": "CASH"
        }
    )

    assert response.status_code == 422


def test_invalid_payment_method_is_rejected(client, test_user):
    headers = get_auth_headers(client)

    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "invoice_id": 1,
            "amount": "100.00",
            "payment_method": "INVALID_METHOD"
        }
    )

    assert response.status_code == 422
