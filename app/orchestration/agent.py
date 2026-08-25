from __future__ import annotations

from dataclasses import dataclass

from app.llm import GroqClient
from app.llm.intent import extract_intent
from app.orchestration.context import (
    ContextResolution,
    SessionContext,
    resolve_context,
)
from app.orchestration.router import (
    Intent,
    RouteDecision,
    route_intent,
)

@dataclass
class OrchestrationResult:
    context: ContextResolution
    intent: Intent
    route: RouteDecision


def orchestrate(
    message: str,
    session: SessionContext,
    llm: GroqClient,
) -> OrchestrationResult:
    """
    Resolve session context, extract intent, and determine route.

    This function does not execute retrieval or tools yet.
    """

    context = resolve_context(
        message,
        session,
    )

    intent = extract_intent(
        llm,
        context.resolved_query,
    )

    route = route_intent(intent)

    return OrchestrationResult(
        context=context,
        intent=intent,
        route=route,
    )