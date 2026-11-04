CREATE SCHEMA analytics;
REVOKE ALL ON SCHEMA analytics FROM PUBLIC;
CREATE TABLE analytics.publication (
    publication_id text PRIMARY KEY,
    reference_key text NOT NULL,
    cutoff timestamptz NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL CHECK (period_end > period_start),
    zone text NOT NULL,
    rules_hash text NOT NULL,
    published_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE analytics.runs (
    run_id uuid PRIMARY KEY,
    publication_id text REFERENCES analytics.publication,
    attempted_publication_id text,
    started_at timestamptz NOT NULL,
    finished_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    status text NOT NULL CHECK (status IN ('PUBLISHED','REUSED','FAILED')),
    diagnostic text,
    CHECK ((status = 'FAILED') = (publication_id IS NULL))
);
CREATE TABLE analytics.scenarios (
    publication_id text REFERENCES analytics.publication NOT NULL,
    scenario text NOT NULL CHECK (scenario IN ('BASE','EMPTY','LATE')),
    PRIMARY KEY (publication_id, scenario)
);
CREATE TABLE analytics.deliveries (
    publication_id text NOT NULL,
    scenario text NOT NULL,
    delivery_key text NOT NULL,
    delivery_id text NOT NULL,
    promised_at timestamptz,
    completed_at timestamptz,
    completed_local_date date,
    contested boolean NOT NULL,
    has_received_document boolean NOT NULL,
    first_valid_at timestamptz,
    receipt_hours numeric,
    in_cohort boolean NOT NULL,
    PRIMARY KEY (publication_id, scenario, delivery_key),
    FOREIGN KEY (publication_id, scenario) REFERENCES analytics.scenarios
);
CREATE TABLE analytics.documents (
    publication_id text NOT NULL,
    scenario text NOT NULL,
    document_key text NOT NULL,
    delivery_key text NOT NULL,
    source_system text NOT NULL,
    document_id text NOT NULL,
    family_key text NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    evaluation_key text,
    result text NOT NULL CHECK (result IN ('APPROVED','REVIEW_REQUIRED','NOT_EVALUATED')),
    rules_version text,
    received_at timestamptz NOT NULL,
    PRIMARY KEY (publication_id, scenario, document_key),
    UNIQUE (publication_id, scenario, document_key, evaluation_key),
    FOREIGN KEY (publication_id, scenario, delivery_key) REFERENCES analytics.deliveries,
    CHECK ((result = 'NOT_EVALUATED') = (evaluation_key IS NULL))
);
CREATE TABLE analytics.reasons (
    publication_id text NOT NULL,
    scenario text NOT NULL,
    document_key text NOT NULL,
    evaluation_key text NOT NULL,
    code text NOT NULL,
    affected_field text,
    UNIQUE NULLS NOT DISTINCT (publication_id, scenario, evaluation_key, code, affected_field),
    FOREIGN KEY (publication_id, scenario, document_key, evaluation_key)
        REFERENCES analytics.documents (publication_id, scenario, document_key, evaluation_key)
);
CREATE VIEW analytics.consume_publication AS SELECT * FROM analytics.publication;
CREATE VIEW analytics.consume_scenarios AS SELECT * FROM analytics.scenarios;
CREATE VIEW analytics.consume_deliveries AS SELECT * FROM analytics.deliveries;
CREATE VIEW analytics.consume_documents AS SELECT * FROM analytics.documents;
CREATE VIEW analytics.consume_reasons AS SELECT * FROM analytics.reasons;
