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


def create_approved_quote(client, headers):
    customer_response = client.post(
        "/customers/",
        headers=headers,
        json={
            "first_name": "Invoice",
            "last_name": "Customer",
            "email": "invoice-customer@example.com",
            "phone": "0821118000"
        }
    )

    assert customer_response.status_code == 200
    customer_id = customer_response.json()["id"]

    vehicle_response = client.post(
        "/vehicles/",
        headers=headers,
        json={
            "customer_id": customer_id,
            "registration": "INVOICE 168 GP",
            "vin": "INVOICE12345678901",
            "make": "Toyota",
            "model": "Supra",
            "year": 2023,
            "mileage": 20000
        }
    )

    assert vehicle_response.status_code == 200
    vehicle_id = vehicle_response.json()["id"]

    job_response = client.post(
        "/job-cards/",
        headers=headers,
        json={
            "vehicle_id": vehicle_id,
            "description": "Scheduled maintenance",
            "estimated_cost": "2000.00"
        }
    )

    assert job_response.status_code == 200
    job_card_id = job_response.json()["id"]

    quote_response = client.post(
        "/quotes/",
        headers=headers,
        json={
            "job_card_id": job_card_id,
            "items": [
                {
                    "description": "Oil service",
                    "quantity": 1,
                    "unit_price": "1000.00"
                }
            ]
        }
    )

    assert quote_response.status_code == 200
    quote_id = quote_response.json()["id"]

    # First, send the draft quote.
    send_response = client.patch(
        f"/quotes/{quote_id}/status",
        headers=headers,
        json={"status": "SENT"}
    )

    assert send_response.status_code == 200, (
        f"Failed to send quote: {send_response.text}"
    )

    # Next, approve the sent quote.
    approve_response = client.patch(
        f"/quotes/{quote_id}/status",
        headers=headers,
        json={"status": "APPROVED"}
    )

    assert approve_response.status_code == 200, (
        f"Failed to approve quote: {approve_response.text}"
    )

    return quote_id


def test_create_invoice_from_approved_quote(client, test_user):
    headers = get_auth_headers(client)
    quote_id = create_approved_quote(client, headers)

    response = client.post(
        f"/invoices/from-quote/{quote_id}",
        headers=headers
    )

    print("Invoice status:", response.status_code)
    print("Invoice response:", response.text)

    assert response.status_code in [200, 201], (
        f"Invoice creation failed: {response.text}"
    )

    invoice = response.json()

    assert invoice["quote_id"] == quote_id
    assert invoice["status"] in [
        "UNPAID",
        "PARTIALLY_PAID",
        "PAID"
    ]
    assert invoice["total"] == "1150.00"


def test_invoice_list_pagination(client, test_user):
    headers = get_auth_headers(client)

    response = client.get(
        "/invoices/?page=1&page_size=10",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 10

def test_duplicate_invoice_is_rejected(client, test_user):
    headers = get_auth_headers(client)
    quote_id = create_approved_quote(client, headers)

    first_response = client.post(
        f"/invoices/from-quote/{quote_id}",
        headers=headers
    )

    assert first_response.status_code in [200, 201]

    second_response = client.post(
        f"/invoices/from-quote/{quote_id}",
        headers=headers
    )

    assert second_response.status_code in [400, 409]