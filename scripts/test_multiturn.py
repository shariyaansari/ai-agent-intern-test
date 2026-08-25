from app.llm import GroqClient
from app.orchestration import (
    SessionContext,
    orchestrate,
)


def main():
    client = GroqClient()

    session = SessionContext(
        active_topic="international shipping",
        last_user_message="Do you ship internationally?",
        last_resolved_query="Do you ship internationally?",
    )

    result = orchestrate(
        "What about Canada?",
        session,
        client,
    )

    print("CONTEXT:", result.context)
    print("INTENT:", result.intent)
    print("ROUTE:", result.route)


if __name__ == "__main__":
    main()