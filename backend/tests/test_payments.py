from decimal import Decimal
import models


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


def create_test_invoice(client, headers):
    customer_response = client.post(
        "/customers/",
        headers=headers,
        json={
            "first_name": "Payment",
            "last_name": "Customer",
            "email": "payment-customer@example.com",
            "phone": "0821119000"
        }
    )
    assert customer_response.status_code == 200

    customer_id = customer_response.json()["id"]

    vehicle_response = client.post(
        "/vehicles/",
        headers=headers,
        json={
            "customer_id": customer_id,
            "registration": "PAYMENT 169 GP",
            "vin": "PAYMENT12345678901",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "mileage": 30000
        }
    )
    assert vehicle_response.status_code == 200

    vehicle_id = vehicle_response.json()["id"]

    job_response = client.post(
        "/job-cards/",
        headers=headers,
        json={
            "vehicle_id": vehicle_id,
            "description": "Payment integration test",
            "estimated_cost": "1150.00"
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
                    "description": "Workshop service",
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
    approval_response = client.patch(
        f"/quotes/{quote_id}/status",
        headers=headers,
        json={"status": "APPROVED"}
    )

    assert approval_response.status_code == 200, (
        f"Failed to approve quote: {approval_response.text}"
    )

    invoice_response = client.post(
        f"/invoices/from-quote/{quote_id}",
        headers=headers
    )
    assert invoice_response.status_code in [200, 201]

    return invoice_response.json()

def test_partial_payment(client, test_user):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "invoice_id": invoice["id"],
            "amount": "500.00",
            "payment_method": "EFT",
            "reference": "TEST-PARTIAL-001"
        }
    )

    assert response.status_code in [200, 201]

    payment = response.json()

    assert payment["invoice_id"] == invoice["id"]
    assert Decimal(str(payment["amount"])) == Decimal("500.00")

    balance_response = client.get(
        f"/payments/invoice/{invoice['id']}/balance",
        headers=headers
    )

    assert balance_response.status_code == 200

    balance = balance_response.json()

    assert Decimal(str(balance["amount_paid"])) == Decimal("500.00")
    assert Decimal(str(balance["balance"])) == Decimal("650.00")
    assert balance["status"] == "PARTIALLY_PAID"

def test_full_payment_settles_invoice(client, test_user):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "invoice_id": invoice["id"],
            "amount": "1150.00",
            "payment_method": "CARD",
            "reference": "TEST-FULL-001"
        }
    )

    assert response.status_code in [200, 201]

    balance_response = client.get(
        f"/payments/invoice/{invoice['id']}/balance",
        headers=headers
    )

    assert balance_response.status_code == 200

    balance = balance_response.json()

    assert Decimal(str(balance["amount_paid"])) == Decimal("1150.00")
    assert Decimal(str(balance["balance"])) == Decimal("0.00")
    assert balance["status"] == "PAID"


def test_overpayment_is_rejected(client, test_user):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "invoice_id": invoice["id"],
            "amount": "1150.01",
            "payment_method": "EFT",
            "reference": "TEST-OVERPAY-001"
        }
    )

    assert response.status_code in [400, 422]


def test_payment_reversal_restores_invoice_balance(client, test_user):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    payment_response = client.post(
        "/payments/",
        headers=headers,
        json={
            "invoice_id": invoice["id"],
            "amount": "500.00",
            "payment_method": "EFT",
            "reference": "TEST-REVERSAL-001"
        }
    )

    assert payment_response.status_code in [200, 201]

    payment_id = payment_response.json()["id"]

    reversal_response = client.post(
        f"/payments/{payment_id}/reverse",
        headers=headers,
        json={
            "reason": "Integration test reversal"
        }
    )

    assert reversal_response.status_code == 200

    balance_response = client.get(
        f"/payments/invoice/{invoice['id']}/balance",
        headers=headers
    )

    assert balance_response.status_code == 200

    balance = balance_response.json()

    assert Decimal(str(balance["amount_paid"])) == Decimal("0.00")
    assert Decimal(str(balance["balance"])) == Decimal("1150.00")
    assert balance["status"] == "UNPAID"


def test_payment_reversal_preserves_record_and_audit_trail(
    client, db, test_user
):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    payment_response = client.post(
        "/payments/",
        headers=headers,
        json={
            "invoice_id": invoice["id"],
            "amount": "500.00",
            "payment_method": "EFT",
            "reference": "AUDIT-REVERSAL-001"
        }
    )
    assert payment_response.status_code in [200, 201], (
        payment_response.text
    )

    payment_id = payment_response.json()["id"]
    reason = "Customer payment entered incorrectly"

    reversal_response = client.post(
        f"/payments/{payment_id}/reverse",
        headers=headers,
        json={"reason": reason}
    )
    assert reversal_response.status_code == 200, (
        reversal_response.text
    )

    # The original payment must remain in the database.
    payment = (
        db.query(models.Payment)
        .filter(
            models.Payment.id == payment_id,
            models.Payment.business_id == test_user.business_id
        )
        .one()
    )

    assert payment.reversed_at is not None
    assert payment.reversal_reason == reason
    assert payment.amount == Decimal("500.00")

    # Exactly one reversal audit event must exist for this payment.
    audit_entries = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.business_id == test_user.business_id,
            models.AuditLog.action == "PAYMENT_REVERSED",
            models.AuditLog.entity_type == "Payment",
            models.AuditLog.entity_id == payment_id
        )
        .all()
    )

    assert len(audit_entries) == 1
    assert audit_entries[0].user_id == test_user.id
    assert reason in audit_entries[0].details


def test_reversing_payment_twice_does_not_duplicate_audit(
    client, db, test_user
):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    payment_response = client.post(
        "/payments/",
        headers=headers,
        json={
            "invoice_id": invoice["id"],
            "amount": "500.00",
            "payment_method": "EFT",
            "reference": "AUDIT-DOUBLE-REVERSAL"
        }
    )
    assert payment_response.status_code in [200, 201], (
        payment_response.text
    )

    payment_id = payment_response.json()["id"]
    reversal_payload = {
        "reason": "Duplicate reversal protection test"
    }

    first_response = client.post(
        f"/payments/{payment_id}/reverse",
        headers=headers,
        json=reversal_payload
    )
    assert first_response.status_code == 200, first_response.text

    second_response = client.post(
        f"/payments/{payment_id}/reverse",
        headers=headers,
        json=reversal_payload
    )
    assert second_response.status_code == 400, (
        second_response.text
    )

    audit_count = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.business_id == test_user.business_id,
            models.AuditLog.action == "PAYMENT_REVERSED",
            models.AuditLog.entity_type == "Payment",
            models.AuditLog.entity_id == payment_id
        )
        .count()
    )

    assert audit_count == 1