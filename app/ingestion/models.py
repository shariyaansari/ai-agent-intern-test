from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class Document:
    """A parsed Markdown document with its front-matter metadata."""

    path: str
    content: str
    metadata: dict[str, Any]

    @property
    def document_id(self) -> str | None:
        return self.metadata.get("document_id")

    @property
    def title(self) -> str | None:
        return self.metadata.get("title")

    @property
    def status(self) -> str | None:
        return self.metadata.get("status")

    @property
    def effective_date(self) -> date | None:
        value = self.metadata.get("effective_date")
        if value is None:
            return None

        if isinstance(value, date):
            return value

        return date.fromisoformat(str(value))

    @property
    def audience(self) -> str | None:
        return self.metadata.get("audience")

    @property
    def policy_authority(self) -> str | None:
        return self.metadata.get("policy_authority")
    
    @property
    def supersedes(self) -> str | None:
        return self.metadata.get("supersedes")


@dataclass
class DocumentChunk:
    """A retrieval unit derived from a Markdown document."""
    chunk_id: str
    text: str

    filename: str
    document_id: str | None
    title: str | None

    heading: str | None
    heading_path: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    embedding_text: str | None = None
    embedding: Any | None = None
    