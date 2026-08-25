import pytest
from pathlib import Path

from sentence_transformers import SentenceTransformer

from app.ingestion import (
    EmbeddingIndex,
    chunk_documents,
    load_documents,
)


KNOWLEDGE_BASE = Path("knowledge-base")
MODEL_NAME = "all-MiniLM-L6-v2"


@pytest.fixture(scope="session")
def embedding_model():
    return SentenceTransformer(MODEL_NAME)


@pytest.fixture(scope="session")
def retrieval_index(embedding_model):
    documents = load_documents(KNOWLEDGE_BASE)
    chunks = chunk_documents(documents)

    return EmbeddingIndex.build(
        chunks=chunks,
        model=embedding_model,
    )