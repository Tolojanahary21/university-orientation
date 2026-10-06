from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.main import app
from app.models.enums import UserRole


class FakeAdmin:
    role = UserRole.ADMIN


def test_trace_id_is_generated_and_echoed():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert UUID(response.headers["X-Trace-Id"])


def test_trace_id_is_preserved():
    client = TestClient(app)
    trace_id = "25b59dd7-4b79-4943-83f3-37b53f5db6a4"
    response = client.get("/health", headers={"X-Trace-Id": trace_id})
    assert response.headers["X-Trace-Id"] == trace_id


def test_admin_stats_requires_admin():
    client = TestClient(app)
    response = client.get("/admin/stats")
    assert response.status_code == 401


def test_admin_stats_checks_role():
    client = TestClient(app)
    app.dependency_overrides[get_current_user] = lambda: type(
        "Student", (), {"role": UserRole.STUDENT, "is_active": True}
    )()
    try:
        response = client.get("/admin/stats")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
