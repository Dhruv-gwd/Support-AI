"""
Auth, registration, and single-tenant bootstrap.

Covers the exact bug we hit manually this session: every signup used to
create its own tenant and become admin of it. These tests pin down the
fixed behavior so a future change can't silently reintroduce it.
"""
from conftest import register, auth_headers


def test_register_returns_a_usable_token(client):
    resp, token = register(client)
    assert resp.status_code == 201
    assert token

    me = client.get("/api/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"


def test_first_user_ever_becomes_admin(client):
    resp, token = register(client, email="first@example.com")
    assert resp.status_code == 201

    me = client.get("/api/auth/me", headers=auth_headers(token))
    assert me.json()["role"] == "admin"


def test_second_user_joins_as_plain_user_not_a_new_admin(client):
    """This is the regression test for the bug we found manually: a
    second signup must NOT get its own tenant or admin rights."""
    register(client, email="first@example.com")
    resp2, token2 = register(client, email="second@example.com")
    assert resp2.status_code == 201

    me2 = client.get("/api/auth/me", headers=auth_headers(token2))
    assert me2.json()["role"] == "user"


def test_second_user_shares_the_same_tenant_as_the_first(client):
    _, token1 = register(client, email="first@example.com")
    _, token2 = register(client, email="second@example.com")

    admin_only = client.get(
        "/api/admin/users", headers=auth_headers(token1)
    )
    assert admin_only.status_code == 200
    emails = {u["email"] for u in admin_only.json()}
    # Both users should be visible to the admin, because they're in the
    # same workspace — proves they weren't split into separate tenants.
    assert emails == {"first@example.com", "second@example.com"}


def test_duplicate_email_registration_is_rejected(client):
    register(client, email="dupe@example.com")
    resp, _ = register(client, email="dupe@example.com")
    assert resp.status_code == 400


def test_password_too_short_is_rejected(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "short@example.com", "password": "short", "full_name": "X"},
    )
    assert resp.status_code == 422


def test_login_with_correct_credentials_succeeds(client):
    register(client, email="login@example.com", password="correct-horse-battery")
    resp = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "correct-horse-battery"},
    )
    assert resp.status_code == 200
    assert resp.json().get("access_token")


def test_login_with_wrong_password_fails(client):
    register(client, email="login2@example.com", password="correct-horse-battery")
    resp = client.post(
        "/api/auth/login",
        json={"email": "login2@example.com", "password": "totally-wrong-password"},
    )
    assert resp.status_code == 401


def test_login_with_unknown_email_fails(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "whatever-password-here"},
    )
    assert resp.status_code == 401


def test_protected_route_without_token_is_rejected(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_protected_route_with_garbage_token_is_rejected(client):
    resp = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


def test_protected_route_with_malformed_auth_header_is_rejected(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "not-even-bearer-format"})
    assert resp.status_code == 401
