from src.memory.strategy.evaluator import StrategyEvaluator
from src.memory.strategy.models import (
    StrategyAttempt,
    StrategyOutcome,
    StrategyRecord,
    StrategyStatus,
    utc_now,
)
from src.memory.strategy.repository import StrategyRepository


class StrategyManager:


    def __init__(
        self,
        repository: StrategyRepository | None = None,
    ) -> None:
        self.repository = repository or StrategyRepository()
        self._evaluator = StrategyEvaluator()

    def register_strategy(
        self,
        *,
        name: str,
        description: str,
        task_type: str,
        problem_pattern: str | None = None,
        steps: list[str] | None = None,
    ) -> StrategyRecord:
        if not name.strip():
            raise ValueError("Strategy name cannot be empty")
        if not description.strip():
            raise ValueError("Strategy description cannot be empty")
        if not task_type.strip():
            raise ValueError("Task type cannot be empty")

        strategy = StrategyRecord(
            strategy_id=self._new_strategy_id(),
            name=name,
            description=description,
            task_type=task_type,
            problem_pattern=problem_pattern,
            steps=list(steps or []),
        )

        self.repository.save_strategy(strategy)
        return strategy

    @staticmethod
    def _new_strategy_id() -> str:
        from uuid import uuid4
        return str(uuid4())

    def get_strategy(self, strategy_id: str) -> StrategyRecord | None:
        return self.repository.get_strategy(strategy_id)

    def list_strategies(self) -> list[StrategyRecord]:
        return self.repository.list_strategies()

    def record_attempt(
        self,
        *,
        strategy_id: str,
        action_taken: str,
        task_id: str | None = None,
        outcome: StrategyOutcome = StrategyOutcome.UNKNOWN,
        observation: str | None = None,
        evidence: list[str] | None = None,
        verified: bool = False,
        connection=None,
    ) -> StrategyAttempt:
        if connection is not None:
            strategy = self.repository.get_strategy_for_update(
                strategy_id,
                connection=connection,
            )
            if strategy is None:
                raise KeyError(f"Strategy not found: {strategy_id}")
        else:
            strategy = self._require_strategy(strategy_id)

        if strategy.status == StrategyStatus.DISABLED:
            raise ValueError("Cannot record an attempt for a disabled strategy")

        if not action_taken.strip():
            raise ValueError("Action taken cannot be empty")

        if verified and outcome == StrategyOutcome.UNKNOWN:
            raise ValueError(
                "An unknown outcome cannot be marked as verified"
            )

        attempt = StrategyAttempt(
            attempt_id=self._new_strategy_id(),
            strategy_id=strategy_id,
            task_id=task_id,
            action_taken=action_taken,
            outcome=outcome,
            observation=observation,
            evidence=list(evidence or []),
            verified=verified,
        )

        self.repository.save_attempt(attempt, connection=connection)
        return attempt

    def get_attempt(self, attempt_id: str) -> StrategyAttempt | None:
        return self.repository.get_attempt(attempt_id)

    def list_attempts(
        self,
        strategy_id: str | None = None,
    ) -> list[StrategyAttempt]:
        return self.repository.list_attempts(strategy_id)

    def verify_attempt(
        self,
        attempt_id: str,
        *,
        outcome: StrategyOutcome,
        evidence: list[str],
    ) -> StrategyAttempt:
        attempt = self.repository.get_attempt(attempt_id)

        if attempt is None:
            raise KeyError(f"Attempt not found: {attempt_id}")

        if outcome == StrategyOutcome.UNKNOWN:
            raise ValueError("Cannot verify an unknown outcome")

        if not evidence or not any(item.strip() for item in evidence):
            raise ValueError("Evidence is required to verify an attempt")

        updated_attempt = attempt.model_copy(
            update={
                "outcome": outcome,
                "evidence": list(evidence),
                "verified": True,
            }
        )

        self.repository.save_attempt(updated_attempt)
        return updated_attempt

    def get_performance(self, strategy_id: str):
        strategy = self._require_strategy(strategy_id)
        attempts = self.repository.list_attempts(strategy_id)
        return self._evaluator.evaluate(strategy, attempts)

    def set_strategy_status(
        self,
        strategy_id: str,
        status: StrategyStatus,
    ) -> StrategyRecord:
        strategy = self._require_strategy(strategy_id)
        strategy.status = status
        strategy.updated_at = utc_now()
        self.repository.save_strategy(strategy)
        return strategy

    def _require_strategy(self, strategy_id: str) -> StrategyRecord:
        strategy = self.repository.get_strategy(strategy_id)

        if strategy is None:
            raise KeyError(f"Strategy not found: {strategy_id}")

        return strategy
