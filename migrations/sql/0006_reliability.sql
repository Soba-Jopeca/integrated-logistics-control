CREATE TABLE ilc.capture_checkpoints (
    capture_run_id text PRIMARY KEY REFERENCES ilc.runs(run_id),
    source_system text NOT NULL REFERENCES ilc.sources(source_system),
    page_limit integer NOT NULL CHECK (page_limit BETWEEN 1 AND 100),
    last_page integer NOT NULL DEFAULT 0 CHECK (last_page >= 0),
    records integer NOT NULL DEFAULT 0 CHECK (records >= 0),
    dataset_id text,
    api_total integer CHECK (api_total >= 0),
    next_cursor text,
    complete boolean NOT NULL DEFAULT false,
    CHECK (dataset_id IS NULL OR dataset_id ~ '^[0-9a-f]{64}$'),
    CHECK ((last_page=0 AND dataset_id IS NULL AND api_total IS NULL AND records=0 AND NOT complete)
        OR (last_page>0 AND dataset_id IS NOT NULL AND api_total IS NOT NULL)),
    CHECK (NOT complete OR (next_cursor IS NULL AND records=api_total))
);
CREATE TABLE ilc.capture_checkpoint_history (
    capture_run_id text NOT NULL REFERENCES ilc.capture_checkpoints(capture_run_id),
    page_number integer NOT NULL,
    invocation_run_id text NOT NULL REFERENCES ilc.runs(run_id),
    records integer NOT NULL,
    dataset_id text NOT NULL,
    next_cursor text,
    complete boolean NOT NULL,
    recorded_at timestamptz NOT NULL,
    PRIMARY KEY(capture_run_id,page_number)
);
CREATE TABLE ilc.capture_request_log (
    request_key uuid PRIMARY KEY,
    capture_run_id text NOT NULL REFERENCES ilc.capture_checkpoints(capture_run_id),
    invocation_run_id text NOT NULL REFERENCES ilc.runs(run_id),
    page_number integer NOT NULL,
    request_attempt integer NOT NULL CHECK (request_attempt BETWEEN 1 AND 3),
    purpose text NOT NULL CHECK (purpose IN ('PAGE','SNAPSHOT_PROBE')),
    request_url text NOT NULL,
    requested_at timestamptz NOT NULL,
    ended_at timestamptz NOT NULL,
    http_status integer,
    response_body bytea,
    response_sha256 text,
    error_category text,
    CHECK (ended_at>=requested_at),
    CHECK ((response_body IS NULL AND response_sha256 IS NULL) OR
        (response_body IS NOT NULL AND response_sha256 ~ '^[0-9a-f]{64}$'))
);
CREATE TABLE ilc.reprocessing_links (
    new_attempt_id uuid PRIMARY KEY REFERENCES ilc.attempts(attempt_id),
    previous_attempt_id uuid NOT NULL REFERENCES ilc.attempts(attempt_id),
    reason text NOT NULL,
    CHECK (new_attempt_id<>previous_attempt_id)
);
CREATE TRIGGER checkpoint_history_immutable BEFORE UPDATE OR DELETE ON ilc.capture_checkpoint_history
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER request_log_immutable BEFORE UPDATE OR DELETE ON ilc.capture_request_log
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER reprocessing_links_immutable BEFORE UPDATE OR DELETE ON ilc.reprocessing_links
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
