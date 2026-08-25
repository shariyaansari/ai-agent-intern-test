from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvaluationResult:
    case_id: str
    category: str
    passed: bool
    failures: list[str] = field(
        default_factory=list
    )


@dataclass
class EvaluationSummary:
    results: list[EvaluationResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(
            result.passed
            for result in self.results
        )

    @property
    def failed(self) -> int:
        return self.total - self.passed

    def by_category(self) -> dict[str, tuple[int, int]]:
        categories: dict[str, tuple[int, int]] = {}

        for result in self.results:
            passed, total = categories.get(
                result.category,
                (0, 0),
            )

            categories[result.category] = (
                passed + int(result.passed),
                total + 1,
            )

        return categories