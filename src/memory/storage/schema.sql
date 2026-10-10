CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    request_id TEXT,
    objective TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending', 'running', 'paused', 'completed', 'failed'
        )),
    current_step TEXT,
    completed_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    pending_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    attempt_count INTEGER NOT NULL DEFAULT 0
        CHECK (attempt_count >= 0),
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_tasks_request_id
    ON tasks (request_id);

CREATE INDEX IF NOT EXISTS idx_tasks_status
    ON tasks (status);


CREATE TABLE IF NOT EXISTS experiences (
    experience_id TEXT PRIMARY KEY,
    task_id TEXT REFERENCES tasks(task_id) ON DELETE SET NULL,
    request_id TEXT,
    query TEXT NOT NULL,
    task_type TEXT,
    problem_pattern TEXT NOT NULL,
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    diagnosis TEXT NOT NULL,
    action TEXT NOT NULL,
    outcome TEXT NOT NULL DEFAULT 'unknown'
        CHECK (outcome IN ('success', 'failure', 'partial', 'unknown')),
    status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (status IN ('candidate', 'verified', 'rejected')),
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0
        CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_experiences_pattern
    ON experiences (problem_pattern);

CREATE INDEX IF NOT EXISTS idx_experiences_status
    ON experiences (status);

CREATE INDEX IF NOT EXISTS idx_experiences_task_id
    ON experiences (task_id);


CREATE TABLE IF NOT EXISTS experience_evidence (
    evidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experience_id TEXT NOT NULL
        REFERENCES experiences(experience_id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL
        CHECK (evidence_type IN (
            'test_result',
            'execution_result',
            'tool_result',
            'human_feedback',
            'llm_assessment',
            'other'
        )),
    description TEXT NOT NULL,
    source TEXT,
    supports_outcome BOOLEAN NOT NULL DEFAULT TRUE,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_experience_id
    ON experience_evidence (experience_id);


CREATE TABLE IF NOT EXISTS strategies (
    strategy_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    task_type TEXT NOT NULL,
    problem_pattern TEXT,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_attempts INTEGER NOT NULL DEFAULT 0
        CHECK (total_attempts >= 0),
    successes INTEGER NOT NULL DEFAULT 0
        CHECK (successes >= 0),
    failures INTEGER NOT NULL DEFAULT 0
        CHECK (failures >= 0),
    partial_successes INTEGER NOT NULL DEFAULT 0
        CHECK (partial_successes >= 0),
    unknown_outcomes INTEGER NOT NULL DEFAULT 0
        CHECK (unknown_outcomes >= 0),
    status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (status IN ('candidate', 'active', 'disabled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CHECK (
        total_attempts =
        successes + failures + partial_successes + unknown_outcomes
    )
);

CREATE INDEX IF NOT EXISTS idx_strategies_task_type
    ON strategies (task_type);

CREATE INDEX IF NOT EXISTS idx_strategies_status
    ON strategies (status);


CREATE TABLE IF NOT EXISTS strategy_attempts (
    attempt_id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL
        REFERENCES strategies(strategy_id) ON DELETE CASCADE,
    task_id TEXT REFERENCES tasks(task_id) ON DELETE SET NULL,
    outcome TEXT NOT NULL DEFAULT 'unknown'
        CHECK (outcome IN ('success', 'failure', 'partial', 'unknown')),
    action_taken TEXT NOT NULL,
    observation TEXT,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_attempts_strategy_id
    ON strategy_attempts (strategy_id);

CREATE INDEX IF NOT EXISTS idx_attempts_task_id
    ON strategy_attempts (task_id);

CREATE INDEX IF NOT EXISTS idx_attempts_verified
    ON strategy_attempts (verified);


-- Idempotency ledger for atomic learning operations.
-- A repeated operation_key must reuse its existing learning result.
CREATE TABLE IF NOT EXISTS learning_operations (
    operation_key TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    experience_id TEXT NOT NULL
        REFERENCES experiences(experience_id) ON DELETE RESTRICT,
    attempt_id TEXT
        REFERENCES strategy_attempts(attempt_id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_learning_operations_experience
    ON learning_operations (experience_id);

CREATE TABLE IF NOT EXISTS memory_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    task_id TEXT,
    request_id TEXT,
    experience_id TEXT,
    strategy_id TEXT,
    attempt_id TEXT,
    occurred_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    schema_version INTEGER NOT NULL DEFAULT 1
        CHECK (schema_version >= 1),
    source TEXT NOT NULL DEFAULT 'soul.memory',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_events_type_time
    ON memory_events (event_type, occurred_at);

CREATE INDEX IF NOT EXISTS idx_memory_events_task_time
    ON memory_events (task_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_memory_events_request_time
    ON memory_events (request_id, occurred_at);


CREATE TABLE IF NOT EXISTS event_outbox (
    event_id TEXT PRIMARY KEY
        REFERENCES memory_events(event_id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'delivered', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 0
        CHECK (attempts >= 0),
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    claimed_at TIMESTAMPTZ,
    claim_token TEXT,
    delivered_at TIMESTAMPTZ
);

-- Safe migration for databases where event_outbox already exists.
-- This does not delete or reset existing data.
ALTER TABLE event_outbox
    ADD COLUMN IF NOT EXISTS claim_token TEXT;

CREATE INDEX IF NOT EXISTS idx_event_outbox_pending
    ON event_outbox (next_attempt_at, created_at)
    WHERE status IN ('pending', 'processing');
