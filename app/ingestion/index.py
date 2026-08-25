from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer

from .models import DocumentChunk


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    score: float


class EmbeddingIndex:
    """Small in-memory cosine-similarity index."""

    def __init__(
        self,
        chunks: list[DocumentChunk],
        embeddings: np.ndarray,
    ):
        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match number of embeddings."
            )

        self.chunks = chunks
        self.embeddings = self._normalize(embeddings)

    @staticmethod
    def _normalize(
        vectors: np.ndarray,
    ) -> np.ndarray:
        norms = np.linalg.norm(
            vectors,
            axis=1,
            keepdims=True,
        )

        norms = np.maximum(norms, 1e-12)

        return vectors / norms

    @classmethod
    def build(
        cls,
        chunks: list[DocumentChunk],
        model: SentenceTransformer,
    ) -> "EmbeddingIndex":

        texts = [
            chunk.embedding_text or chunk.text
            for chunk in chunks
            ]

        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=True,
        )

        embeddings = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):
            chunk.embedding = embedding

        return cls(
            chunks=chunks,
            embeddings=embeddings,
        )

    def search(
        self,
        query_embedding: list[float] | np.ndarray,
        top_k: int = 5,
    ) -> list[RetrievalResult]:

        query = np.asarray(
            query_embedding,
            dtype=np.float32,
        )

        query_norm = np.linalg.norm(query)

        if query_norm == 0:
            raise ValueError(
                "Query embedding cannot be zero."
            )

        query = query / query_norm

        scores = self.embeddings @ query

        top_k = min(top_k, len(scores))

        indices = np.argsort(scores)[::-1][:top_k]

        return [
            RetrievalResult(
                chunk=self.chunks[index],
                score=float(scores[index]),
            )
            for index in indices
        ]

    def search_text(
        self,
        query: str,
        model: SentenceTransformer,
        top_k: int = 5,
    ) -> list[RetrievalResult]:

        query_embedding = model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=False,
        )

        return self.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )