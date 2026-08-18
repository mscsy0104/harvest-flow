from __future__ import annotations

from typing import Any

from harvest_flow_core.interfaces import VectorDB
from harvest_flow.database import (
    delete_note_from_vector_db,
    save_to_vector_db,
    search_knowledge_base,
)


class QdrantVectorAdapter(VectorDB):
    """Qdrant-backed vector adapter using existing vector operations."""

    def upsert_document(self, file_name: str, content: str, payload: dict[str, Any]) -> None:
        save_to_vector_db(file_name, content, payload)

    def delete_document(self, file_name: str) -> None:
        delete_note_from_vector_db(file_name)

    def query_similar(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return search_knowledge_base(query, top_k=top_k)

