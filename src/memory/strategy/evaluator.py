from dataclasses import dataclass

from src.memory.strategy.models import (
    StrategyAttempt,
    StrategyOutcome,
    StrategyRecord,
)


@dataclass(frozen=True)
class StrategyPerformance:
    strategy_id: str
    verified_attempts: int
    successes: int
    failures: int
    partial_successes: int
    unknown_outcomes: int
    success_rate: float
    partial_success_rate: float


class StrategyEvaluator:
    """Evaluate strategies using independently verified outcomes."""

    def evaluate(
        self,
        strategy: StrategyRecord,
        attempts: list[StrategyAttempt],
    ) -> StrategyPerformance:
        # Ignore attempts belonging to other strategies and
        # outcomes that have not been independently verified.
        verified_attempts = [
            attempt
            for attempt in attempts
            if (
                attempt.strategy_id == strategy.strategy_id
                and attempt.verified
            )
        ]

        successes = sum(
            attempt.outcome == StrategyOutcome.SUCCESS
            for attempt in verified_attempts
        )

        failures = sum(
            attempt.outcome == StrategyOutcome.FAILURE
            for attempt in verified_attempts
        )

        partial_successes = sum(
            attempt.outcome == StrategyOutcome.PARTIAL
            for attempt in verified_attempts
        )

        unknown_outcomes = sum(
            attempt.outcome == StrategyOutcome.UNKNOWN
            for attempt in verified_attempts
        )

        total = len(verified_attempts)

        return StrategyPerformance(
            strategy_id=strategy.strategy_id,
            verified_attempts=total,
            successes=successes,
            failures=failures,
            partial_successes=partial_successes,
            unknown_outcomes=unknown_outcomes,
            success_rate=successes / total if total else 0.0,
            partial_success_rate=(
                partial_successes / total if total else 0.0
            ),
        )
