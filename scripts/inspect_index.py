from pathlib import Path
import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from app.ingestion import (
    EmbeddingIndex,
    chunk_documents,
    load_documents,
)


KNOWLEDGE_BASE = Path("knowledge-base")


def main():
    load_dotenv()

    model_name = os.getenv(
        "EMBEDDING_MODEL",
        "all-MiniLM-L6-v2",
    )

    print(f"Loading embedding model: {model_name}")

    model = SentenceTransformer(model_name)

    documents = load_documents(KNOWLEDGE_BASE)
    chunks = chunk_documents(documents)

    print(f"Documents: {len(documents)}")
    print(f"Chunks:    {len(chunks)}")

    index = EmbeddingIndex.build(
        chunks=chunks,
        model=model,
    )

    print("Embeddings: complete")

    while True:
        query = input("\nQuery (or 'exit'): ").strip()

        if query.lower() == "exit":
            break

        if not query:
            continue

        results = index.search_text(
            query=query,
            model=model,
            top_k=5,
        )

        print("\nTop results:\n")

        for i, result in enumerate(results, start=1):
            chunk = result.chunk

            print(f"{i}. score={result.score:.4f}")
            print(f"   file: {chunk.filename}")
            print(f"   id: {chunk.document_id}")
            print(f"   heading: {chunk.heading}")
            print(
                f"   status: "
                f"{chunk.metadata.get('status')}"
            )
            print(
                f"   authority: "
                f"{chunk.metadata.get('policy_authority')}"
            )
            print(f"   text: {chunk.text[:300]}")
            print()


if __name__ == "__main__":
    main()