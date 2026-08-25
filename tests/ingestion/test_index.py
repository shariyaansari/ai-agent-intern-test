import numpy as np

from app.ingestion.index import EmbeddingIndex
from app.ingestion.models import DocumentChunk


def make_chunk(
    chunk_id: str,
    text: str,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        text=text,
        embedding_text=text,
        filename="test.md",
        document_id="TEST-001",
        title="Test",
        heading="Test Heading",
        heading_path=["Test Heading"],
        metadata={
            "status": "active",
            "policy_authority": "official",
        },
    )


def test_cosine_search_returns_most_similar_chunk():
    chunks = [
        make_chunk("one", "returns policy"),
        make_chunk("two", "shipping policy"),
    ]

    embeddings = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
        ],
        dtype=np.float32,
    )

    index = EmbeddingIndex(
        chunks=chunks,
        embeddings=embeddings,
    )

    results = index.search(
        query_embedding=[1.0, 0.0],
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "one"
    assert results[0].score > 0.99


def test_search_results_are_sorted_by_score():
    chunks = [
        make_chunk("one", "returns"),
        make_chunk("two", "shipping"),
        make_chunk("three", "warranty"),
    ]

    embeddings = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
            [0.7, 0.7],
        ],
        dtype=np.float32,
    )

    index = EmbeddingIndex(
        chunks=chunks,
        embeddings=embeddings,
    )

    results = index.search(
        query_embedding=[1.0, 0.0],
        top_k=3,
    )

    scores = [result.score for result in results]

    assert scores == sorted(
        scores,
        reverse=True,
    )


def test_search_respects_top_k():
    chunks = [
        make_chunk("one", "one"),
        make_chunk("two", "two"),
        make_chunk("three", "three"),
    ]

    embeddings = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
            [0.7, 0.7],
        ],
        dtype=np.float32,
    )

    index = EmbeddingIndex(
        chunks=chunks,
        embeddings=embeddings,
    )

    results = index.search(
        query_embedding=[1.0, 0.0],
        top_k=2,
    )

    assert len(results) == 2
    
def test_retrieval_result_preserves_chunk_metadata():
    chunks = [
        DocumentChunk(
            chunk_id="returns-1",
            text="Returns are allowed.",
            embedding_text="Returns policy: Returns are allowed.",
            filename="returns.md",
            document_id="RET-2026-01",
            title="Returns Policy",
            heading="Returns Window",
            heading_path=["Returns Policy", "Returns Window"],
            metadata={
                "status": "active",
                "policy_authority": "official",
                "superseded_by": None,
            },
        )
    ]

    embeddings = np.array(
        [[1.0, 0.0]],
        dtype=np.float32,
    )

    index = EmbeddingIndex(
        chunks=chunks,
        embeddings=embeddings,
    )

    results = index.search(
        query_embedding=[1.0, 0.0],
        top_k=1,
    )

    result = results[0]

    assert result.chunk.document_id == "RET-2026-01"
    assert result.chunk.filename == "returns.md"
    assert result.chunk.heading == "Returns Window"
    assert result.chunk.metadata["status"] == "active"
    assert result.chunk.metadata["policy_authority"] == "official"