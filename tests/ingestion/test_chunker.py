from pathlib import Path

from app.ingestion.chunker import (
    chunk_document,
    chunk_documents,
)
from app.ingestion.loader import load_document, load_documents


KNOWLEDGE_BASE = Path("knowledge-base")


def test_chunks_preserve_filename():
    document = load_document(
        KNOWLEDGE_BASE / "01-returns-policy-current.md"
    )

    chunks = chunk_document(document)

    assert chunks

    assert all(
        chunk.filename == "01-returns-policy-current.md"
        for chunk in chunks
    )


def test_chunks_preserve_metadata():
    document = load_document(
        KNOWLEDGE_BASE / "02-returns-policy-legacy.md"
    )

    chunks = chunk_document(document)

    assert chunks

    for chunk in chunks:
        assert chunk.document_id == "RET-2024-01"
        assert chunk.metadata["status"] == "superseded"
        assert chunk.metadata["policy_authority"] == "official"
        assert chunk.metadata["superseded_by"] == "RET-2026-01"


def test_chunks_have_headings():
    document = load_document(
        KNOWLEDGE_BASE / "01-returns-policy-current.md"
    )

    chunks = chunk_document(document)

    assert any(
        chunk.heading is not None
        for chunk in chunks
    )


def test_heading_path_is_preserved():
    document = load_document(
        KNOWLEDGE_BASE / "01-returns-policy-current.md"
    )

    chunks = chunk_document(document)

    assert any(
        len(chunk.heading_path) > 0
        for chunk in chunks
    )


def test_embedding_text_contains_context():
    document = load_document(
        KNOWLEDGE_BASE / "01-returns-policy-current.md"
    )

    chunks = chunk_document(document)

    assert chunks

    for chunk in chunks:
        assert chunk.embedding_text
        assert document.title in chunk.embedding_text
        assert chunk.text in chunk.embedding_text


def test_chunk_ids_are_deterministic():
    document = load_document(
        KNOWLEDGE_BASE / "01-returns-policy-current.md"
    )

    first = chunk_document(document)
    second = chunk_document(document)

    assert [c.chunk_id for c in first] == [
        c.chunk_id for c in second
    ]


def test_chunking_all_documents():
    documents = load_documents(KNOWLEDGE_BASE)

    chunks = chunk_documents(documents)

    assert chunks
    assert len(chunks) >= len(documents)