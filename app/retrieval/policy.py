from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from app.ingestion import DocumentChunk


class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    CONFLICT = "conflict"
    INSUFFICIENT = "insufficient"


@dataclass
class ApplicabilityContext:
    purchase_date: date | None = None
    membership_tier: str | None = None
    product_is_final_sale: bool | None = None
    request_type: str | None = None
    final_sale_product_page: bool | None = None
    final_sale_cart: bool | None = None
    final_sale_order_confirmation: bool | None = None


@dataclass
class ApplicableSource:
    """
    A source selected by the Phase 3 resolver.
    """

    chunk: DocumentChunk
    reason: str


@dataclass
class ResolutionResult:
    """
    Structured result of policy resolution.
    """

    status: ResolutionStatus
    sources: list[ApplicableSource]
    reason: str