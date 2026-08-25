from app.orchestration.router import (
    IntentSchema,
    Route,
    route_query,
)


def test_policy_question_routes_to_retrieval():
    result = route_query(
        "What is your return policy?"
    )

    assert result.route == Route.RETRIEVAL


def test_order_status_routes_to_order_tool():
    result = route_query(
        "Where is my order ORD-1007?"
    )

    assert result.route == Route.ORDER_TOOL


def test_policy_and_order_question_routes_to_both():
    result = route_query(
        "Can I return order ORD-1007?"
    )

    assert result.route == Route.BOTH


def test_general_message_needs_neither():
    result = route_query(
        "Hello"
    )

    assert result.route == Route.NONE


def test_intent_schema_disallows_additional_properties():
    schema = IntentSchema.model_json_schema()

    assert schema["additionalProperties"] is False