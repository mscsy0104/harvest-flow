from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VectorDB(ABC):
    """Abstract interface for vector database operations."""

    @abstractmethod
    def upsert_document(self, file_name: str, content: str, payload: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_document(self, file_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def query_similar(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError


class MetadataDB(ABC):
    """Abstract interface for metadata persistence."""

    @abstractmethod
    def save_note_metadata(
        self,
        filename: str,
        last_modified: float,
        status: str,
        workflow_stage: str | None = None,
        last_transition_at: float | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_note_metadata(self, filename: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_ready_to_publish(self, now_ts: float) -> list[dict[str, Any]]:
        raise NotImplementedError


class SSGPublisher(ABC):
    """Abstract interface for publish/unpublish operations."""

    @abstractmethod
    def publish_content(self, file_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def unpublish_content(self, file_name: str) -> bool:
        raise NotImplementedError

