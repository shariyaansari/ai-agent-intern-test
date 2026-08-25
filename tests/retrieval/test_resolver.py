from datetime import date
import numpy as np

from app.ingestion import (
    DocumentChunk,
    RetrievalResult,
)

from app.retrieval import (
    ApplicabilityContext,
    ApplicableSource,
    ResolutionResult,
    ResolutionStatus,
    applies_by_final_sale,
    applies_by_membership,
    applies_by_purchase_date,
    determine_final_sale_status,
    filter_authoritative_candidates,
    resolve_supersession,
    detect_conflict,
    is_authoritative,
    resolve_policy,
    source_supersedes,
)

from app.retrieval.policy import ResolutionStatus

def make_chunk(
    *,
    document_id: str,
    status: str = "active",
    policy_authority: str = "official",
    customer_answering: bool = True,
    effective_date=None,
    superseded_date=None,
    superseded_by=None,
):
    metadata = {
        "status": status,
        "policy_authority": policy_authority,
        "customer_answering": customer_answering,
    }

    if effective_date is not None:
        metadata["effective_date"] = effective_date

    if superseded_date is not None:
        metadata["superseded_date"] = superseded_date

    if superseded_by is not None:
        metadata["superseded_by"] = superseded_by

    return DocumentChunk(
        chunk_id=f"{document_id}-chunk",
        text="Test policy content.",
        embedding_text="Test policy content.",
        filename=f"{document_id}.md",
        document_id=document_id,
        title="Test Policy",
        heading="Test Heading",
        heading_path=["Test Heading"],
        metadata=metadata,
        embedding=np.array([1.0, 0.0]),
    )


def test_active_official_document_is_authoritative():
    chunk = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
    )

    assert is_authoritative(chunk)


def test_draft_document_is_not_authoritative():
    chunk = make_chunk(
        document_id="MIG-TEST-04",
        status="draft",
        policy_authority="none",
        customer_answering=False,
    )

    assert not is_authoritative(chunk)


def test_non_official_document_is_not_authoritative():
    chunk = make_chunk(
        document_id="TEST-001",
        status="active",
        policy_authority="none",
    )

    assert not is_authoritative(chunk)


def test_non_customer_answering_document_is_not_authoritative():
    chunk = make_chunk(
        document_id="TEST-002",
        status="active",
        policy_authority="official",
        customer_answering=False,
    )

    assert not is_authoritative(chunk)


def test_explicit_supersession_is_detected():
    old = make_chunk(
        document_id="RET-2024-01",
        status="superseded",
        policy_authority="official",
        superseded_by="RET-2026-01",
    )

    new = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
    )

    assert source_supersedes(new, old)


def test_wrong_successor_does_not_count_as_supersession():
    old = make_chunk(
        document_id="RET-2024-01",
        status="superseded",
        policy_authority="official",
        superseded_by="OTHER-001",
    )

    new = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
    )

    assert not source_supersedes(new, old)


def test_legacy_policy_applies_before_supersession_date():
    legacy = make_chunk(
        document_id="RET-2024-01",
        status="superseded",
        policy_authority="official",
        effective_date=date(2024, 1, 1),
        superseded_date=date(2026, 4, 1),
        superseded_by="RET-2026-01",
    )

    context = ApplicabilityContext(
        purchase_date=date(2026, 3, 1)
    )

    assert applies_by_purchase_date(
        legacy,
        context,
    )


def test_legacy_policy_does_not_apply_after_supersession_date():
    legacy = make_chunk(
        document_id="RET-2024-01",
        status="superseded",
        policy_authority="official",
        effective_date=date(2024, 1, 1),
        superseded_date=date(2026, 4, 1),
        superseded_by="RET-2026-01",
    )

    context = ApplicabilityContext(
        purchase_date=date(2026, 5, 1)
    )

    assert not applies_by_purchase_date(
        legacy,
        context,
    )


def test_policy_before_effective_date_does_not_apply():
    current = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
        effective_date=date(2026, 4, 1),
    )

    context = ApplicabilityContext(
        purchase_date=date(2026, 3, 1)
    )

    assert not applies_by_purchase_date(
        current,
        context,
    )


def test_missing_purchase_date_does_not_reject_source():
    current = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
        effective_date=date(2026, 4, 1),
    )

    context = ApplicabilityContext()

    assert applies_by_purchase_date(
        current,
        context,
    )
    
def test_superseded_official_document_remains_authoritative_source():
    chunk = make_chunk(
        document_id="RET-2024-01",
        status="superseded",
        policy_authority="official",
    )

    assert is_authoritative(chunk)
    
def test_superseded_document_can_be_filtered_from_current_candidates():
    legacy = make_chunk(
        document_id="RET-2024-01",
        status="superseded",
        policy_authority="official",
        superseded_by="RET-2026-01",
    )

    current = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
    )

    legacy_result = RetrievalResult(
        chunk=legacy,
        score=0.95,
    )

    current_result = RetrievalResult(
        chunk=current,
        score=0.90,
    )

    candidates = filter_authoritative_candidates(
        [
            legacy_result,
            current_result,
        ]
    )

    assert len(candidates) == 2
    
def test_explicitly_superseded_source_is_removed_when_successor_exists():
    legacy = make_chunk(
        document_id="RET-2024-01",
        status="superseded",
        policy_authority="official",
        superseded_by="RET-2026-01",
    )

    current = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
    )

    results = [
        RetrievalResult(
            chunk=legacy,
            score=0.95,
        ),
        RetrievalResult(
            chunk=current,
            score=0.90,
        ),
    ]

    resolved = resolve_supersession(results)

    document_ids = [
        result.chunk.document_id
        for result in resolved
    ]

    assert "RET-2026-01" in document_ids
    assert "RET-2024-01" not in document_ids
    
def test_trailplus_membership_applies_to_trailplus_policy():
    chunk = make_chunk(
        document_id="MEM-2026-01",
        status="active",
        policy_authority="official",
    )

    context = ApplicabilityContext(
        membership_tier="trailplus"
    )

    assert applies_by_membership(
        chunk,
        context,
    )
    
def test_standard_membership_does_not_apply_to_trailplus_policy():
    chunk = make_chunk(
        document_id="MEM-2026-01",
        status="active",
        policy_authority="official",
    )

    context = ApplicabilityContext(
        membership_tier="standard"
    )

    assert not applies_by_membership(
        chunk,
        context,
    )
    
def test_missing_membership_does_not_assume_trailplus():
    chunk = make_chunk(
        document_id="MEM-2026-01",
        status="active",
        policy_authority="official",
    )

    context = ApplicabilityContext(
        membership_tier=None
    )

    assert not applies_by_membership(
        chunk,
        context,
    )
    
def test_membership_rule_does_not_reject_general_policy():
    chunk = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
    )

    context = ApplicabilityContext(
        membership_tier="standard"
    )

    assert applies_by_membership(
        chunk,
        context,
    )
    
def test_final_sale_policy_applies_to_change_of_mind():
    chunk = make_chunk(
        document_id="RET-2026-02",
        status="active",
        policy_authority="official",
    )

    context = ApplicabilityContext(
        request_type="change_of_mind",
        product_is_final_sale=True,
    )

    assert applies_by_final_sale(
        chunk,
        context,
    )
    
def test_final_sale_does_not_block_damaged_item_review():
    chunk = make_chunk(
        document_id="RET-2026-02",
        status="active",
        policy_authority="official",
    )

    context = ApplicabilityContext(
        request_type="damaged",
        product_is_final_sale=True,
    )

    assert not applies_by_final_sale(
        chunk,
        context,
    )

def test_final_sale_does_not_block_incorrect_item_review():
    chunk = make_chunk(
        document_id="RET-2026-02",
        status="active",
        policy_authority="official",
    )

    context = ApplicabilityContext(
        request_type="incorrect_item",
        product_is_final_sale=True,
    )

    assert not applies_by_final_sale(
        chunk,
        context,
    )

def test_final_sale_rule_does_not_filter_general_return_policy():
    chunk = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
    )

    context = ApplicabilityContext(
        request_type="change_of_mind",
        product_is_final_sale=True,
    )

    assert applies_by_final_sale(
        chunk,
        context,
    )
    
def test_product_page_final_sale_label_is_sufficient():
    context = ApplicabilityContext(
        final_sale_product_page=True,
        final_sale_cart=False,
        final_sale_order_confirmation=False,
    )

    assert determine_final_sale_status(context) is True
    
def test_cart_final_sale_label_is_sufficient():
    context = ApplicabilityContext(
        final_sale_product_page=False,
        final_sale_cart=True,
        final_sale_order_confirmation=False,
    )

    assert determine_final_sale_status(context) is True
    
def test_order_confirmation_final_sale_label_is_sufficient():
    context = ApplicabilityContext(
        final_sale_product_page=False,
        final_sale_cart=False,
        final_sale_order_confirmation=True,
    )

    assert determine_final_sale_status(context) is True
    
def test_promotion_code_alone_does_not_make_item_final_sale():
    context = ApplicabilityContext(
        final_sale_product_page=False,
        final_sale_cart=False,
        final_sale_order_confirmation=False,
    )

    assert determine_final_sale_status(context) is False
    
def test_missing_final_sale_information_is_unknown():
    context = ApplicabilityContext()

    assert determine_final_sale_status(context) is None
    
    
    
def test_multiple_active_official_sources_without_supersession_are_conflict_candidates():
    first = make_chunk(
        document_id="POLICY-A",
        status="active",
        policy_authority="official",
    )

    second = make_chunk(
        document_id="POLICY-B",
        status="active",
        policy_authority="official",
    )

    results = [
        RetrievalResult(
            chunk=first,
            score=0.95,
        ),
        RetrievalResult(
            chunk=second,
            score=0.92,
        ),
    ]

    assert detect_conflict(results)
    
    
def test_explicit_supersession_is_not_a_conflict():
    old = make_chunk(
        document_id="RET-2024-01",
        status="superseded",
        policy_authority="official",
        superseded_by="RET-2026-01",
    )

    new = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
    )

    results = [
        RetrievalResult(
            chunk=old,
            score=0.95,
        ),
        RetrievalResult(
            chunk=new,
            score=0.92,
        ),
    ]

    assert not detect_conflict(results)
    
def test_empty_retrieval_is_insufficient():
    result = resolve_policy([])

    assert result.status == ResolutionStatus.INSUFFICIENT
    assert result.sources == []
    
def test_only_untrusted_document_is_insufficient():
    draft = make_chunk(
        document_id="MIG-TEST-04",
        status="draft",
        policy_authority="none",
        customer_answering=False,
    )

    result = resolve_policy([
        RetrievalResult(
            chunk=draft,
            score=0.95,
        )
    ])

    assert result.status == ResolutionStatus.INSUFFICIENT
    assert result.sources == []
    
def test_current_policy_wins_over_superseded_legacy_policy():
    legacy = make_chunk(
        document_id="RET-2024-01",
        status="superseded",
        policy_authority="official",
        effective_date=date(2024, 1, 1),
        superseded_date=date(2026, 4, 1),
        superseded_by="RET-2026-01",
    )

    current = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
        effective_date=date(2026, 4, 1),
    )

    result = resolve_policy(
        [
            RetrievalResult(chunk=legacy, score=0.95),
            RetrievalResult(chunk=current, score=0.90),
        ],
        context=ApplicabilityContext(
            purchase_date=date(2026, 5, 1)
        ),
    )

    assert result.status == ResolutionStatus.RESOLVED

    document_ids = [
        source.chunk.document_id
        for source in result.sources
    ]

    assert document_ids == ["RET-2026-01"]
    
def test_legacy_policy_applies_to_pre_april_purchase():
    legacy = make_chunk(
        document_id="RET-2024-01",
        status="superseded",
        policy_authority="official",
        effective_date=date(2024, 1, 1),
        superseded_date=date(2026, 4, 1),
        superseded_by="RET-2026-01",
    )

    current = make_chunk(
        document_id="RET-2026-01",
        status="active",
        policy_authority="official",
        effective_date=date(2026, 4, 1),
    )

    result = resolve_policy(
        [
            RetrievalResult(chunk=current, score=0.95),
            RetrievalResult(chunk=legacy, score=0.90),
        ],
        context=ApplicabilityContext(
            purchase_date=date(2026, 3, 1)
        ),
    )

    assert result.status == ResolutionStatus.RESOLVED

    document_ids = [
        source.chunk.document_id
        for source in result.sources
    ]

    assert "RET-2024-01" in document_ids
    
    
def test_resolver_applies_membership_context():
    trailplus = make_chunk(
        document_id="MEM-2026-01",
        status="active",
        policy_authority="official",
    )

    result = resolve_policy(
        [
            RetrievalResult(
                chunk=trailplus,
                score=0.95,
            )
        ],
        context=ApplicabilityContext(
            membership_tier="trailplus",
        ),
    )

    assert result.status == ResolutionStatus.RESOLVED
    assert result.sources[0].chunk.document_id == "MEM-2026-01"

def test_resolver_does_not_select_trailplus_without_membership():
    trailplus = make_chunk(
        document_id="MEM-2026-01",
        status="active",
        policy_authority="official",
    )

    result = resolve_policy(
        [
            RetrievalResult(
                chunk=trailplus,
                score=0.95,
            )
        ],
        context=ApplicabilityContext(),
    )

    assert result.status == ResolutionStatus.INSUFFICIENT