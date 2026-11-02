CREATE TABLE ilc.reference_imports (
    file_key uuid PRIMARY KEY,
    run_id text NOT NULL REFERENCES ilc.runs(run_id),
    source_system text NOT NULL REFERENCES ilc.sources(source_system),
    kind text NOT NULL CHECK (kind IN ('ORDER','DELIVERY')),
    file_name text NOT NULL,
    original_bytes bytea NOT NULL,
    original_sha256 text NOT NULL CHECK (original_sha256 ~ '^[0-9a-f]{64}$'),
    source_jsonl_sha256 text NOT NULL CHECK (source_jsonl_sha256 ~ '^[0-9a-f]{64}$'),
    adapter_version text NOT NULL,
    received_at timestamptz NOT NULL,
    UNIQUE (run_id,kind)
);
CREATE TABLE ilc.reference_results (
    file_key uuid NOT NULL REFERENCES ilc.reference_imports(file_key),
    row_number integer NOT NULL CHECK (row_number > 0),
    outcome text NOT NULL CHECK (outcome IN ('INSERTED','DUPLICATE','CONFLICT','REJECTED')),
    reason text,
    incoming_data jsonb NOT NULL,
    previous_data jsonb,
    entity_key uuid,
    PRIMARY KEY(file_key,row_number)
);
CREATE TABLE ilc.supplement_payloads (
    input_key uuid PRIMARY KEY REFERENCES ilc.inputs(input_key),
    file_name text NOT NULL,
    file_sha256 text NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    line_number integer NOT NULL CHECK (line_number > 0),
    original_bytes bytea NOT NULL
);
CREATE TABLE ilc.event_processing_results (
    attempt_id uuid PRIMARY KEY,
    input_key uuid NOT NULL,
    outcome text NOT NULL CHECK (outcome IN ('ACCEPTED','DUPLICATE','CONFLICT','REJECTED')),
    reason text,
    normalizer_version text NOT NULL,
    normalized_sha256 text,
    normalized_payload jsonb,
    event_key uuid REFERENCES ilc.events(event_key),
    conflict_key uuid REFERENCES ilc.conflicts(conflict_key),
    FOREIGN KEY(attempt_id,input_key) REFERENCES ilc.attempts(attempt_id,input_key),
    CHECK ((normalized_sha256 IS NULL AND normalized_payload IS NULL)
        OR (normalized_sha256 ~ '^[0-9a-f]{64}$' AND normalized_payload IS NOT NULL)),
    CHECK (outcome='ACCEPTED' OR reason IS NOT NULL)
);
CREATE TRIGGER reference_imports_immutable BEFORE UPDATE OR DELETE ON ilc.reference_imports
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER reference_results_immutable BEFORE UPDATE OR DELETE ON ilc.reference_results
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER supplement_payloads_immutable BEFORE UPDATE OR DELETE ON ilc.supplement_payloads
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER event_processing_results_immutable BEFORE UPDATE OR DELETE ON ilc.event_processing_results
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
