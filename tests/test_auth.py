import pytest


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "supersecret1"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "supersecret2"}
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


def test_register_duplicate_username(client):
    client.post(
        "/api/v1/auth/register",
        json={"username": "charlie", "email": "charlie1@example.com", "password": "supersecret3"},
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "charlie", "email": "charlie2@example.com", "password": "supersecret3"},
    )
    assert response.status_code == 409


def test_login_success(client):
    client.post(
        "/api/v1/auth/register",
        json={"username": "dave", "email": "dave@example.com", "password": "mypassword8"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "mypassword8"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"username": "eve", "email": "eve@example.com", "password": "correct1pass"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "eve@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_register_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "frank", "email": "frank@example.com", "password": "short"},
    )
    assert response.status_code == 422


def test_register_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "grace", "email": "not-an-email", "password": "goodpassword"},
    )
    assert response.status_code == 422


def test_logout_and_refresh_revoked(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={"username": "henry", "email": "henry@example.com", "password": "strongpassword1"},
    )
    tokens = reg.json()
    refresh_token = tokens["refresh_token"]

    logout_resp = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_resp.status_code == 204

    refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 401
