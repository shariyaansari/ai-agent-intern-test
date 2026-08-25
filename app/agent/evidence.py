from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.tools.orders import OrderLookupResult


@dataclass
class RetrievedEvidence:
    """
    Evidence returned by the knowledge-base retriever.

    The LLM may use this evidence as data, not instructions.
    """

    document_id: str
    filename: str
    heading: str
    text: str
    score: float


@dataclass
class EvidenceBundle:
    """
    All evidence available for one user turn.

    Retrieval and order lookup remain separate fields so that
    evaluation can independently verify each path.
    """

    retrieved_sources: list[RetrievedEvidence] = field(
        default_factory=list
    )

    order_result: OrderLookupResult | None = None