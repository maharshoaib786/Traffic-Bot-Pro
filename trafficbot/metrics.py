"""Metrics collection utilities for Traffic Bot."""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class VisitMetrics:
    """Aggregate statistics for a campaign run."""

    successes: int = 0
    failures: int = 0
    durations: List[float] = field(default_factory=list)
    errors: Dict[str, int] = field(default_factory=dict)

    def record_success(self, duration: float) -> None:
        self.successes += 1
        if duration >= 0:
            self.durations.append(duration)

    def record_failure(self, reason: str) -> None:
        self.failures += 1
        self.errors[reason] = self.errors.get(reason, 0) + 1

    @property
    def total(self) -> int:
        return self.successes + self.failures

    def summary(self) -> Dict[str, float | int | None]:
        """Return friendly metrics for logging or export."""

        avg_duration = statistics.mean(self.durations) if self.durations else None
        return {
            "total": self.total,
            "successes": self.successes,
            "failures": self.failures,
            "avg_duration": avg_duration,
            "min_duration": min(self.durations) if self.durations else None,
            "max_duration": max(self.durations) if self.durations else None,
            "errors": dict(self.errors),
        }

    def as_text(self) -> str:
        summary = self.summary()
        parts = [
            f"Visits: {summary['total']}",
            f"Successes: {summary['successes']}",
            f"Failures: {summary['failures']}",
        ]
        if summary["avg_duration"] is not None:
            parts.append(f"Avg duration: {summary['avg_duration']:.2f}s")
        if summary["errors"]:
            parts.append(f"Errors: {summary['errors']}")
        return " | ".join(parts)
