from fastapi.testclient import TestClient

from chatterlite.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "application": "ChatterLite API",
        "environment": "development",
        "version": "0.1.0",
    }