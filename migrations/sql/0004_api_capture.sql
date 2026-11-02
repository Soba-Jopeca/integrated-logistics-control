CREATE TABLE ilc.capture_pages (
    page_key uuid PRIMARY KEY,
    run_id text NOT NULL REFERENCES ilc.runs(run_id) ON DELETE RESTRICT,
    page_number integer NOT NULL CHECK (page_number > 0),
    source_system text NOT NULL REFERENCES ilc.sources(source_system) ON DELETE RESTRICT,
    request_url text NOT NULL,
    requested_cursor text,
    received_at timestamptz NOT NULL,
    http_status integer NOT NULL CHECK (http_status BETWEEN 100 AND 599),
    content_type text NOT NULL,
    response_body bytea NOT NULL CHECK (octet_length(response_body) <= 1048576),
    response_sha256 text NOT NULL CHECK (response_sha256 ~ '^[0-9a-f]{64}$'),
    capture_status text NOT NULL CHECK (capture_status IN ('CAPTURED', 'HTTP_ERROR', 'INVALID_RESPONSE')),
    dataset_id text,
    api_total integer CHECK (api_total >= 0),
    next_cursor text,
    item_count integer NOT NULL CHECK (item_count >= 0 AND item_count <= 100),
    CONSTRAINT uq_capture_run_page UNIQUE (run_id, page_number),
    CONSTRAINT ck_capture_failed_empty CHECK (capture_status = 'CAPTURED' OR item_count = 0),
    CONSTRAINT ck_capture_snapshot CHECK (dataset_id IS NULL OR dataset_id ~ '^[0-9a-f]{64}$')
);

CREATE TABLE ilc.capture_items (
    page_key uuid NOT NULL REFERENCES ilc.capture_pages(page_key) ON DELETE RESTRICT,
    item_index integer NOT NULL CHECK (item_index >= 0 AND item_index < 100),
    input_key uuid NOT NULL UNIQUE REFERENCES ilc.inputs(input_key) ON DELETE RESTRICT,
    PRIMARY KEY (page_key, item_index)
);

CREATE TRIGGER capture_pages_immutable BEFORE UPDATE OR DELETE ON ilc.capture_pages
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER capture_items_immutable BEFORE UPDATE OR DELETE ON ilc.capture_items
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
