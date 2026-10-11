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


def test_create_job_card(client, test_user):
    headers = get_auth_headers(client)
    customer_response = client.post(
        "/customers/",
        headers=headers,
        json={
            "first_name": "Job",
            "last_name": "Customer",
            "email": "job-customer@example.com",
            "phone": "0821116666"
        }
    )

    assert customer_response.status_code == 200
    customer_id = customer_response.json()["id"]

    vehicle_response = client.post(
        "/vehicles/",
        headers=headers,
        json={
            "customer_id": customer_id,
            "registration": "JOB 168 GP",
            "vin": "JOBVIN12345678901",
            "make": "Volkswagen",
            "model": "Golf GTI",
            "year": 2022,
            "mileage": 35000
        }
    )

    assert vehicle_response.status_code == 200
    vehicle_id = vehicle_response.json()["id"]

    job_response = client.post(
        "/job-cards/",
        headers=headers,
        json={
            "vehicle_id": vehicle_id,
            "description": (
                "Inspect front brakes and investigate "
                "vibration under braking."
            ),
            "estimated_cost": "4500.00"
        }
    )

    assert job_response.status_code == 200

    job = job_response.json()

    assert job["vehicle_id"] == vehicle_id
    assert job["description"] == (
        "Inspect front brakes and investigate "
        "vibration under braking."
    )
    assert job["business_id"] == test_user.business_id


def test_job_card_list_pagination(client, test_user):
    headers = get_auth_headers(client)

    response = client.get(
        "/job-cards/?page=1&page_size=10",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
