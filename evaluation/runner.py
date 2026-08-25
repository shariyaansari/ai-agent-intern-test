from __future__ import annotations

from pathlib import Path

from app.orchestration import SessionContext
from scripts.test_agent import build_agent

from evaluation.assertions import evaluate_expectations
from evaluation.loader import load_cases
from evaluation.results import (
    EvaluationResult,
    EvaluationSummary,
)


VISIBLE_CASES = Path(
    "evaluation/visible-cases.json"
)


def run_case(
    agent,
    case: dict,
) -> EvaluationResult:

    session = SessionContext()

    last_response = None
    last_evidence = None

    for message in case["messages"]:
        last_response = agent.respond(
            message["content"],
            session,
        )

        last_evidence = agent.last_evidence

    failures = evaluate_expectations(
        response=last_response,
        evidence=last_evidence,
        expectations=case["expect"],
    )

    return EvaluationResult(
        case_id=case["id"],
        category=case["category"],
        passed=not failures,
        failures=failures,
    )


def run_evaluation() -> EvaluationSummary:
    cases = load_cases(
        VISIBLE_CASES
    )

    agent = build_agent()

    results = []

    for case in cases:
        result = run_case(
            agent,
            case,
        )

        results.append(result)

    return EvaluationSummary(
        results=results
    )


def print_summary(
    summary: EvaluationSummary,
) -> None:

    print()
    print("=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    for result in summary.results:
        status = (
            "PASS"
            if result.passed
            else "FAIL"
        )

        print(
            f"{status:4} "
            f"{result.case_id}"
        )

        for failure in result.failures:
            print(
                f"      - {failure}"
            )

    print()
    print("-" * 60)

    print(
        f"Total:  {summary.total}"
    )

    print(
        f"Passed: {summary.passed}"
    )

    print(
        f"Failed: {summary.failed}"
    )

    print()
    print("BY CATEGORY")

    for category, (
        passed,
        total,
    ) in summary.by_category().items():

        print(
            f"{category:25} "
            f"{passed}/{total}"
        )


def main() -> None:
    summary = run_evaluation()
    print_summary(summary)


if __name__ == "__main__":
    main()