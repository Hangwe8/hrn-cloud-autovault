def get_auth_headers(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "test-user@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_customer_create_and_retrieve(client, test_user):
    headers = get_auth_headers(client)

    create_response = client.post(
        "/customers/",
        headers=headers,
        json={
            "first_name": "Integration",
            "last_name": "Customer",
            "email": "integration@example.com",
            "phone": "0821112222"
        }
    )

    assert create_response.status_code == 200

    customer = create_response.json()

    assert customer["first_name"] == "Integration"
    assert customer["last_name"] == "Customer"
    assert customer["business_id"] == test_user.business_id

    customer_id = customer["id"]

    retrieve_response = client.get(
        f"/customers/{customer_id}",
        headers=headers
    )

    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["id"] == customer_id


def test_customer_search(client, test_user):
    headers = get_auth_headers(client)

    client.post(
        "/customers/",
        headers=headers,
        json={
            "first_name": "Searchable",
            "last_name": "Customer",
            "email": "searchable@example.com",
            "phone": "0821113333"
        }
    )

    response = client.get(
        "/customers/?search=Searchable",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["first_name"] == "Searchable"
        for item in data["items"]
    )


def test_customer_list_pagination(client, test_user):
    headers = get_auth_headers(client)

    response = client.get(
        "/customers/?page=1&page_size=10",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
