def test_root(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["product"] == "HRN Cloud AutoVault"
    assert data["status"] == "running"
    assert data["version"] == "0.1.0"


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"