import models

def get_token(client, email, password):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_customer(client, headers):
    response = client.post(
        "/customers/",
        headers=headers,
        json={
            "first_name": "Archive",
            "last_name": "Test",
            "email": "archive-test@example.com",
            "phone": "0821234567"
        }
    )

    assert response.status_code == 200, response.text

    return response.json()["id"]


def test_customer_archive_and_restore_lifecycle(
    client,
    db,
    test_user
):
    token = get_token(
        client,
        "test-user@example.com",
        "TestPassword123!"
    )
    headers = auth_headers(token)

    customer_id = create_customer(client, headers)

    # Create a vehicle linked to the customer.
    vehicle_response = client.post(
        "/vehicles/",
        headers=headers,
        json={
            "customer_id": customer_id,
            "registration": "ARCHIVE 123 GP",
            "vin": "ARCHIVEVIN12345678",
            "make": "BMW",
            "model": "M3",
            "year": 2022,
            "mileage": 45000
        }
    )

    assert vehicle_response.status_code == 200, vehicle_response.text

    vehicle_id = vehicle_response.json()["id"]

    # Archive the customer.
    archive_response = client.delete(
        f"/customers/{customer_id}",
        headers=headers
    )

    assert archive_response.status_code == 200

    # Archived customer must disappear from normal listings.
    normal_list = client.get(
        "/customers/",
        headers=headers
    )

    assert normal_list.status_code == 200

    normal_ids = [
        customer["id"]
        for customer in normal_list.json()["items"]
    ]

    assert customer_id not in normal_ids

    # Archived customer must remain visible to an owner.
    archived_list = client.get(
        "/customers/?include_archived=true",
        headers=headers
    )

    assert archived_list.status_code == 200

    archived_ids = [
        customer["id"]
        for customer in archived_list.json()["items"]
    ]

    assert customer_id in archived_ids

    # Normal customer retrieval must reject archived records.
    archived_detail = client.get(
        f"/customers/{customer_id}",
        headers=headers
    )

    assert archived_detail.status_code == 404

    # The vehicle must still exist in the database.
    vehicle = db.query(models.Vehicle).filter(
        models.Vehicle.id == vehicle_id,
        models.Vehicle.business_id == test_user.business_id
    ).first()

    assert vehicle is not None
    assert vehicle.customer_id == customer_id

    # Restore the customer.
    restore_response = client.post(
        f"/customers/{customer_id}/restore",
        headers=headers
    )

    assert restore_response.status_code == 200, restore_response.text
    assert restore_response.json()["id"] == customer_id

    # Customer should now be accessible again.
    restored_detail = client.get(
        f"/customers/{customer_id}",
        headers=headers
    )

    assert restored_detail.status_code == 200

    # The restored customer should appear in the normal listing.
    restored_list = client.get(
        "/customers/",
        headers=headers
    )

    restored_ids = [
        customer["id"]
        for customer in restored_list.json()["items"]
    ]

    assert customer_id in restored_ids

    # Vehicle remains linked after restoration.
    vehicle_after_restore = db.query(models.Vehicle).filter(
        models.Vehicle.id == vehicle_id
    ).first()

    assert vehicle_after_restore is not None
    assert vehicle_after_restore.customer_id == customer_id


def test_customer_restore_is_tenant_scoped(
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

    headers_a = auth_headers(token_a)
    headers_b = auth_headers(token_b)

    customer_id = create_customer(client, headers_a)

    # Business A archives its customer.
    archive_response = client.delete(
        f"/customers/{customer_id}",
        headers=headers_a
    )

    assert archive_response.status_code == 200

    # Business B must not be able to restore Business A's customer.
    restore_response = client.post(
        f"/customers/{customer_id}/restore",
        headers=headers_b
    )

    assert restore_response.status_code == 404

    # Business A must still be able to restore its own customer.
    owner_restore = client.post(
        f"/customers/{customer_id}/restore",
        headers=headers_a
    )

    assert owner_restore.status_code == 200