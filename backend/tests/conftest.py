"""
Shared pytest fixtures.

These tests never talk to a real Ollama server or a real, shared Chroma
store: they set SECRET_KEY / DATABASE_PATH to throwaway values *before*
the app is imported, and monkeypatch the embedding + vector-store calls so
`pytest` runs in seconds with no Docker services running. That's a
deliberate trade-off — it means these tests won't catch an actual Ollama
integration break, only the application logic around auth, uploads, and
tenant isolation. Catching real Ollama failures is what the manual
clean-machine rebuild test (docker compose up --build) is for.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# --- Set required env vars BEFORE importing anything from the app ---
# app/config.py raises at import time if SECRET_KEY is missing, and
# app/models/database.py picks its SQLite file from DATABASE_PATH at
# import time too. Both must be set first.
_TEST_DB_DIR = tempfile.mkdtemp(prefix="supportai_test_db_")
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production-use-only-in-tests"
os.environ["DATABASE_PATH"] = str(Path(_TEST_DB_DIR) / "test.db")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "1000")  # tests fire many requests fast

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.models.database import Base, engine, SessionLocal  # noqa: E402
import app.api.documents as documents_module  # noqa: E402
from app.services.vector_store_service import VectorStoreService  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_database():
    """Wipe and recreate every table before each test, so tests never leak
    state into each other (e.g. one test's user shouldn't affect another
    test's "am I the first user" tenant-bootstrap check)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _isolated_image_map(tmp_path, monkeypatch):
    """Point image_store's on-disk image_map.json at a temp file instead
    of the real backend/app/images/image_map.json, so running tests never
    mutates real application data."""
    import app.services.image_store as image_store_module

    fake_map_path = tmp_path / "image_map_test.json"
    monkeypatch.setattr(image_store_module, "IMAGE_MAP_PATH", fake_map_path)
    yield


@pytest.fixture(autouse=True)
def _isolated_vector_store(tmp_path, monkeypatch):
    """Point the module-level vector_store singleton at a fresh temp
    directory per test, instead of the real backend/chroma_data folder,
    so tests can't pollute or depend on real uploaded data."""
    test_store = VectorStoreService(persist_directory=str(tmp_path / "chroma_test"))
    monkeypatch.setattr(documents_module, "vector_store", test_store)
    yield test_store


@pytest.fixture(autouse=True)
def _fake_embeddings(monkeypatch):
    """Replace real Ollama embedding calls with a cheap deterministic fake.
    No Ollama server is running in the test environment, and we don't need
    real embedding quality to test upload/dedup/tenant-isolation logic —
    we just need *some* fixed-length vector per chunk."""

    def fake_embed_documents(self, texts):
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

    def fake_embed_query(self, text):
        return [0.1, 0.2, 0.3, 0.4]

    monkeypatch.setattr(
        documents_module.EmbeddingService, "embed_documents", fake_embed_documents
    )
    monkeypatch.setattr(
        documents_module.EmbeddingService, "embed_query", fake_embed_query
    )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def register(client, email="admin@example.com", password="correct-horse-battery", name="Test Admin"):
    """Register a user and return (response, access_token)."""
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )
    token = resp.json().get("access_token") if resp.status_code == 201 else None
    return resp, token


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
