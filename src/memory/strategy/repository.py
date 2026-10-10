from pathlib import Path

from psycopg.types.json import Jsonb

from src.memory.storage.database import get_pool
from src.memory.strategy.models import StrategyAttempt, StrategyRecord


class StrategyRepository:


    def __init__(
        self,
        storage_dir: str = "data/memory/strategies",
    ) -> None:

        self.storage_dir = Path(storage_dir)
        self.strategies_dir = self.storage_dir / "records"
        self.attempts_dir = self.storage_dir / "attempts"

    @staticmethod
    def _validate_id(record_id: str) -> None:
        if not record_id or Path(record_id).name != record_id:
            raise ValueError("Invalid record ID")

    def save_strategy(self, strategy: StrategyRecord) -> None:
        self._validate_id(strategy.strategy_id)

        with get_pool().connection() as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO strategies (
                            strategy_id, name, description, task_type,
                            problem_pattern, steps, total_attempts,
                            successes, failures, partial_successes,
                            unknown_outcomes, status, created_at,
                            updated_at, metadata
                        )
                        VALUES (
                            %(strategy_id)s, %(name)s, %(description)s,
                            %(task_type)s, %(problem_pattern)s, %(steps)s,
                            %(total_attempts)s, %(successes)s, %(failures)s,
                            %(partial_successes)s, %(unknown_outcomes)s,
                            %(status)s, %(created_at)s, %(updated_at)s,
                            %(metadata)s
                        )
                        ON CONFLICT (strategy_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            task_type = EXCLUDED.task_type,
                            problem_pattern = EXCLUDED.problem_pattern,
                            steps = EXCLUDED.steps,
                            total_attempts = EXCLUDED.total_attempts,
                            successes = EXCLUDED.successes,
                            failures = EXCLUDED.failures,
                            partial_successes = EXCLUDED.partial_successes,
                            unknown_outcomes = EXCLUDED.unknown_outcomes,
                            status = EXCLUDED.status,
                            updated_at = EXCLUDED.updated_at,
                            metadata = EXCLUDED.metadata
                        """,
                        {
                            "strategy_id": strategy.strategy_id,
                            "name": strategy.name,
                            "description": strategy.description,
                            "task_type": strategy.task_type,
                            "problem_pattern": strategy.problem_pattern,
                            "steps": Jsonb(strategy.steps),
                            "total_attempts": strategy.total_attempts,
                            "successes": strategy.successes,
                            "failures": strategy.failures,
                            "partial_successes": strategy.partial_successes,
                            "unknown_outcomes": strategy.unknown_outcomes,
                            "status": strategy.status.value,
                            "created_at": strategy.created_at,
                            "updated_at": strategy.updated_at,
                            "metadata": Jsonb(strategy.metadata),
                        },
                    )



    def get_strategy_for_update(self, strategy_id: str, *, connection):

        self._validate_id(strategy_id)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT strategy_id, name, description, task_type,
                    problem_pattern, steps, total_attempts, successes,
                    failures, partial_successes, unknown_outcomes,
                    status, created_at, updated_at, metadata
                FROM strategies
                WHERE strategy_id = %s
                FOR UPDATE
                """,
                (strategy_id,),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            columns = [column.name for column in cursor.description]

        return StrategyRecord.model_validate(
            dict(zip(columns, row, strict=True))
        )


    def get_strategy(self, strategy_id: str) -> StrategyRecord | None:
        self._validate_id(strategy_id)

        with get_pool().connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT strategy_id, name, description, task_type,
                           problem_pattern, steps, total_attempts, successes,
                           failures, partial_successes, unknown_outcomes,
                           status, created_at, updated_at, metadata
                    FROM strategies
                    WHERE strategy_id = %s
                    """,
                    (strategy_id,),
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                columns = [
                    column.name for column in cursor.description
                ]

        return StrategyRecord.model_validate(
            dict(zip(columns, row, strict=True))
        )

    def list_strategies(self) -> list[StrategyRecord]:
        with get_pool().connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT strategy_id, name, description, task_type,
                           problem_pattern, steps, total_attempts, successes,
                           failures, partial_successes, unknown_outcomes,
                           status, created_at, updated_at, metadata
                    FROM strategies
                    ORDER BY created_at, strategy_id
                    """
                )
                rows = cursor.fetchall()
                columns = [
                    column.name for column in cursor.description
                ]

        return [
            StrategyRecord.model_validate(
                dict(zip(columns, row, strict=True))
            )
            for row in rows
        ]

    def delete_strategy(self, strategy_id: str) -> bool:
        self._validate_id(strategy_id)

        # The schema cascades deletion to the strategy's attempts.
        with get_pool().connection() as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM strategies
                        WHERE strategy_id = %s
                        """,
                        (strategy_id,),
                    )
                    return cursor.rowcount > 0

    @staticmethod
    def _refresh_statistics_in_transaction(
        cursor,
        strategy_id: str,
    ) -> None:
        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE verified
                ) AS total_attempts,
                COUNT(*) FILTER (
                    WHERE verified AND outcome = 'success'
                ) AS successes,
                COUNT(*) FILTER (
                    WHERE verified AND outcome = 'failure'
                ) AS failures,
                COUNT(*) FILTER (
                    WHERE verified AND outcome = 'partial'
                ) AS partial_successes,
                COUNT(*) FILTER (
                    WHERE verified AND outcome = 'unknown'
                ) AS unknown_outcomes
            FROM strategy_attempts
            WHERE strategy_id = %s
            """,
            (strategy_id,),
        )

        stats = cursor.fetchone()

        cursor.execute(
            """
            UPDATE strategies
            SET total_attempts = %s,
                successes = %s,
                failures = %s,
                partial_successes = %s,
                unknown_outcomes = %s,
                updated_at = NOW()
            WHERE strategy_id = %s
            """,
            (*stats, strategy_id),
        )

        if cursor.rowcount != 1:
            raise KeyError(f"Strategy not found: {strategy_id}")

    def save_attempt(
        self,
        attempt: StrategyAttempt,
        *,
        connection=None,
    ) -> None:
        """Save an attempt and refresh counters in the same transaction."""
        self._validate_id(attempt.attempt_id)
        self._validate_id(attempt.strategy_id)

        if connection is not None:
            with connection.cursor() as cursor:
                self._save_attempt_with_cursor(cursor, attempt)
            return

        with get_pool().connection() as conn:
            with conn.transaction():
                with conn.cursor() as cursor:
                    self._save_attempt_with_cursor(cursor, attempt)

    def _save_attempt_with_cursor(self, cursor, attempt: StrategyAttempt) -> None:
        cursor.execute(
            """
            SELECT strategy_id
            FROM strategy_attempts
            WHERE attempt_id = %s
            FOR UPDATE
            """,
            (attempt.attempt_id,),
        )
        previous_row = cursor.fetchone()
        previous_strategy_id = (
            previous_row[0] if previous_row is not None else None
        )

        cursor.execute(
            """
            INSERT INTO strategy_attempts (
                attempt_id, strategy_id, task_id, outcome,
                action_taken, observation, evidence, verified,
                created_at, metadata
            )
            VALUES (
                %(attempt_id)s, %(strategy_id)s, %(task_id)s,
                %(outcome)s, %(action_taken)s, %(observation)s,
                %(evidence)s, %(verified)s, %(created_at)s, %(metadata)s
            )
            ON CONFLICT (attempt_id) DO UPDATE SET
                strategy_id = EXCLUDED.strategy_id,
                task_id = EXCLUDED.task_id,
                outcome = EXCLUDED.outcome,
                action_taken = EXCLUDED.action_taken,
                observation = EXCLUDED.observation,
                evidence = EXCLUDED.evidence,
                verified = EXCLUDED.verified,
                metadata = EXCLUDED.metadata
            """,
            {
                "attempt_id": attempt.attempt_id,
                "strategy_id": attempt.strategy_id,
                "task_id": attempt.task_id,
                "outcome": attempt.outcome.value,
                "action_taken": attempt.action_taken,
                "observation": attempt.observation,
                "evidence": Jsonb(attempt.evidence),
                "verified": attempt.verified,
                "created_at": attempt.created_at,
                "metadata": Jsonb(attempt.metadata),
            },
        )

        strategy_ids = {attempt.strategy_id}
        if previous_strategy_id is not None:
            strategy_ids.add(previous_strategy_id)

        for strategy_id in sorted(strategy_ids):
            self._refresh_statistics_in_transaction(cursor, strategy_id)

    def get_attempt(
        self,
        attempt_id: str,
    ) -> StrategyAttempt | None:
        self._validate_id(attempt_id)

        with get_pool().connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT attempt_id, strategy_id, task_id, outcome,
                           action_taken, observation, evidence, verified,
                           created_at, metadata
                    FROM strategy_attempts
                    WHERE attempt_id = %s
                    """,
                    (attempt_id,),
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                columns = [
                    column.name for column in cursor.description
                ]

        return StrategyAttempt.model_validate(
            dict(zip(columns, row, strict=True))
        )

    def list_attempts(
        self,
        strategy_id: str | None = None,
    ) -> list[StrategyAttempt]:
        with get_pool().connection() as connection:
            with connection.cursor() as cursor:
                if strategy_id is None:
                    cursor.execute(
                        """
                        SELECT attempt_id, strategy_id, task_id, outcome,
                               action_taken, observation, evidence, verified,
                               created_at, metadata
                        FROM strategy_attempts
                        ORDER BY created_at, attempt_id
                        """
                    )
                else:
                    self._validate_id(strategy_id)
                    cursor.execute(
                        """
                        SELECT attempt_id, strategy_id, task_id, outcome,
                               action_taken, observation, evidence, verified,
                               created_at, metadata
                        FROM strategy_attempts
                        WHERE strategy_id = %s
                        ORDER BY created_at, attempt_id
                        """,
                        (strategy_id,),
                    )

                rows = cursor.fetchall()
                columns = [
                    column.name for column in cursor.description
                ]

        return [
            StrategyAttempt.model_validate(
                dict(zip(columns, row, strict=True))
            )
            for row in rows
        ]


    def delete_attempt(self, attempt_id: str, *, connection=None) -> bool:
        self._validate_id(attempt_id)

        if connection is not None:
            with connection.cursor() as cursor:
                return self._delete_attempt_with_cursor(cursor, attempt_id)

        with get_pool().connection() as conn:
            with conn.transaction():
                with conn.cursor() as cursor:
                    return self._delete_attempt_with_cursor(cursor, attempt_id)


    def _delete_attempt_with_cursor(self, cursor, attempt_id: str) -> bool:
        cursor.execute(
            """
            DELETE FROM strategy_attempts
            WHERE attempt_id = %s
            RETURNING strategy_id
            """,
            (attempt_id,),
        )

        row = cursor.fetchone()
        if row is None:
            return False

        self._refresh_statistics_in_transaction(cursor, row[0])
        return True
