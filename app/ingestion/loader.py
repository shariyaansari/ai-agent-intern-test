from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Document


REQUIRED_METADATA = {
    "document_id",
    "title",
    "status",
    "effective_date",
    
}


def parse_front_matter(raw: str) -> tuple[dict[str, Any], str]:
    """
    Split a Markdown document into YAML front matter and Markdown body.
    """

    text = raw.replace("\r\n", "\n")

    if not text.startswith("---\n"):
        raise ValueError("Document does not start with YAML front matter.")

    parts = text.split("\n---\n", maxsplit=1)

    if len(parts) != 2:
        raise ValueError("Malformed YAML front matter.")

    front_matter_text = parts[0][4:]
    body = parts[1]

    metadata = yaml.safe_load(front_matter_text)

    if not isinstance(metadata, dict):
        raise ValueError("Front matter must be a YAML mapping.")

    return metadata, body


def validate_metadata(metadata: dict[str, Any], path: Path) -> None:
    """Validate required metadata without discarding optional metadata."""

    missing = REQUIRED_METADATA - metadata.keys()

    if missing:
        raise ValueError(
            f"{path.name} is missing required metadata: "
            f"{sorted(missing)}"
        )


def load_document(path: Path) -> Document:
    """Load and validate one Markdown document."""

    raw = path.read_text(encoding="utf-8")

    metadata, body = parse_front_matter(raw)

    validate_metadata(metadata, path)

    return Document(
        path=str(path),
        content=body.strip(),
        metadata=metadata,
    )


def load_documents(directory: str | Path) -> list[Document]:
    """Load all Markdown documents from a knowledge-base directory."""

    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"Knowledge base not found: {directory}")

    paths = sorted(directory.glob("*.md"))

    if not paths:
        raise ValueError(f"No Markdown documents found in {directory}")

    documents = [load_document(path) for path in paths]

    return documents