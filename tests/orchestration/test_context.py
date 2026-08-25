from app.orchestration.context import (
    SessionContext,
    resolve_context,
)


def test_follow_up_can_use_previous_shipping_topic():
    session = SessionContext(
        last_user_message="Do you ship internationally?",
        last_resolved_query="Do you ship internationally?",
        active_topic="international shipping",
    )

    result = resolve_context(
        "What about Canada?",
        session,
    )

    assert result.context_used is True
    assert "international shipping" in result.resolved_query
    assert "Canada" in result.resolved_query


def test_standalone_question_does_not_use_context():
    session = SessionContext(
        active_topic="international shipping",
    )

    result = resolve_context(
        "What is your warranty policy?",
        session,
    )

    assert result.context_used is False
    assert result.resolved_query == "What is your warranty policy?"


def test_empty_message_is_safe():
    session = SessionContext()

    result = resolve_context(
        "",
        session,
    )

    assert result.resolved_query == ""
    assert result.context_used is False
    
def test_follow_up_preserves_previous_topic():
    session = SessionContext(
        last_user_message="Do you ship internationally?",
        last_resolved_query="Do you ship internationally?",
        active_topic="international shipping",
    )

    result = resolve_context(
        "What about Canada?",
        session,
    )

    assert result.context_used is True
    assert result.resolved_query == (
        "international shipping: What about Canada?"
    )
    
def test_warranty_follow_up_uses_previous_topic():
    session = SessionContext(
        active_topic="warranty",
        last_resolved_query="What is the warranty for backpacks?",
    )

    result = resolve_context(
        "What about drinkware?",
        session,
    )

    assert result.context_used is True
    assert result.resolved_query == (
        "warranty: What about drinkware?"
    )

def test_order_follow_up_preserves_order_id():
    session = SessionContext(
        active_topic="order status",
        order_id="ORD-1007",
        last_resolved_query="Where is ORD-1007?",
    )

    result = resolve_context(
        "When will it arrive?",
        session,
    )

    assert result.context_used is True
    assert result.order_id == "ORD-1007"
    assert "ORD-1007" in result.resolved_query
    
def test_unrelated_question_does_not_use_previous_context():
    session = SessionContext(
        active_topic="warranty",
        order_id="ORD-1007",
    )

    result = resolve_context(
        "What is your gift card policy?",
        session,
    )

    assert result.context_used is False
    assert result.resolved_query == (
        "What is your gift card policy?"
    )