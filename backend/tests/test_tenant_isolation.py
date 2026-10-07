def get_token(client, email, password):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }

def test_customer_isolation(
    client,
    db,
    test_user,
    second_user
):
    token_a = get_token(
        client,
        "test-user@example.com",
        "TestPassword123!"
    )

    token_b = get_token(
        client,
        "second-user@example.com",
        "SecondPassword123!"
    )

    customer = {
        "first_name": "Private",
        "last_name": "Customer",
        "email": "private@example.com",
        "phone": "0820000001"
    }

    create_response = client.post(
        "/customers/",
        json=customer,
        headers=auth_headers(token_a)
    )

    assert create_response.status_code == 200

    customer_id = create_response.json()["id"]

    response = client.get(
        f"/customers/{customer_id}",
        headers=auth_headers(token_b)
    )

    assert response.status_code == 404

def test_vehicle_isolation(
    client,
    db,
    test_user,
    second_user
):
    token_a = get_token(
        client,
        "test-user@example.com",
        "TestPassword123!"
    )

    token_b = get_token(
        client,
        "second-user@example.com",
        "SecondPassword123!"
    )

    customer_response = client.post(
        "/customers/",
        json={
            "first_name": "Vehicle",
            "last_name": "Owner",
            "email": "vehicle@example.com",
            "phone": "0820000002"
        },
        headers=auth_headers(token_a)
    )

    assert customer_response.status_code == 200

    customer_id = customer_response.json()["id"]

    vehicle_response = client.post(
        "/vehicles/",
        json={
            "customer_id": customer_id,
            "registration": "TEST 123 GP",
            "vin": "TESTVIN123456789",
            "make": "BMW",
            "model": "M3",
            "year": 2022,
            "mileage": 50000
        },
        headers=auth_headers(token_a)
    )

    assert vehicle_response.status_code == 200

    vehicle_id = vehicle_response.json()["id"]

    response = client.get(
        f"/vehicles/{vehicle_id}",
        headers=auth_headers(token_b)
    )

    assert response.status_code == 404

def test_customer_list_isolation(
    client,
    test_user,
    second_user
):
    token_a = get_token(
        client,
        "test-user@example.com",
        "TestPassword123!"
    )

    token_b = get_token(
        client,
        "second-user@example.com",
        "SecondPassword123!"
    )

    response = client.post(
        "/customers/",
        json={
            "first_name": "Hidden",
            "last_name": "Customer",
            "email": "hidden@example.com",
            "phone": "0820000003"
        },
        headers=auth_headers(token_a)
    )

    assert response.status_code == 200

    customer_id = response.json()["id"]

    response = client.get(
        "/customers/",
        headers=auth_headers(token_b)
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = [
        customer["id"]
        for customer in data["items"]
    ]

    assert customer_id not in returned_ids

def test_dashboard_isolation(
    client,
    test_user,
    second_user
):
    token_a = get_token(
        client,
        "test-user@example.com",
        "TestPassword123!"
    )

    token_b = get_token(
        client,
        "second-user@example.com",
        "SecondPassword123!"
    )

    response = client.get(
        "/dashboard/",
        headers=auth_headers(token_b)
    )

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["total_customers"] == 0
    assert data["summary"]["total_vehicles"] == 0