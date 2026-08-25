from .context import (
    ContextResolution,
    SessionContext,
    is_order_follow_up,
    resolve_context,
    update_session_context,
)

from .router import (
    Intent,
    IntentSchema,
    RequestType,
    Route,
    RouteDecision,
    route_intent,
    route_query,
)

__all__ = [
    "ContextResolution",
    "Intent",
    "IntentSchema",
    "OrchestrationResult",
    "RequestType",
    "Route",
    "RouteDecision",
    "SessionContext",
    "orchestrate",
    "resolve_context",
    "update_session_context",
    "is_order_follow_up",
    "route_intent",
    "route_query",
]


def __getattr__(name: str):
    if name in {
        "OrchestrationResult",
        "orchestrate",
    }:
        from .agent import (
            OrchestrationResult,
            orchestrate,
        )

        return {
            "OrchestrationResult": OrchestrationResult,
            "orchestrate": orchestrate,
        }[name]

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )