"""
Pengujian endpoint /health
Jalankan dengan: pytest tests/
"""
import pytest
from app import create_app, db


@pytest.fixture
def client():
    """Membuat test client dengan database SQLite in-memory."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client


def test_health_check(client):
    """Health check harus mengembalikan status 200 dan status healthy."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "version" in data


def test_health_check_content_type(client):
    """Response harus berupa JSON."""
    response = client.get("/health")
    assert response.content_type == "application/json"
