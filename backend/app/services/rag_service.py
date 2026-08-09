from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.services.gemini_service import GeminiService
from app.services.image_store import get_document_images

TOP_K = 8


def build_prompt(context: str, question: str, history: list[dict] | None = None) -> str:
    if not context.strip():
        return (
            "You are a customer support assistant. No relevant company "
            "documents were found for this question. Politely tell the "
            "customer you don't have information on this topic and suggest "
            f"they contact support directly.\n\nQuestion: {question}"
        )

    history_text = ""
    if history:
        lines = []
        for turn in history[-6:]:
            lines.append(f"{turn['role'].capitalize()}: {turn['content']}")
        history_text = "\n".join(lines) + "\n\n"

    return f"""You are a helpful customer support assistant. Answer the customer's \
question using ONLY the context below. Keep your answer concise — 2 to 4 sentences. \
Do not use outside knowledge. If the answer isn't in the context, say you don't have \
that information rather than guessing.

{history_text}Context:
{context}

Question: {question}

Answer:"""


class RagService:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreService()
        self.gemini_service = GeminiService()

    def answer(
        self,
        question: str,
        tenant_id: int,
        top_k: int = TOP_K,
        history: list[dict] | None = None,
    ) -> tuple[str, list[str], list[str]]:
        query_embedding = self.embedding_service.embed_query(question)
        results = self.vector_store.query(
            query_embedding, top_k=top_k, tenant_id=tenant_id
        )

        retrieved_chunks = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        context = "\n\n---\n\n".join(retrieved_chunks)

        prompt = build_prompt(context, question, history)
        answer = self.gemini_service.generate_response(prompt)

        sources = sorted({m["source"] for m in metadatas if "source" in m})
        image_urls = []
        for source in sources:
            for img_name in get_document_images(source):
                image_urls.append(f"/api/images/{img_name}")

        return answer, sources, image_urls
