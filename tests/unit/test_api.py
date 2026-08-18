from fastapi.testclient import TestClient

from mercury_rec.api import app


def test_liveness_returns_runtime_metadata() -> None:
    response = TestClient(app).get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["environment"] == "local"


def test_readiness_is_available_before_dependencies_are_added() -> None:
    response = TestClient(app).get("/health/ready")

    assert response.status_code == 200
    assert response.json()["model_version"] == "unconfigured"
