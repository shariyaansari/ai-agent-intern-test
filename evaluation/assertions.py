from __future__ import annotations

from typing import Any


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def assert_contains(
    answer: str,
    required: list[str],
) -> list[str]:
    normalized = normalize(answer)
    failures = []

    for phrase in required:
        if normalize(phrase) not in normalized:
            failures.append(
                f"Missing required text: {phrase!r}"
            )

    return failures


def assert_not_contains(
    answer: str,
    forbidden: list[str],
) -> list[str]:
    normalized = normalize(answer)
    failures = []

    for phrase in forbidden:
        if normalize(phrase) in normalized:
            failures.append(
                f"Contains forbidden text: {phrase!r}"
            )

    return failures


def assert_sources(
    response: Any,
    required_sources: list[str],
) -> list[str]:
    actual_sources = {
        source.filename
        for source in response.sources
    }

    failures = []

    for filename in required_sources:
        if filename not in actual_sources:
            failures.append(
                f"Missing required source: {filename!r}"
            )

    return failures


def assert_handoff(
    response: Any,
    expected: bool,
) -> list[str]:
    if response.needs_human != expected:
        return [
            (
                "Expected needs_human="
                f"{expected}, got "
                f"{response.needs_human}"
            )
        ]

    return []


def assert_must_not_include(
    answer: str,
    forbidden: list[str],
) -> list[str]:
    return assert_not_contains(
        answer,
        forbidden,
    )
    
def assert_tool_calls(
    evidence: Any,
    expected_tool: str,
) -> list[str]:
    failures = []

    if expected_tool == "not_called":
        if evidence.order_result is not None:
            failures.append(
                "Order tool was called unexpectedly."
            )

    elif expected_tool == "order_lookup":
        if evidence.order_result is None:
            failures.append(
                "Expected order lookup but it was not called."
            )

    elif expected_tool == "not_called_without_id":
        if evidence.order_result is not None:
            failures.append(
                "Order tool was called without an order ID."
            )

    return failures

def assert_tool_arguments(
    evidence: Any,
    expected: dict[str, Any],
) -> list[str]:
    failures = []

    order_result = evidence.order_result

    if order_result is None:
        return [
            "Cannot verify tool arguments: order tool was not called."
        ]

    order = order_result.order

    if order is None:
        return [
            "Cannot verify tool arguments: no order was returned."
        ]

    actual_order_id = order.get("order_id")

    expected_order_id = expected.get(
        "order_id"
    )

    if actual_order_id != expected_order_id:
        failures.append(
            (
                "Expected order ID "
                f"{expected_order_id!r}, "
                f"got {actual_order_id!r}"
            )
        )

    return failures

def evaluate_expectations(
    response: Any,
    evidence: Any,
    expectations: dict[str, Any],
) -> list[str]:
    failures: list[str] = []

    failures.extend(
        assert_contains(
            response.answer,
            expectations.get(
                "must_include",
                [],
            ),
        )
    )

    failures.extend(
        assert_not_contains(
            response.answer,
            expectations.get(
                "must_not_include",
                [],
            ),
        )
    )

    failures.extend(
        assert_sources(
            response,
            expectations.get(
                "required_sources",
                [],
            ),
        )
    )

    failures.extend(
        assert_handoff(
            response,
            expectations.get(
                "handoff",
                False,
            ),
        )
    )

    tool = expectations.get("tool")

    if tool:
        failures.extend(
            assert_tool_calls(
                evidence,
                tool,
            )
        )

    tool_arguments = expectations.get(
        "tool_arguments"
    )

    if tool_arguments:
        failures.extend(
            assert_tool_arguments(
                evidence,
                tool_arguments,
            )
        )

    return failures
