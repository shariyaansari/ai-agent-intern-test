from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
import re

ORDER_ID_PATTERN = re.compile(
    r"^ORD-\d+$",
    re.IGNORECASE,
)

class Route(str, Enum):
    RETRIEVAL = "retrieval"
    ORDER_TOOL = "order_tool"
    BOTH = "both"
    NONE = "none"


@dataclass
class RouteDecision:
    route: Route
    reason: str
    
class RequestType(str, Enum):
    GENERAL = "general"
    POLICY = "policy"
    ORDER = "order"
    ACTION = "action"
    SENSITIVE = "sensitive"

class IntentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_type: RequestType
    needs_retrieval: bool
    needs_order_lookup: bool
    order_id: str | None = Field(
        description="Explicit order ID supplied by the customer.",
    )
    membership_tier: str | None = Field(
        description=(
            "Membership tier explicitly stated or clearly established "
            "by the customer, such as trailplus or standard. "
            "Use null when it is not established."
        ),
    )

@dataclass
class Intent:
    request_type: RequestType
    needs_retrieval: bool
    needs_order_lookup: bool
    order_id: str | None = None
    membership_tier: str | None = None

def route_query(query: str) -> RouteDecision:
    """
    Determine which system capability is required.

    This is intentionally deterministic for the initial
    implementation.
    """

    normalized = query.strip().lower()

    if not normalized:
        return RouteDecision(
            route=Route.NONE,
            reason="Empty query.",
        )

    order_terms = (
        "order",
        "tracking",
        "where is my order",
        "when will my order arrive",
        "delivery status",
        "shipment status",
    )

    policy_terms = (
        "return",
        "refund",
        "warranty",
        "shipping",
        "ship",
        "final sale",
        "gift card",
        "price adjustment",
        "cancel",
        "cancellation",
        "membership",
        "trailplus",
    )

    needs_order = any(
        term in normalized
        for term in order_terms
    )

    needs_retrieval = any(
        term in normalized
        for term in policy_terms
    )

    if needs_order and needs_retrieval:
        return RouteDecision(
            route=Route.BOTH,
            reason="The query requires order data and policy information.",
        )

    if needs_order:
        return RouteDecision(
            route=Route.ORDER_TOOL,
            reason="The query requires order-specific information.",
        )

    if needs_retrieval:
        return RouteDecision(
            route=Route.RETRIEVAL,
            reason="The query requires knowledge-base information.",
        )

    return RouteDecision(
        route=Route.NONE,
        reason="No retrieval or order lookup is required.",
    )
    
def validate_intent(intent: Intent) -> Intent:
    """
    Apply application-level validation to LLM-produced intent.
    """
    if intent.membership_tier is not None:
        intent.membership_tier = (
            intent.membership_tier.strip().lower()
        )

        if intent.membership_tier not in {
            "trailplus",
            "standard",
        }:
            intent.membership_tier = None

    if intent.order_id is not None:
        order_id = intent.order_id.strip().upper()

        if not ORDER_ID_PATTERN.fullmatch(order_id):
            intent.order_id = None
            intent.needs_order_lookup = False
        else:
            intent.order_id = order_id

    if intent.request_type == RequestType.SENSITIVE:
        intent.needs_retrieval = False
        intent.needs_order_lookup = False

    return intent

def route_intent(intent: Intent) -> RouteDecision:
    intent = validate_intent(intent)

    if (
        intent.needs_retrieval
        and intent.needs_order_lookup
    ):
        return RouteDecision(
            route=Route.BOTH,
            reason="Intent requires knowledge-base retrieval and order lookup.",
        )

    if intent.needs_order_lookup:
        return RouteDecision(
            route=Route.ORDER_TOOL,
            reason="Intent requires order-specific information.",
        )

    if intent.needs_retrieval:
        return RouteDecision(
            route=Route.RETRIEVAL,
            reason="Intent requires knowledge-base information.",
        )

    return RouteDecision(
        route=Route.NONE,
        reason="Intent requires neither retrieval nor order lookup.",
    )