"""Admin-only routes must reject regular users, not just unauthenticated ones."""
from conftest import register, auth_headers


def _admin_and_user_tokens(client):
    _, admin_token = register(client, email="boss@example.com")
    _, user_token = register(client, email="employee@example.com")
    return admin_token, user_token


def test_admin_users_list_rejects_regular_user(client):
    _, user_token = _admin_and_user_tokens(client)
    resp = client.get("/api/admin/users", headers=auth_headers(user_token))
    assert resp.status_code == 403


def test_admin_users_list_allows_admin(client):
    admin_token, _ = _admin_and_user_tokens(client)
    resp = client.get("/api/admin/users", headers=auth_headers(admin_token))
    assert resp.status_code == 200


def test_admin_settings_rejects_regular_user(client):
    _, user_token = _admin_and_user_tokens(client)
    resp = client.get("/api/admin/settings", headers=auth_headers(user_token))
    assert resp.status_code == 403


def test_admin_settings_allows_admin_and_has_expected_fields(client):
    admin_token, _ = _admin_and_user_tokens(client)
    resp = client.get("/api/admin/settings", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    for field in (
        "tenant_name",
        "tenant_slug",
        "rate_limit_per_minute",
        "max_file_size_mb",
        "access_token_expire_minutes",
    ):
        assert field in body


def test_document_upload_rejects_regular_user(client):
    _, user_token = _admin_and_user_tokens(client)
    resp = client.post(
        "/api/documents/upload",
        headers=auth_headers(user_token),
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 403


def test_document_list_rejects_regular_user(client):
    _, user_token = _admin_and_user_tokens(client)
    resp = client.get("/api/documents", headers=auth_headers(user_token))
    assert resp.status_code == 403
