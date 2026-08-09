import logging
import time

import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.5


class EmbeddingServiceError(Exception):
    pass


class EmbeddingService:

    def __init__(self):
        self.client = httpx.Client(base_url=OLLAMA_BASE_URL, timeout=120.0)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)

    def _embed_one(self, text: str) -> list[float]:
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.post(
                    "/api/embeddings",
                    json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text},
                )
                response.raise_for_status()
                embedding = response.json().get("embedding")
                if not embedding:
                    raise EmbeddingServiceError("Ollama returned an empty embedding")
                return embedding
            except (httpx.HTTPError, ValueError, EmbeddingServiceError) as e:
                last_error = e
                logger.warning(
                    "Ollama embedding failed (attempt %d/%d): %s", attempt, MAX_RETRIES, e
                )
                time.sleep(BASE_DELAY_SECONDS * attempt)

        raise EmbeddingServiceError(
            "Ollama is unavailable. Start Ollama and pull the configured embedding model."
        )
