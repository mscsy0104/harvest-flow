"""Adapter implementations that bridge core interfaces to runtime backends."""

from .metadata_db import SqliteMetadataAdapter
from .ssg import GitHubSSGAdapter
from .vector_db import QdrantVectorAdapter

__all__ = [
    "GitHubSSGAdapter",
    "QdrantVectorAdapter",
    "SqliteMetadataAdapter",
]

