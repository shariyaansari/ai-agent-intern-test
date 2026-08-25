from __future__ import annotations

from datetime import date
from typing import Iterable

from app.ingestion import DocumentChunk, RetrievalResult

from .policy import (
    ApplicabilityContext,
    ApplicableSource,
    ResolutionResult,
    ResolutionStatus,
)


def is_authoritative(chunk: DocumentChunk) -> bool:
    """
    A source can support a customer answer only when it is
    explicitly official and customer-answerable.
    """

    metadata = chunk.metadata

    return (
        metadata.get("policy_authority") == "official"
        and metadata.get("customer_answering", True) is not False
        and metadata.get("status") != "draft"
    )
    
def is_superseded(chunk: DocumentChunk) -> bool:
    return chunk.metadata.get("status") == "superseded"


def superseded_by(chunk: DocumentChunk) -> str | None:
    value = chunk.metadata.get("superseded_by")

    if value is None:
        return None

    return str(value)

def source_supersedes(
    newer: DocumentChunk,
    older: DocumentChunk,
) -> bool:
    """
    Return True only when the older document explicitly names
    the newer document as its successor.
    """

    newer_id = newer.document_id
    older_successor = older.metadata.get("superseded_by")

    if newer_id is None or older_successor is None:
        return False

    return str(older_successor) == str(newer_id)

def filter_authoritative_candidates(
    results: Iterable[RetrievalResult],
) -> list[RetrievalResult]:
    """
    Remove documents that cannot serve as authoritative
    customer-facing policy.
    """

    return [
        result
        for result in results
        if is_authoritative(result.chunk)
    ]
    
def resolve_supersession(
    results: list[RetrievalResult],
) -> list[RetrievalResult]:
    """
    Remove a superseded source when its explicitly declared
    successor is present among the retrieved candidates.
    """

    candidates = filter_authoritative_candidates(results)

    document_ids = {
        result.chunk.document_id
        for result in candidates
    }

    resolved: list[RetrievalResult] = []

    for result in candidates:
        successor = result.chunk.metadata.get(
            "superseded_by"
        )

        if successor is not None:
            if str(successor) in {
                str(document_id)
                for document_id in document_ids
                if document_id is not None
            }:
                continue

        resolved.append(result)

    return resolved

def applies_by_purchase_date(
    chunk: DocumentChunk,
    context: ApplicabilityContext,
) -> bool:
    """
    Determine whether a policy's effective period contains
    the customer's purchase date.

    If no purchase date is known, do not reject the source
    based on dates alone.
    """

    purchase_date = context.purchase_date

    if purchase_date is None:
        return True

    effective_date = chunk.metadata.get("effective_date")
    superseded_date = chunk.metadata.get("superseded_date")

    if effective_date is not None:
        if purchase_date < effective_date:
            return False

    if superseded_date is not None:
        if purchase_date >= superseded_date:
            return False

    return True

def applies_by_membership(
    chunk: DocumentChunk,
    context: ApplicabilityContext,
) -> bool:
    """
    Determine whether a membership-specific policy applies.

    TrailPlus applies only when membership was active when
    the order was placed.

    If membership information is unavailable, we do not
    assume the customer qualifies.
    """

    membership_tier = context.membership_tier

    # This is not a TrailPlus-specific document.
    if chunk.document_id != "MEM-2026-01":
        return True

    # We cannot assume TrailPlus membership.
    if membership_tier is None:
        return False

    return membership_tier.lower() == "trailplus"

def applies_by_final_sale(
    chunk: DocumentChunk,
    context: ApplicabilityContext,
) -> bool:
    """
    Determine whether the final-sale policy is relevant
    to the current request.

    Final-sale restrictions apply to change-of-mind returns.
    They do not remove the customer's ability to report
    damaged, defective, or incorrect items.
    """

    if chunk.document_id != "RET-2026-02":
        return True

    # We only apply the restriction to change-of-mind returns.
    if context.request_type is None:
        return True

    if context.request_type in {
        "damaged",
        "defective",
        "incorrect_item",
    }:
        return False

    return True


def determine_final_sale_status(
    context: ApplicabilityContext,
) -> bool | None:
    """
    Determine final-sale status from the three customer-facing
    labeling locations.

    Any explicit FINAL SALE label is sufficient.

    None means the information is unavailable.
    """

    labels = (
        context.final_sale_product_page,
        context.final_sale_cart,
        context.final_sale_order_confirmation,
    )

    known_labels = [
        value
        for value in labels
        if value is not None
    ]

    if not known_labels:
        return None

    return any(known_labels)


def detect_conflict(
    results: list[RetrievalResult],
) -> bool:
    """
    Detect whether multiple authoritative, applicable sources
    remain without an explicit supersession relationship.

    This function does not decide whether two arbitrary pieces
    of text semantically contradict each other. It identifies
    the candidate situation that requires conflict evaluation.
    """

    candidates = filter_authoritative_candidates(results)

    if len(candidates) < 2:
        return False

    document_ids = {
        result.chunk.document_id
        for result in candidates
    }

    for result in candidates:
        successor = result.chunk.metadata.get("superseded_by")

        if successor and str(successor) in {
            str(document_id)
            for document_id in document_ids
            if document_id is not None
        }:
            return False

    return True


def resolve_policy(
    results: list[RetrievalResult],
    context: ApplicabilityContext | None = None,
) -> ResolutionResult:
    """
    Resolve retrieved policy candidates into authoritative evidence.

    This function does not generate a customer-facing answer.
    It only determines which retrieved sources can support one.
    """

    if not results:
        return ResolutionResult(
            status=ResolutionStatus.INSUFFICIENT,
            sources=[],
            reason="No relevant knowledge-base evidence was retrieved.",
        )

    if context is None:
        context = ApplicabilityContext()

    # 1. Authority
    candidates = filter_authoritative_candidates(results)

    if not candidates:
        return ResolutionResult(
            status=ResolutionStatus.INSUFFICIENT,
            sources=[],
            reason="Retrieved sources are not authoritative customer-facing policy.",
        )

    # 2. Purchase-date applicability
    candidates = [
        result
        for result in candidates
        if applies_by_purchase_date(
            result.chunk,
            context,
        )
        and applies_by_membership(
            result.chunk,
            context,
        )
        and applies_by_final_sale(
            result.chunk,
            context,
        )
    ]

    if not candidates:
        return ResolutionResult(
            status=ResolutionStatus.INSUFFICIENT,
            sources=[],
            reason="No authoritative source applies to the supplied purchase date.",
        )

    # 3. Supersession
    candidates = resolve_supersession(candidates)

    if not candidates:
        return ResolutionResult(
            status=ResolutionStatus.INSUFFICIENT,
            sources=[],
            reason="No applicable authoritative source remains after supersession resolution.",
        )

    # 4. Convert surviving candidates to structured sources.
    sources = [
        ApplicableSource(
            chunk=result.chunk,
            reason="Retrieved authoritative source that passed applicability and supersession checks.",
        )
        for result in candidates
    ]

    # 5. Potential conflict.
    if detect_conflict(candidates):
        return ResolutionResult(
            status=ResolutionStatus.CONFLICT,
            sources=sources,
            reason=(
                "Multiple active official sources remain and none "
                "explicitly supersedes the other."
            ),
        )

    # 6. One applicable source.
    if len(sources) == 1:
        return ResolutionResult(
            status=ResolutionStatus.RESOLVED,
            sources=sources,
            reason="One authoritative applicable source remains.",
        )

    # Multiple non-conflicting sources can legitimately support an answer.
    return ResolutionResult(
        status=ResolutionStatus.RESOLVED,
        sources=sources,
        reason="Multiple authoritative applicable sources remain.",
    )