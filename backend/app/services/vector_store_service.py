import uuid

import chromadb

# Embeddings from different providers have incompatible dimensions. Keep the
# Ollama index separate from the legacy Gemini-backed collection.
COLLECTION_NAME = "documents_ollama_v1"
PERSIST_DIR = "chroma_data"  # relative to backend/ working directory


class VectorStoreService:

    def __init__(self, persist_directory: str = PERSIST_DIR):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(COLLECTION_NAME)

    def add_chunks(
        self, chunks: list[str], embeddings: list[list[float]], source_filename: str, tenant_id: int
    ) -> list[str]:
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {"source": source_filename, "chunk_index": i, "tenant_id": tenant_id}
            for i in range(len(chunks))
        ]
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        return ids

    def query(self, query_embedding: list[float], tenant_id: int, top_k: int = 4) -> dict:
        where_filter = {"tenant_id": tenant_id}
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas"],
        )

    def list_sources(self, tenant_id: int) -> list[str]:
        where_filter = {"tenant_id": tenant_id}
        all_items = self.collection.get(where=where_filter)
        sources = (
            {m["source"] for m in all_items["metadatas"]}
            if all_items["metadatas"]
            else set()
        )
        return sorted(sources)

    def delete_source(self, filename: str, tenant_id: int) -> int:
        where_filter = {
            "$and": [
                {"source": filename},
                {"tenant_id": tenant_id},
            ]
        }
        matches = self.collection.get(where=where_filter)
        ids = matches["ids"]
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)
