from __future__ import annotations

from typing import Any

from harvest_flow.core.interfaces import MetadataDB
from harvest_flow.database import (
    get_note_metadata,
    list_ready_to_publish,
    update_metadata_db,
)


class SqliteMetadataAdapter(MetadataDB):
    """SQLite-backed metadata adapter using existing persistence module."""

    def save_note_metadata(
        self,
        filename: str,
        last_modified: float,
        status: str,
        workflow_stage: str | None = None,
        last_transition_at: float | None = None,
    ) -> None:
        update_metadata_db(
            filename,
            last_modified,
            status,
            workflow_stage=workflow_stage,
            last_transition_at=last_transition_at,
        )

    def get_note_metadata(self, filename: str) -> dict[str, Any] | None:
        return get_note_metadata(filename)

    def list_ready_to_publish(self, now_ts: float) -> list[dict[str, Any]]:
        return list_ready_to_publish(now_ts)

