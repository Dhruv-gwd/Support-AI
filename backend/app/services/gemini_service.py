import logging
import time

import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.5


class GeminiServiceError(Exception):
    """Raised when the local Ollama generation service is unavailable."""


class GeminiService:

    def __init__(self):
        self.client = httpx.Client(base_url=OLLAMA_BASE_URL, timeout=120.0)

    def generate_response(self, message: str) -> str:
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.post(
                    "/api/generate",
                    json={"model": OLLAMA_CHAT_MODEL, "prompt": message, "stream": False},
                )
                response.raise_for_status()
                answer = response.json().get("response", "").strip()
                if answer:
                    return answer
                raise GeminiServiceError("Ollama returned an empty response")
            except (httpx.HTTPError, ValueError, GeminiServiceError) as e:
                last_error = e
                logger.warning("Ollama generation failed (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
                time.sleep(BASE_DELAY_SECONDS * attempt)

        raise GeminiServiceError(
            "Ollama is unavailable. Start Ollama and pull the configured chat model."
        ) from last_error
