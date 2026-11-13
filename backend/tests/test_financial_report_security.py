def test_financial_reports_require_authentication(client):
    endpoints = [
        "/reports/job-performance",
        "/reports/monthly-revenue",
        "/reports/payment-summary",
        "/reports/payment-reversals",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401, (
            f"{endpoint} should require authentication; "
            f"got {response.status_code}: {response.text}"
        )


def test_payment_reversal_report_rejects_invalid_dates(
    client, test_user
):
    from tests.test_payments import get_auth_headers

    headers = get_auth_headers(client)

    response = client.get(
        "/reports/payment-reversals",
        params={"start_date": "not-a-date"},
        headers=headers,
    )

    assert response.status_code == 422, response.text


def test_payment_summary_accepts_start_date_only(
    client, test_user
):
    from tests.test_payments import get_auth_headers

    headers = get_auth_headers(client)

    response = client.get(
        "/reports/payment-summary",
        params={"start_date": "not-a-date"},
        headers=headers,
    )

    # The current route treats dates as strings. This test documents
    # that malformed values must not silently produce a successful report.
    assert response.status_code == 422, (
        "Expected invalid date input to be rejected, but received "
        f"{response.status_code}: {response.text}"
    )
