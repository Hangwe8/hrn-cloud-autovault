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


def test_create_service_record(client, test_user):
    headers = get_auth_headers(client)

    customer_response = client.post(
        "/customers/",
        headers=headers,
        json={
            "first_name": "Service",
            "last_name": "Owner",
            "email": "service-owner@example.com",
            "phone": "0821115555"
        }
    )

    assert customer_response.status_code == 200
    customer_id = customer_response.json()["id"]

    vehicle_response = client.post(
        "/vehicles/",
        headers=headers,
        json={
            "customer_id": customer_id,
            "registration": "SERVICE 167 GP",
            "vin": "SERVICEVIN12345678",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2021,
            "mileage": 60000
        }
    )

    assert vehicle_response.status_code == 200
    vehicle_id = vehicle_response.json()["id"]

    service_response = client.post(
        "/service-records/",
        headers=headers,
        json={
            "vehicle_id": vehicle_id,
            "mileage": 60000,
            "description": "Oil and filter replacement",
            "parts_cost": "850.00",
            "labour_cost": "450.00",
            "total_cost": "1300.00",
            "technician": "Test Technician"
        }
    )

    assert service_response.status_code == 200

    service = service_response.json()

    assert service["vehicle_id"] == vehicle_id
    assert service["description"] == "Oil and filter replacement"
    assert float(service["total_cost"]) == 1300.00


def test_service_record_list(client, test_user):
    headers = get_auth_headers(client)

    response = client.get(
        "/service-records/?page=1&page_size=10",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 10