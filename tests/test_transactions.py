"""
Pengujian endpoint transaksi (/transactions)
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


@pytest.fixture
def auth_headers(client):
    """Helper: register + login dan kembalikan headers JWT."""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@test.com",
        "password": "password123",
    })
    res = client.post("/auth/login", json={
        "email": "test@test.com",
        "password": "password123",
    })
    token = res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_tx(client, headers, amount=50000, description="Makan siang",
              date="2026-05-08", tx_type="expense"):
    return client.post("/transactions", json={
        "amount": amount,
        "description": description,
        "date": date,
        "transaction_type": tx_type,
    }, headers=headers)


# ── GET /transactions ─────────────────────────────────────────────────────────

def test_get_transactions_empty(client, auth_headers):
    res = client.get("/transactions", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()["transactions"] == []


def test_get_transactions_unauthorized(client):
    res = client.get("/transactions")
    assert res.status_code == 401


# ── POST /transactions ────────────────────────────────────────────────────────

def test_create_transaction_success(client, auth_headers):
    res = create_tx(client, auth_headers)
    assert res.status_code == 201
    data = res.get_json()
    assert data["transaction"]["amount"] == 50000
    assert data["transaction"]["description"] == "Makan siang"


def test_create_transaction_missing_amount(client, auth_headers):
    res = client.post("/transactions", json={
        "description": "Test", "date": "2026-05-08"
    }, headers=auth_headers)
    assert res.status_code == 400


def test_create_transaction_negative_amount(client, auth_headers):
    res = create_tx(client, auth_headers, amount=-1000)
    assert res.status_code == 400


def test_create_transaction_invalid_date(client, auth_headers):
    res = create_tx(client, auth_headers, date="08-05-2026")
    assert res.status_code == 400


def test_create_transaction_invalid_type(client, auth_headers):
    res = client.post("/transactions", json={
        "amount": 10000, "description": "Test",
        "date": "2026-05-08", "transaction_type": "invalid"
    }, headers=auth_headers)
    assert res.status_code == 400


# ── GET /transactions/:id ─────────────────────────────────────────────────────

def test_get_transaction_by_id(client, auth_headers):
    tx_id = create_tx(client, auth_headers).get_json()["transaction"]["id"]
    res = client.get(f"/transactions/{tx_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()["transaction"]["id"] == tx_id


def test_get_transaction_not_found(client, auth_headers):
    res = client.get("/transactions/9999", headers=auth_headers)
    assert res.status_code == 404


# ── PUT /transactions/:id ─────────────────────────────────────────────────────

def test_update_transaction(client, auth_headers):
    tx_id = create_tx(client, auth_headers).get_json()["transaction"]["id"]
    res = client.put(f"/transactions/{tx_id}", json={
        "amount": 75000, "description": "Makan malam"
    }, headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()["transaction"]
    assert data["amount"] == 75000
    assert data["description"] == "Makan malam"


# ── DELETE /transactions/:id ──────────────────────────────────────────────────

def test_delete_transaction(client, auth_headers):
    tx_id = create_tx(client, auth_headers).get_json()["transaction"]["id"]
    res = client.delete(f"/transactions/{tx_id}", headers=auth_headers)
    assert res.status_code == 200

    # Pastikan sudah terhapus
    res2 = client.get(f"/transactions/{tx_id}", headers=auth_headers)
    assert res2.status_code == 404
