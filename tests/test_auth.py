"""
Pengujian endpoint autentikasi (/auth/register, /auth/login, /auth/me)
"""
import pytest
from app import create_app, db


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "test-secret"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client


def register_user(client, username="budi", email="budi@test.com", password="secret123"):
    return client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
    })


def login_user(client, email="budi@test.com", password="secret123"):
    return client.post("/auth/login", json={
        "email": email,
        "password": password,
    })


# ── Register ──────────────────────────────────────────────────────────────────

def test_register_success(client):
    res = register_user(client)
    assert res.status_code == 201
    data = res.get_json()
    assert data["message"] == "Registrasi berhasil"
    assert data["user"]["username"] == "budi"


def test_register_duplicate_username(client):
    register_user(client)
    res = register_user(client)  # Username sama
    assert res.status_code == 409
    assert "Username" in res.get_json()["error"]


def test_register_duplicate_email(client):
    register_user(client)
    res = register_user(client, username="budi2")  # Email sama
    assert res.status_code == 409


def test_register_short_password(client):
    res = register_user(client, password="123")
    assert res.status_code == 400


def test_register_missing_field(client):
    res = client.post("/auth/register", json={"username": "budi"})
    assert res.status_code == 400


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success(client):
    register_user(client)
    res = login_user(client)
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data


def test_login_wrong_password(client):
    register_user(client)
    res = login_user(client, password="wrongpassword")
    assert res.status_code == 401


def test_login_unknown_email(client):
    res = login_user(client, email="notfound@test.com")
    assert res.status_code == 401


# ── /auth/me ──────────────────────────────────────────────────────────────────

def test_get_me_with_token(client):
    register_user(client)
    token = login_user(client).get_json()["access_token"]
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["user"]["username"] == "budi"


def test_get_me_without_token(client):
    res = client.get("/auth/me")
    assert res.status_code == 401
