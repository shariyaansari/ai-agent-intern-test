from __future__ import annotations
from pathlib import Path

import hashlib
import re

from .models import Document, DocumentChunk


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def make_chunk_id(
    filename: str,
    heading_path: list[str],
    chunk_index: int,
) -> str:
    """Create a deterministic ID for a chunk."""

    raw = "|".join(
        [
            filename,
            *heading_path,
            str(chunk_index),
        ]
    )

    digest = hashlib.sha1(
        raw.encode("utf-8")
    ).hexdigest()[:12]

    return f"{filename}:{digest}"


def split_by_headings(
    content: str,
) -> list[tuple[list[str], str]]:
    """
    Split Markdown into heading-aware sections.

    Returns:
        [(heading_path, section_text), ...]
    """

    lines = content.splitlines()

    sections: list[tuple[list[str], str]] = []

    heading_stack: list[str] = []
    current_lines: list[str] = []
    current_path: list[str] = []

    def flush() -> None:
        text = "\n".join(current_lines).strip()

        if text:
            sections.append(
                (
                    current_path.copy(),
                    text,
                )
            )

    for line in lines:
        match = HEADING_RE.match(line)

        if match:
            flush()
            current_lines.clear()

            level = len(match.group(1))
            heading = match.group(2).strip()

            heading_stack[:] = heading_stack[: level - 1]
            heading_stack.append(heading)

            current_path = heading_stack.copy()

        else:
            current_lines.append(line)

    flush()

    return sections


def chunk_document(
    document: Document,
    max_chars: int = 5000,
) -> list[DocumentChunk]:
    """
    Convert one document into heading-aware chunks.
    """

    sections = split_by_headings(document.content)

    chunks: list[DocumentChunk] = []
    chunk_index = 0

    for heading_path, section_text in sections:

        if len(section_text) <= max_chars:
            pieces = [section_text]

        else:
            paragraphs = [
                paragraph.strip()
                for paragraph in section_text.split("\n\n")
                if paragraph.strip()
            ]

            pieces = []
            current = ""

            for paragraph in paragraphs:

                candidate = (
                    paragraph
                    if not current
                    else f"{current}\n\n{paragraph}"
                )

                if len(candidate) <= max_chars:
                    current = candidate

                else:
                    if current:
                        pieces.append(current)

                    current = paragraph

            if current:
                pieces.append(current)

        for piece in pieces:

            filename = Path(document.path).name

            chunk_id = make_chunk_id(
                filename=filename,
                heading_path=heading_path,
                chunk_index=chunk_index,
            )

            # This is where embedding_text MUST be created.
            # heading_path and piece both exist here.
            embedding_text = "\n".join(
                part
                for part in [
                    (
                        f"Title: {document.title}"
                        if document.title
                        else None
                    ),
                    (
                        f"Section: {' > '.join(heading_path)}"
                        if heading_path
                        else None
                    ),
                    piece,
                ]
                if part
            )

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    text=piece,
                    embedding_text=embedding_text,
                    filename=filename,
                    document_id=document.document_id,
                    title=document.title,
                    heading=(
                        heading_path[-1]
                        if heading_path
                        else None
                    ),
                    heading_path=heading_path,
                    metadata=document.metadata.copy(),
                )
            )

            chunk_index += 1

    return chunks


def chunk_documents(
    documents: list[Document],
    max_chars: int = 5000,
) -> list[DocumentChunk]:
    """Chunk all documents."""

    chunks: list[DocumentChunk] = []

    for document in documents:
        chunks.extend(
            chunk_document(
                document,
                max_chars=max_chars,
            )
        )

    return chunks