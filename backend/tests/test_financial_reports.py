from decimal import Decimal
from datetime import datetime

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


def test_payment_summary_distinguishes_reversed_and_active_payments(
    client, test_user
):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    active_payment = create_payment(
        client, headers, invoice["id"], "500.00", "REPORT-ACTIVE"
    )
    reversed_payment = create_payment(
        client, headers, invoice["id"], "200.00", "REPORT-REVERSED"
    )

    reversal_response = client.post(
        f"/payments/{reversed_payment['id']}/reverse",
        headers=headers,
        json={"reason": "Reporting integrity test"},
    )
    assert reversal_response.status_code == 200, reversal_response.text

    response = client.get(
        "/reports/payment-summary",
        headers=headers,
    )
    assert response.status_code == 200, response.text

    summary = response.json()

    assert summary["total_payments"] == 2
    assert Decimal(str(summary["total_received"])) == Decimal("700.00")
    assert Decimal(str(summary["total_reversed"])) == Decimal("200.00")
    assert Decimal(str(summary["active_received"])) == Decimal("500.00")


def test_monthly_revenue_excludes_reversed_payments(client, test_user):
    headers = get_auth_headers(client)
    invoice = create_test_invoice(client, headers)

    active_payment = create_payment(
        client, headers, invoice["id"], "500.00", "MONTHLY-ACTIVE"
    )
    reversed_payment = create_payment(
        client, headers, invoice["id"], "200.00", "MONTHLY-REVERSED"
    )

    reversal_response = client.post(
        f"/payments/{reversed_payment['id']}/reverse",
        headers=headers,
        json={"reason": "Monthly revenue test"},
    )
    assert reversal_response.status_code == 200, reversal_response.text

    response = client.get(
        "/reports/monthly-revenue",
        headers=headers,
    )
    assert response.status_code == 200, response.text

    month = datetime.fromisoformat(
        active_payment["paid_at"].replace("Z", "+00:00")
    ).strftime("%Y-%m")

    monthly_rows = response.json()
    current_month_rows = [
        row for row in monthly_rows if row["month"] == month
    ]

    assert current_month_rows, (
        f"Expected a revenue row for {month}; received {monthly_rows}"
    )

    revenue = sum(
        (Decimal(str(row["revenue"])) for row in current_month_rows),
        Decimal("0.00"),
    )

    assert revenue == Decimal("500.00")


def test_financial_reports_are_isolated_by_business(
    client, test_user, second_user
):
    headers_a = get_auth_headers(client)

    login_b = client.post(
        "/auth/login",
        json={
            "email": "second-user@example.com",
            "password": "SecondPassword123!",
        },
    )
    assert login_b.status_code == 200, login_b.text

    headers_b = {
        "Authorization": f"Bearer {login_b.json()['access_token']}"
    }

    invoice = create_test_invoice(client, headers_a)

    create_payment(
        client, headers_a, invoice["id"], "300.00", "TENANT-REPORT-TEST"
    )

    summary_response = client.get(
        "/reports/payment-summary",
        headers=headers_b,
    )
    assert summary_response.status_code == 200, summary_response.text

    summary = summary_response.json()
    assert summary["total_payments"] == 0
    assert Decimal(str(summary["total_received"])) == Decimal("0.00")
    assert Decimal(str(summary["total_reversed"])) == Decimal("0.00")
    assert Decimal(str(summary["active_received"])) == Decimal("0.00")

    revenue_response = client.get(
        "/reports/monthly-revenue",
        headers=headers_b,
    )
    assert revenue_response.status_code == 200, revenue_response.text
    assert revenue_response.json() == []

    reversals_response = client.get(
        "/reports/payment-reversals",
        headers=headers_b,
    )
    assert reversals_response.status_code == 200, reversals_response.text
    assert reversals_response.json() == []
