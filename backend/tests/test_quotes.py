def get_auth_headers(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "test-user@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 200

    return {
        "Authorization": (
            f"Bearer {response.json()['access_token']}"
        )
    }


def create_job_card(client, headers):
    customer_response = client.post(
        "/customers/",
        headers=headers,
        json={
            "first_name": "Quote",
            "last_name": "Customer",
            "email": "quote-customer@example.com",
            "phone": "0821117000"
        }
    )

    assert customer_response.status_code == 200
    customer_id = customer_response.json()["id"]

    vehicle_response = client.post(
        "/vehicles/",
        headers=headers,
        json={
            "customer_id": customer_id,
            "registration": "QUOTE 168 GP",
            "vin": "QUOTE1234567890123",
            "make": "BMW",
            "model": "M3",
            "year": 2022,
            "mileage": 48000
        }
    )

    assert vehicle_response.status_code == 200
    vehicle_id = vehicle_response.json()["id"]

    job_response = client.post(
        "/job-cards/",
        headers=headers,
        json={
            "vehicle_id": vehicle_id,
            "description": "Brake inspection and repair",
            "estimated_cost": "5000.00"
        }
    )

    assert job_response.status_code == 200
    return job_response.json()["id"]


def test_create_quote(client, test_user):
    headers = get_auth_headers(client)
    job_card_id = create_job_card(client, headers)

    response = client.post(
        "/quotes/",
        headers=headers,
        json={
            "job_card_id": job_card_id,
            "items": [
                {
                    "description": "Brake pads",
                    "quantity": 1,
                    "unit_price": "2100.00"
                },
                {
                    "description": "Brake discs",
                    "quantity": 2,
                    "unit_price": "2250.00"
                }
            ]
        }
    )

    assert response.status_code == 200

    quote = response.json()

    assert quote["job_card_id"] == job_card_id
    assert quote["subtotal"] == "6600.00"
    assert quote["vat"] == "990.00"
    assert quote["total"] == "7590.00"


def test_quote_list_pagination(client, test_user):
    headers = get_auth_headers(client)

    response = client.get(
        "/quotes/?page=1&page_size=10",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
