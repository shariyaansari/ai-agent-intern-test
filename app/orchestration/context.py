from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionContext:
    """
    Minimal structured context carried between turns.

    This is deliberately separate from the router.
    """

    last_user_message: str | None = None
    last_resolved_query: str | None = None
    active_topic: str | None = None
    order_id: str | None = None


@dataclass
class ContextResolution:
    resolved_query: str
    context_used: bool
    topic: str | None = None
    order_id: str | None = None
    
def resolve_context(
    message: str,
    session: SessionContext,
) -> ContextResolution:
    """
    Resolve a new message using structured session context.

    Context resolution happens before intent extraction and routing.
    """

    message = message.strip()

    if not message:
        return ContextResolution(
            resolved_query="",
            context_used=False,
            topic=session.active_topic,
            order_id=session.order_id,
        )

    normalized = message.lower()

    follow_up_prefixes = (
        "what about ",
        "how about ",
        "and ",
    )

    is_follow_up = normalized.startswith(
        follow_up_prefixes
    )

    # Order follow-up
    if (
        session.order_id
        and is_order_follow_up(message)
    ):
        return ContextResolution(
            resolved_query=(
                f"Order {session.order_id}: {message}"
            ),
            context_used=True,
            topic=session.active_topic,
            order_id=session.order_id,
        )

    # Topic follow-up
    if session.active_topic and is_follow_up:
        return ContextResolution(
            resolved_query=(
                f"{session.active_topic}: {message}"
            ),
            context_used=True,
            topic=session.active_topic,
            order_id=session.order_id,
        )

    return ContextResolution(
        resolved_query=message,
        context_used=False,
        topic=session.active_topic,
        order_id=session.order_id,
    )


def is_order_follow_up(message: str) -> bool:
    normalized = message.strip().lower()

    return normalized.startswith(
        (
            "when will it",
            "when will my",
            "where is it",
            "where is my",
            "has it",
            "what is the status",
            "what's the status",
        )
    )

def update_session_context(
    session: SessionContext,
    *,
    user_message: str,
    resolved_query: str,
    topic: str | None,
    order_id: str | None,
) -> None:
    session.last_user_message = user_message
    session.last_resolved_query = resolved_query

    if topic is not None:
        session.active_topic = topic

    if order_id is not None:
        session.order_id = order_id