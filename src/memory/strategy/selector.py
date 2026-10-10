from dataclasses import dataclass

from src.memory.strategy.manager import StrategyManager
from src.memory.strategy.models import StrategyRecord, StrategyStatus


@dataclass(frozen=True)
class StrategyRecommendation:
    strategy: StrategyRecord
    score: float
    verified_attempts: int
    success_rate: float
    reason: str


class StrategySelector:
    """Recommend a strategy using task compatibility and verified history."""

    def __init__(
        self,
        manager: StrategyManager | None = None,
        *,
        minimum_attempts: int = 3,
    ) -> None:
        if minimum_attempts < 1:
            raise ValueError("minimum_attempts must be at least 1")

        self.manager = manager or StrategyManager()
        self.minimum_attempts = minimum_attempts

    def select(
        self,
        *,
        task_type: str,
        problem_pattern: str | None = None,
        limit: int = 3,
    ) -> list[StrategyRecommendation]:
        if not task_type.strip():
            raise ValueError("Task type cannot be empty")
        if limit < 1:
            raise ValueError("limit must be at least 1")

        recommendations: list[StrategyRecommendation] = []

        for strategy in self.manager.list_strategies():
            if strategy.status != StrategyStatus.ACTIVE:
                continue

            if strategy.task_type.casefold() != task_type.casefold():
                continue

            if (
                problem_pattern is not None
                and strategy.problem_pattern is not None
                and strategy.problem_pattern.casefold()
                != problem_pattern.casefold()
            ):
                continue

            performance = self.manager.get_performance(strategy.strategy_id)

            # Compatibility establishes eligibility. Historical performance
            # is only used when enough verified attempts exist.
            score = 1.0
            reason = "Matches the requested task type."

            if problem_pattern and strategy.problem_pattern:
                score += 1.0
                reason = "Matches task type and problem pattern."

            if performance.verified_attempts >= self.minimum_attempts:
                score += performance.success_rate
                reason += " Includes verified historical performance."
            else:
                reason += " Insufficient verified history; performance is unproven."

            recommendations.append(
                StrategyRecommendation(
                    strategy=strategy,
                    score=score,
                    verified_attempts=performance.verified_attempts,
                    success_rate=performance.success_rate,
                    reason=reason,
                )
            )

        recommendations.sort(
            key=lambda item: (
                -item.score,
                -item.verified_attempts,
                item.strategy.name.casefold(),
            )
        )

        return recommendations[:limit]
