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


def test_payment_summary_filters_by_date_range(client, db, test_user):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    first = create_payment(
        client, headers, invoice["id"], "100.00", "DATE-FILTER-JAN"
    )
    second = create_payment(
        client, headers, invoice["id"], "250.00", "DATE-FILTER-FEB"
    )

    payment_jan = db.query(models.Payment).filter(
        models.Payment.id == first["id"]
    ).one()
    payment_feb = db.query(models.Payment).filter(
        models.Payment.id == second["id"]
    ).one()

    payment_jan.paid_at = datetime(2026, 1, 15, 12, 0, 0)
    payment_feb.paid_at = datetime(2026, 2, 15, 12, 0, 0)
    db.flush()

    response = client.get(
        "/reports/payment-summary",
        params={
            "start_date": "2026-01-01T00:00:00",
            "end_date": "2026-01-31T23:59:59",
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    summary = response.json()
    assert summary["total_payments"] == 1
    assert Decimal(str(summary["total_received"])) == Decimal("100.00")
    assert Decimal(str(summary["active_received"])) == Decimal("100.00")


def test_payment_summary_returns_zero_for_empty_date_range(
    client, test_user
):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    create_payment(
        client, headers, invoice["id"], "100.00", "DATE-FILTER-EMPTY"
    )

    response = client.get(
        "/reports/payment-summary",
        params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2020-01-31T23:59:59",
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    summary = response.json()
    assert summary["total_payments"] == 0
    assert Decimal(str(summary["total_received"])) == Decimal("0.00")
    assert Decimal(str(summary["total_reversed"])) == Decimal("0.00")
    assert Decimal(str(summary["active_received"])) == Decimal("0.00")
