-- =============================================================
-- Task 2 — call_records table for storing customer interactions
-- =============================================================

CREATE TABLE call_records (
    id              SERIAL PRIMARY KEY,
    customer_phone  VARCHAR(20)   NOT NULL,
    channel         VARCHAR(10)   NOT NULL CHECK (channel IN ('voice', 'whatsapp', 'chat')),
    transcript      TEXT          NOT NULL,
    ai_response     TEXT,
    intent          VARCHAR(100),
    outcome         VARCHAR(20)   NOT NULL CHECK (outcome IN ('resolved', 'escalated', 'failed')),
    confidence_score NUMERIC(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    csat_score      SMALLINT      CHECK (csat_score >= 1 AND csat_score <= 5),  -- nullable, collected after call
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    duration_seconds INTEGER      NOT NULL DEFAULT 0
);

-- INDEX 1: We frequently look up a customer's recent calls by phone number
CREATE INDEX idx_call_records_phone ON call_records (customer_phone);

-- INDEX 2: We filter/report on calls by time range (e.g., "last 7 days")
CREATE INDEX idx_call_records_created_at ON call_records (created_at);

-- INDEX 3: We query by outcome to calculate resolution rates per intent
CREATE INDEX idx_call_records_outcome_intent ON call_records (outcome, intent);
