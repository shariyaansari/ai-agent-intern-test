from pathlib import Path

import pytest
from sentence_transformers import SentenceTransformer

from app.ingestion import (
    EmbeddingIndex,
    chunk_documents,
    load_documents,
)

KNOWLEDGE_BASE = Path("knowledge-base")
MODEL_NAME = "all-MiniLM-L6-v2"


@pytest.fixture(scope="module")
def embedding_model():
    return SentenceTransformer(MODEL_NAME)


@pytest.fixture(scope="module")
def retrieval_index(embedding_model):
    documents = load_documents(KNOWLEDGE_BASE)
    chunks = chunk_documents(documents)

    return EmbeddingIndex.build(
        chunks=chunks,
        model=embedding_model,
    )


def retrieved_document_ids(
    retrieval_index,
    embedding_model,
    query: str,
    top_k: int = 5,
):
    results = retrieval_index.search_text(
        query=query,
        model=embedding_model,
        top_k=top_k,
    )

    return [
        result.chunk.document_id
        for result in results
    ]


def test_return_query_retrieves_return_policy(
    retrieval_index,
    embedding_model,
):
    results = retrieved_document_ids(
        retrieval_index,
        embedding_model,
        "What is the return window?",
    )

    assert (
        "RET-2026-01" in results
        or "RET-2024-01" in results
    )


def test_trail_plus_query_retrieves_trail_plus_policy(
    retrieval_index,
    embedding_model,
):
    results = retrieved_document_ids(
        retrieval_index,
        embedding_model,
        "What is the return window for a Trail Plus member?",
    )

    assert "MEM-2026-01" in results


def test_canada_query_retrieves_international_shipping(
    retrieval_index,
    embedding_model,
):
    results = retrieved_document_ids(
        retrieval_index,
        embedding_model,
        "Do you ship to Canada?",
    )

    assert "SHIP-2026-INTL" in results


def test_warranty_query_retrieves_warranty_policy(
    retrieval_index,
    embedding_model,
):
    results = retrieved_document_ids(
        retrieval_index,
        embedding_model,
        "What does the warranty cover?",
    )

    assert "WAR-2026-01" in results

def test_retrieval_results_have_source_traceability(
    retrieval_index,
    embedding_model,
):
    results = retrieval_index.search_text(
        query="What is the return window?",
        model=embedding_model,
        top_k=5,
    )

    assert results

    for result in results:
        chunk = result.chunk

        assert chunk.chunk_id
        assert chunk.document_id
        assert chunk.filename
        assert chunk.text
        assert chunk.heading is not None
        assert isinstance(chunk.metadata, dict)