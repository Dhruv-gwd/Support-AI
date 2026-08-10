"""
Upload dedup and cross-tenant isolation.

Note on tenant isolation: registration is now single-tenant-per-deployment
by design (see test_auth.py), so the API itself won't create a second
tenant for us to test against. To exercise the isolation *mechanism*
(tenant_id filtering in the vector store + image store) we build a second
tenant directly in the DB here, the way a multi-instance/manual-migration
scenario would. This still proves the underlying guarantee holds even
though the register endpoint no longer exposes a way to trigger it.
"""
from app.models.database import Tenant, User
from app.services.auth_service import create_access_token, get_password_hash

from conftest import register, auth_headers


def test_uploading_same_filename_twice_replaces_not_duplicates(client):
    _, admin_token = register(client, email="admin@example.com")
    headers = auth_headers(admin_token)

    resp1 = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("policy.txt", b"Version one of the policy.", "text/plain")},
    )
    assert resp1.status_code == 200
    assert resp1.json()["chunks_added"] >= 1

    resp2 = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("policy.txt", b"Version two of the policy, much longer text this time around.", "text/plain")},
    )
    assert resp2.status_code == 200

    listed = client.get("/api/documents", headers=headers)
    sources = listed.json()["sources"]
    # The real bug this guards against: uploading the same filename twice
    # used to leave BOTH old and new chunks in the vector store. There
    # should be exactly one entry for "policy.txt", not chunks from both
    # versions coexisting.
    assert sources.count("policy.txt") == 1


def test_upload_rejects_disallowed_file_type(client):
    _, admin_token = register(client, email="admin@example.com")
    resp = client.post(
        "/api/documents/upload",
        headers=auth_headers(admin_token),
        files={"file": ("virus.exe", b"not a real document", "application/octet-stream")},
    )
    assert resp.status_code == 400


def _create_tenant_with_admin(db_session, email, tenant_name):
    """Directly create a second, isolated tenant + admin user, bypassing
    the (now intentionally single-tenant) /register endpoint."""
    tenant = Tenant(name=tenant_name, slug=tenant_name.lower().replace(" ", "-"))
    db_session.add(tenant)
    db_session.flush()

    user = User(
        email=email,
        hashed_password=get_password_hash("some-long-enough-password"),
        full_name="Tenant Admin",
        role="admin",
        tenant_id=tenant.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return tenant, user, token


def test_tenant_b_cannot_see_tenant_as_documents(client, db_session):
    _, admin_token_a = register(client, email="companyA@example.com")
    client.post(
        "/api/documents/upload",
        headers=auth_headers(admin_token_a),
        files={"file": ("secret-plan.txt", b"Confidential company A roadmap.", "text/plain")},
    )

    _, _, admin_token_b = _create_tenant_with_admin(
        db_session, "companyB@example.com", "Company B"
    )

    listed_b = client.get("/api/documents", headers=auth_headers(admin_token_b))
    assert listed_b.status_code == 200
    assert "secret-plan.txt" not in listed_b.json()["sources"]

    # Tenant B also must not be able to delete tenant A's document by name.
    delete_attempt = client.delete(
        "/api/documents/secret-plan.txt", headers=auth_headers(admin_token_b)
    )
    assert delete_attempt.status_code == 404

    # And tenant A should still see their own document, untouched.
    listed_a = client.get("/api/documents", headers=auth_headers(admin_token_a))
    assert "secret-plan.txt" in listed_a.json()["sources"]


def test_tenant_b_image_upload_does_not_collide_with_tenant_a(client, db_session, tmp_path, monkeypatch):
    """Regression test for the cross-tenant image-overwrite bug: two
    tenants uploading a same-named image must not overwrite each other's
    file on disk."""
    import app.api.documents as documents_module

    monkeypatch.setattr(documents_module, "IMAGES_DIR", str(tmp_path / "images"))
    import os
    os.makedirs(documents_module.IMAGES_DIR, exist_ok=True)

    _, admin_token_a = register(client, email="companyA2@example.com")
    _, _, admin_token_b = _create_tenant_with_admin(
        db_session, "companyB2@example.com", "Company B2"
    )

    png_bytes = b"\x89PNG\r\n\x1a\nfake-but-nonempty-image-bytes"

    resp_a = client.post(
        "/api/documents/upload",
        headers=auth_headers(admin_token_a),
        files={"file": ("logo.png", png_bytes + b"-A", "image/png")},
    )
    resp_b = client.post(
        "/api/documents/upload",
        headers=auth_headers(admin_token_b),
        files={"file": ("logo.png", png_bytes + b"-B", "image/png")},
    )
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    # Both files should exist on disk simultaneously, under different
    # tenant-prefixed names — neither should have overwritten the other.
    saved_files = os.listdir(documents_module.IMAGES_DIR)
    assert len(saved_files) == 2, (
        f"expected 2 distinct on-disk files for tenant A and B's 'logo.png', "
        f"got: {saved_files}"
    )
