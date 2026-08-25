from app.orchestration import SessionContext
from scripts.test_agent import build_agent


def main() -> None:
    agent = build_agent()
    session = SessionContext()

    print("Aster & Row Support Agent")
    print("Type 'exit' or 'quit' to leave.\n")

    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not message:
            continue

        if message.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        try:
            response = agent.respond(
                message,
                session,
            )

            print(f"\nAgent: {response.answer}")

            if response.sources:
                print("\nSources:")
                for source in response.sources:
                    print(
                        f"- {source.document_id} | "
                        f"{source.filename} | "
                        f"{source.heading}"
                    )

            if response.needs_human:
                print("\nHuman assistance is recommended.")

            print()

        except Exception as exc:
            print(f"\nAgent error: {exc}\n")


if __name__ == "__main__":
    main()