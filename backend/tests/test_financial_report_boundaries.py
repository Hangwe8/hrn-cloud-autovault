from datetime import datetime
from decimal import Decimal

import models

from tests.test_payments import (
    get_auth_headers,
    create_test_invoice,
)


def create_payment(client, headers, invoice_id, amount, reference):
    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "invoice_id": invoice_id,
            "amount": str(amount),
            "payment_method": "EFT",
            "reference": reference,
        },
    )
    assert response.status_code in [200, 201], response.text
    return response.json()


def set_payment_date(db, payment_id, paid_at):
    payment = db.query(models.Payment).filter(
        models.Payment.id == payment_id
    ).one()
    payment.paid_at = paid_at
    db.flush()


def test_payment_summary_start_date_only(client, db, test_user):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    older = create_payment(
        client, headers, invoice["id"], "100.00", "START-OLD"
    )
    newer = create_payment(
        client, headers, invoice["id"], "200.00", "START-NEW"
    )

    set_payment_date(db, older["id"], datetime(2025, 12, 15, 12, 0))
    set_payment_date(db, newer["id"], datetime(2026, 1, 15, 12, 0))

    response = client.get(
        "/reports/payment-summary",
        params={"start_date": "2026-01-01T00:00:00"},
        headers=headers,
    )
    assert response.status_code == 200, response.text

    summary = response.json()
    assert summary["total_payments"] == 1
    assert Decimal(str(summary["total_received"])) == Decimal("200.00")


def test_payment_summary_end_date_only(client, db, test_user):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    older = create_payment(
        client, headers, invoice["id"], "100.00", "END-OLD"
    )
    newer = create_payment(
        client, headers, invoice["id"], "200.00", "END-NEW"
    )

    set_payment_date(db, older["id"], datetime(2026, 1, 15, 12, 0))
    set_payment_date(db, newer["id"], datetime(2026, 2, 15, 12, 0))

    response = client.get(
        "/reports/payment-summary",
        params={"end_date": "2026-01-31T23:59:59"},
        headers=headers,
    )
    assert response.status_code == 200, response.text

    summary = response.json()
    assert summary["total_payments"] == 1
    assert Decimal(str(summary["total_received"])) == Decimal("100.00")


def test_payment_summary_rejects_reversed_date_range(
    client, test_user
):
    headers = get_auth_headers(client)

    response = client.get(
        "/reports/payment-summary",
        params={
            "start_date": "2026-02-01T00:00:00",
            "end_date": "2026-01-01T00:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 422, response.text

