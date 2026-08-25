from pathlib import Path

import pytest

from app.ingestion.loader import (
    load_document,
    load_documents,
    parse_front_matter,
)


KNOWLEDGE_BASE = Path("knowledge-base")


def test_loads_all_markdown_documents():
    documents = load_documents(KNOWLEDGE_BASE)

    assert len(documents) == 14

    assert all(
        document.document_id
        for document in documents
    )


def test_legacy_returns_metadata_is_preserved():
    path = KNOWLEDGE_BASE / "02-returns-policy-legacy.md"

    document = load_document(path)

    assert document.metadata["document_id"] == "RET-2024-01"
    assert document.metadata["status"] == "superseded"
    assert document.metadata["effective_date"].isoformat() == "2024-01-01"
    assert document.metadata["superseded_date"].isoformat() == "2026-04-01"
    assert document.metadata["superseded_by"] == "RET-2026-01"
    assert document.metadata["policy_authority"] == "official"


def test_migration_document_metadata_is_preserved():
    path = KNOWLEDGE_BASE / "14-internal-content-migration-notes.md"

    document = load_document(path)

    assert document.metadata["status"] == "draft"
    assert document.metadata["policy_authority"] == "none"
    assert document.metadata["customer_answering"] is False


def test_front_matter_is_parsed():
    raw = """---
document_id: TEST-001
title: Test Document
status: active
effective_date: 2026-01-01
---
# Test Heading

Test content.
"""

    metadata, body = parse_front_matter(raw)

    assert metadata["document_id"] == "TEST-001"
    assert metadata["title"] == "Test Document"
    assert metadata["status"] == "active"
    assert "# Test Heading" in body


def test_missing_required_metadata_is_rejected(tmp_path):
    path = tmp_path / "bad.md"

    path.write_text(
        """---
title: Test
status: active
---
# Test
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_document(path)