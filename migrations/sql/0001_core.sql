CREATE SCHEMA ilc;

CREATE TABLE ilc.sources (
    source_system text PRIMARY KEY,
    description text NOT NULL,
    CONSTRAINT ck_sources_id CHECK (source_system <> '' AND source_system = btrim(source_system)),
    CONSTRAINT ck_sources_description CHECK (btrim(description) <> '')
);

CREATE TABLE ilc.inputs (
    input_key uuid PRIMARY KEY,
    source_system text NOT NULL REFERENCES ilc.sources(source_system) ON DELETE RESTRICT,
    input_type text NOT NULL,
    declared_id text,
    original_reference text NOT NULL,
    original_sha256 text NOT NULL,
    received_at timestamptz NOT NULL,
    normalized_sha256 text,
    normalizer_version text,
    normalization_error text,
    CONSTRAINT uq_inputs_source_type UNIQUE (input_key, source_system, input_type),
    CONSTRAINT ck_inputs_type CHECK (input_type IN ('EVENT', 'DOCUMENT')),
    CONSTRAINT ck_inputs_declared_id CHECK (declared_id IS NULL OR (declared_id <> '' AND declared_id = btrim(declared_id))),
    CONSTRAINT ck_inputs_reference CHECK (btrim(original_reference) <> ''),
    CONSTRAINT ck_inputs_hash CHECK (original_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_inputs_normalization CHECK (
        (normalized_sha256 IS NOT NULL AND normalized_sha256 ~ '^[0-9a-f]{64}$'
            AND normalizer_version IS NOT NULL AND btrim(normalizer_version) <> ''
            AND normalization_error IS NULL)
        OR (normalized_sha256 IS NULL AND normalizer_version IS NULL
            AND normalization_error IS NOT NULL AND btrim(normalization_error) <> '')
    )
);

CREATE TABLE ilc.receipts (
    receipt_key uuid PRIMARY KEY,
    input_key uuid NOT NULL REFERENCES ilc.inputs(input_key) ON DELETE RESTRICT,
    attempt_received_at timestamptz NOT NULL,
    original_reference text NOT NULL,
    original_sha256 text NOT NULL,
    CONSTRAINT uq_receipts_input UNIQUE (receipt_key, input_key),
    CONSTRAINT ck_receipts_reference CHECK (btrim(original_reference) <> ''),
    CONSTRAINT ck_receipts_hash CHECK (original_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE TABLE ilc.runs (
    run_id text PRIMARY KEY,
    stage text NOT NULL,
    started_at timestamptz NOT NULL,
    ended_at timestamptz,
    status text NOT NULL,
    error_category text,
    CONSTRAINT ck_runs_id CHECK (run_id <> '' AND run_id = btrim(run_id)),
    CONSTRAINT ck_runs_stage CHECK (btrim(stage) <> ''),
    CONSTRAINT ck_runs_state CHECK (
        (status = 'RUNNING' AND ended_at IS NULL)
        OR (status IN ('SUCCEEDED', 'FAILED', 'PARTIAL') AND ended_at IS NOT NULL)
    ),
    CONSTRAINT ck_runs_time CHECK (ended_at IS NULL OR ended_at >= started_at),
    CONSTRAINT ck_runs_error CHECK (status <> 'FAILED' OR
        (error_category IS NOT NULL AND btrim(error_category) <> ''))
);

CREATE TABLE ilc.attempts (
    attempt_id uuid PRIMARY KEY,
    input_key uuid NOT NULL REFERENCES ilc.inputs(input_key) ON DELETE RESTRICT,
    run_id text NOT NULL REFERENCES ilc.runs(run_id) ON DELETE RESTRICT,
    receipt_key uuid,
    started_at timestamptz NOT NULL,
    ended_at timestamptz,
    outcome text,
    error_category text,
    CONSTRAINT uq_attempts_input UNIQUE (attempt_id, input_key),
    CONSTRAINT fk_attempts_receipt_input FOREIGN KEY (receipt_key, input_key)
        REFERENCES ilc.receipts(receipt_key, input_key) ON DELETE RESTRICT,
    CONSTRAINT ck_attempts_state CHECK (
        (ended_at IS NULL AND outcome IS NULL)
        OR (ended_at IS NOT NULL AND outcome IS NOT NULL AND outcome IN
            ('ACCEPTED', 'REJECTED', 'DUPLICATE', 'CONFLICT', 'FAILED'))
    ),
    CONSTRAINT ck_attempts_time CHECK (ended_at IS NULL OR ended_at >= started_at),
    CONSTRAINT ck_attempts_error CHECK (outcome <> 'FAILED' OR
        (error_category IS NOT NULL AND btrim(error_category) <> ''))
);

CREATE TABLE ilc.orders (
    order_key uuid PRIMARY KEY,
    source_system text NOT NULL REFERENCES ilc.sources(source_system) ON DELETE RESTRICT,
    order_id text NOT NULL,
    released_at timestamptz NOT NULL,
    request_data jsonb NOT NULL,
    CONSTRAINT uq_orders_source_order UNIQUE (source_system, order_id),
    CONSTRAINT ck_orders_id CHECK (order_id <> '' AND order_id = btrim(order_id)),
    CONSTRAINT ck_orders_request CHECK (jsonb_typeof(request_data) = 'object')
);

CREATE TABLE ilc.deliveries (
    delivery_key uuid PRIMARY KEY,
    order_key uuid NOT NULL REFERENCES ilc.orders(order_key) ON DELETE RESTRICT,
    delivery_id text NOT NULL,
    promised_at timestamptz,
    expected_quantity integer NOT NULL,
    quantity_unit text NOT NULL,
    CONSTRAINT uq_deliveries_order UNIQUE (order_key),
    CONSTRAINT uq_deliveries_id UNIQUE (delivery_id),
    CONSTRAINT ck_deliveries_id CHECK (delivery_id <> '' AND delivery_id = btrim(delivery_id)),
    CONSTRAINT ck_deliveries_quantity CHECK (expected_quantity >= 0),
    CONSTRAINT ck_deliveries_unit CHECK (quantity_unit <> '' AND quantity_unit = btrim(quantity_unit))
);

CREATE TABLE ilc.events (
    event_key uuid PRIMARY KEY,
    source_system text NOT NULL,
    event_id text NOT NULL,
    delivery_key uuid NOT NULL REFERENCES ilc.deliveries(delivery_key) ON DELETE RESTRICT,
    schema_version text NOT NULL,
    event_type text NOT NULL,
    occurred_at timestamptz NOT NULL,
    notes text,
    input_key uuid NOT NULL REFERENCES ilc.inputs(input_key) ON DELETE RESTRICT,
    accepted_attempt_id uuid NOT NULL,
    accepted_at timestamptz NOT NULL,
    acceptance_sequence bigint NOT NULL,
    input_type text NOT NULL DEFAULT 'EVENT',
    CONSTRAINT uq_events_input UNIQUE (input_key),
    CONSTRAINT uq_events_sequence UNIQUE (delivery_key, acceptance_sequence),
    CONSTRAINT fk_events_input_source FOREIGN KEY (input_key, source_system, input_type)
        REFERENCES ilc.inputs(input_key, source_system, input_type) ON DELETE RESTRICT,
    CONSTRAINT fk_events_attempt_input FOREIGN KEY (accepted_attempt_id, input_key)
        REFERENCES ilc.attempts(attempt_id, input_key) ON DELETE RESTRICT,
    CONSTRAINT ck_events_id CHECK (event_id <> '' AND event_id = btrim(event_id)),
    CONSTRAINT ck_events_schema CHECK (schema_version = '1.0'),
    CONSTRAINT ck_events_type CHECK (event_type IN ('DISPATCHED', 'IN_TRANSIT', 'DELIVERED')),
    CONSTRAINT ck_events_input_type CHECK (input_type = 'EVENT'),
    CONSTRAINT ck_events_sequence CHECK (acceptance_sequence > 0)
);

CREATE FUNCTION ilc.reject_history_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Immutable history: %', TG_TABLE_NAME USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER inputs_immutable BEFORE UPDATE OR DELETE ON ilc.inputs
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER receipts_immutable BEFORE UPDATE OR DELETE ON ilc.receipts
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER events_immutable BEFORE UPDATE OR DELETE ON ilc.events
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
