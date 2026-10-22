import models
from decimal import Decimal

def get_token(client, email, password):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_invoice(client, token, suffix):
    auth = headers(token)

    customer_response = client.post(
        "/customers/",
        headers=auth,
        json={
            "first_name": "Financial",
            "last_name": f"Test{suffix}",
            "email": f"financial-{suffix}@example.com",
            "phone": "0821119000"
        }
    )
    assert customer_response.status_code == 200, customer_response.text
    customer_id = customer_response.json()["id"]

    vehicle_response = client.post(
        "/vehicles/",
        headers=auth,
        json={
            "customer_id": customer_id,
            "registration": f"FIN{suffix} GP",
            "vin": f"FINANCIALVIN{suffix}123",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "mileage": 30000
        }
    )
    assert vehicle_response.status_code == 200, vehicle_response.text
    vehicle_id = vehicle_response.json()["id"]

    job_response = client.post(
        "/job-cards/",
        headers=auth,
        json={
            "vehicle_id": vehicle_id,
            "description": "Financial isolation test",
            "estimated_cost": "1150.00"
        }
    )
    assert job_response.status_code == 200, job_response.text
    job_id = job_response.json()["id"]

    quote_response = client.post(
        "/quotes/",
        headers=auth,
        json={
            "job_card_id": job_id,
            "items": [
                {
                    "description": "Workshop service",
                    "quantity": 1,
                    "unit_price": "1000.00"
                }
            ]
        }
    )
    assert quote_response.status_code == 200, quote_response.text
    quote_id = quote_response.json()["id"]

    for status in ("SENT", "APPROVED"):
        status_response = client.patch(
            f"/quotes/{quote_id}/status",
            headers=auth,
            json={"status": status}
        )
        assert status_response.status_code == 200, status_response.text

    invoice_response = client.post(
        f"/invoices/from-quote/{quote_id}",
        headers=auth
    )
    assert invoice_response.status_code == 201, invoice_response.text
    return invoice_response.json()


def create_payment(client, token, invoice_id):
    response = client.post(
        "/payments/",
        headers=headers(token),
        json={
            "invoice_id": invoice_id,
            "amount": "100.00",
            "payment_method": "EFT",
            "reference": "TENANT-ISOLATION-TEST"
        }
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_other_business_cannot_read_invoice_or_balance(
    client, test_user, second_user
):
    token_a = get_token(
        client, "test-user@example.com", "TestPassword123!"
    )
    token_b = get_token(
        client, "second-user@example.com", "SecondPassword123!"
    )

    invoice = create_invoice(client, token_a, "A")

    invoice_response = client.get(
        f"/invoices/{invoice['id']}",
        headers=headers(token_b)
    )
    assert invoice_response.status_code == 404

    balance_response = client.get(
        f"/invoices/{invoice['id']}/balance",
        headers=headers(token_b)
    )
    assert balance_response.status_code == 404

    payment_balance_response = client.get(
        f"/payments/invoice/{invoice['id']}/balance",
        headers=headers(token_b)
    )
    assert payment_balance_response.status_code == 404


def test_other_business_cannot_list_invoice_payments(
    client, test_user, second_user
):
    token_a = get_token(
        client, "test-user@example.com", "TestPassword123!"
    )
    token_b = get_token(
        client, "second-user@example.com", "SecondPassword123!"
    )

    invoice = create_invoice(client, token_a, "B")
    payment = create_payment(client, token_a, invoice["id"])

    # The invoice itself is inaccessible to Business B.
    response = client.get(
        f"/payments/invoice/{invoice['id']}",
        headers=headers(token_b)
    )
    assert response.status_code == 404

    # Business B's general payment list must not expose this payment.
    response = client.get(
        "/payments/",
        headers=headers(token_b)
    )
    assert response.status_code == 200, response.text

    body = response.json()
    items = body["items"]
    returned_payment_ids = [item["id"] for item in items]

    assert payment["id"] not in returned_payment_ids




def test_other_business_cannot_reverse_payment(
    client, db, test_user, second_user
):
    token_a = get_token(
        client, "test-user@example.com", "TestPassword123!"
    )
    token_b = get_token(
        client, "second-user@example.com", "SecondPassword123!"
    )

    invoice = create_invoice(client, token_a, "C")
    payment = create_payment(client, token_a, invoice["id"])

    response = client.post(
        f"/payments/{payment['id']}/reverse",
        headers=headers(token_b),
        json={"reason": "Unauthorized cross-business test"}
    )
    assert response.status_code == 404, response.text

    user_a_id = test_user.id
    user_b_id = second_user.id

    # Diagnose the database state without using expired ORM objects.
    db.expire_all()

    user_a = db.query(models.User).filter(
        models.User.id == user_a_id
    ).first()

    user_b = db.query(models.User).filter(
        models.User.id == user_b_id
    ).first()

    print("USER A ID:", user_a_id)
    print("USER A AFTER REVERSAL:", user_a)
    print("USER B ID:", user_b_id)
    print("USER B AFTER REVERSAL:", user_b)

    balance_response = client.get(
        f"/payments/invoice/{invoice['id']}/balance",
        headers=headers(token_a)
    )

    assert balance_response.status_code == 200, balance_response.text

    balance = balance_response.json()
    assert balance["status"] == "PARTIALLY_PAID"
    assert Decimal(str(balance["amount_paid"])) == Decimal("100.00")