-- Additive revision; existing migrations and their objects remain intact.
ALTER TABLE ilc.events ADD CONSTRAINT uq_events_key_input
    UNIQUE (event_key, input_key);

CREATE TABLE ilc.completion_decisions (
    completion_decision_key uuid PRIMARY KEY,
    delivery_key uuid NOT NULL REFERENCES ilc.deliveries(delivery_key) ON DELETE RESTRICT,
    event_key uuid NOT NULL,
    event_type text NOT NULL DEFAULT 'DELIVERED',
    decision_number integer NOT NULL,
    previous_decision_key uuid,
    predecessor_number integer GENERATED ALWAYS AS (decision_number - 1) STORED,
    previous_decided_at timestamptz,
    decided_at timestamptz NOT NULL,
    decision_type text NOT NULL,
    author text NOT NULL,
    reason text NOT NULL,
    CONSTRAINT uq_completion_delivery_number UNIQUE (delivery_key, decision_number),
    CONSTRAINT uq_completion_chain UNIQUE (completion_decision_key, delivery_key, decision_number, decided_at),
    CONSTRAINT uq_completion_key_delivery UNIQUE (completion_decision_key, delivery_key),
    CONSTRAINT uq_completion_successor UNIQUE (previous_decision_key),
    CONSTRAINT fk_completion_previous FOREIGN KEY (previous_decision_key, delivery_key, predecessor_number, previous_decided_at)
        REFERENCES ilc.completion_decisions(completion_decision_key, delivery_key, decision_number, decided_at) ON DELETE RESTRICT,
    CONSTRAINT ck_completion_number CHECK (decision_number >= 1),
    CONSTRAINT ck_completion_previous CHECK (
        (decision_number = 1 AND previous_decision_key IS NULL AND previous_decided_at IS NULL)
        OR (decision_number > 1 AND previous_decision_key IS NOT NULL AND previous_decided_at IS NOT NULL
            AND previous_decided_at <= decided_at)),
    CONSTRAINT ck_completion_time CHECK (isfinite(decided_at)),
    CONSTRAINT ck_completion_event_type CHECK (event_type = 'DELIVERED'),
    CONSTRAINT ck_completion_type CHECK (decision_type IN ('PROVISIONAL', 'MANUAL')),
    CONSTRAINT ck_completion_author CHECK (btrim(author) <> ''),
    CONSTRAINT ck_completion_reason CHECK (btrim(reason) <> '')
);

CREATE TABLE ilc.conflicts (
    conflict_key uuid PRIMARY KEY,
    delivery_key uuid REFERENCES ilc.deliveries(delivery_key) ON DELETE RESTRICT,
    conflict_type text NOT NULL,
    opened_at timestamptz NOT NULL,
    reason text NOT NULL,
    CONSTRAINT ck_conflicts_type CHECK (btrim(conflict_type) <> ''),
    CONSTRAINT ck_conflicts_reason CHECK (btrim(reason) <> ''),
    CONSTRAINT ck_conflicts_time CHECK (isfinite(opened_at))
);

CREATE TABLE ilc.conflict_evidence (
    conflict_evidence_key uuid PRIMARY KEY,
    conflict_key uuid NOT NULL REFERENCES ilc.conflicts(conflict_key) ON DELETE RESTRICT,
    input_key uuid NOT NULL REFERENCES ilc.inputs(input_key) ON DELETE RESTRICT,
    event_key uuid,
    document_key uuid,
    evidence_role text NOT NULL,
    recorded_at timestamptz NOT NULL,
    CONSTRAINT uq_conflict_evidence_input UNIQUE (conflict_key, input_key),
    CONSTRAINT fk_evidence_event_input FOREIGN KEY (event_key, input_key)
        REFERENCES ilc.events(event_key, input_key) ON DELETE RESTRICT,
    CONSTRAINT fk_evidence_document_input FOREIGN KEY (document_key, input_key)
        REFERENCES ilc.document_versions(document_key, input_key) ON DELETE RESTRICT,
    CONSTRAINT ck_evidence_single_object CHECK (event_key IS NULL OR document_key IS NULL),
    CONSTRAINT ck_evidence_role CHECK (evidence_role IN ('ORIGINAL', 'ALTERNATIVE')),
    CONSTRAINT ck_evidence_time CHECK (isfinite(recorded_at))
);

CREATE TABLE ilc.conflict_resolutions (
    resolution_key uuid PRIMARY KEY,
    conflict_key uuid NOT NULL REFERENCES ilc.conflicts(conflict_key) ON DELETE RESTRICT,
    delivery_key uuid REFERENCES ilc.deliveries(delivery_key) ON DELETE RESTRICT,
    completion_decision_key uuid,
    resolution_number integer NOT NULL,
    previous_resolution_key uuid,
    predecessor_number integer GENERATED ALWAYS AS (resolution_number - 1) STORED,
    previous_resolved_at timestamptz,
    resolved_at timestamptz NOT NULL,
    author text NOT NULL,
    reason text NOT NULL,
    decision text NOT NULL,
    CONSTRAINT uq_resolution_conflict_number UNIQUE (conflict_key, resolution_number),
    CONSTRAINT uq_resolution_chain UNIQUE (resolution_key, conflict_key, resolution_number, resolved_at),
    CONSTRAINT uq_resolution_successor UNIQUE (previous_resolution_key),
    CONSTRAINT fk_resolution_previous FOREIGN KEY (previous_resolution_key, conflict_key, predecessor_number, previous_resolved_at)
        REFERENCES ilc.conflict_resolutions(resolution_key, conflict_key, resolution_number, resolved_at) ON DELETE RESTRICT,
    CONSTRAINT fk_resolution_completion_delivery FOREIGN KEY (completion_decision_key, delivery_key)
        REFERENCES ilc.completion_decisions(completion_decision_key, delivery_key) ON DELETE RESTRICT,
    CONSTRAINT ck_resolution_completion_delivery CHECK (completion_decision_key IS NULL OR delivery_key IS NOT NULL),
    CONSTRAINT ck_resolution_number CHECK (resolution_number >= 1),
    CONSTRAINT ck_resolution_previous CHECK (
        (resolution_number = 1 AND previous_resolution_key IS NULL AND previous_resolved_at IS NULL)
        OR (resolution_number > 1 AND previous_resolution_key IS NOT NULL AND previous_resolved_at IS NOT NULL
            AND previous_resolved_at <= resolved_at)),
    CONSTRAINT ck_resolution_time CHECK (isfinite(resolved_at)),
    CONSTRAINT ck_resolution_author CHECK (btrim(author) <> ''),
    CONSTRAINT ck_resolution_reason CHECK (btrim(reason) <> ''),
    CONSTRAINT ck_resolution_decision CHECK (btrim(decision) <> '')
);

CREATE FUNCTION ilc.check_conflict_write() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    parent_delivery uuid;
    parent_opened timestamptz;
    object_delivery uuid;
BEGIN
    -- Serialize changes to the same conflict; do not rewrite its history.
    SELECT delivery_key, opened_at INTO parent_delivery, parent_opened
        FROM ilc.conflicts WHERE conflict_key = NEW.conflict_key FOR UPDATE;
    IF NOT FOUND THEN RETURN NEW; END IF; -- let the named FK reject it
    IF TG_TABLE_NAME = 'conflict_evidence' THEN
        IF EXISTS (SELECT 1 FROM ilc.conflict_resolutions WHERE conflict_key = NEW.conflict_key) THEN
            RAISE EXCEPTION 'Evidence is sealed after first resolution'
                USING ERRCODE = '23514', CONSTRAINT = 'ck_evidence_sealed';
        END IF;
        IF NEW.recorded_at < parent_opened THEN
            RAISE EXCEPTION 'Evidence predates conflict'
                USING ERRCODE = '23514', CONSTRAINT = 'ck_evidence_chronology';
        END IF;
        IF NEW.event_key IS NOT NULL THEN
            SELECT delivery_key INTO object_delivery FROM ilc.events WHERE event_key = NEW.event_key;
        ELSIF NEW.document_key IS NOT NULL THEN
            SELECT delivery_key INTO object_delivery FROM ilc.document_versions WHERE document_key = NEW.document_key;
        END IF;
        IF parent_delivery IS NOT NULL AND object_delivery IS NOT NULL AND parent_delivery <> object_delivery THEN
            RAISE EXCEPTION 'Evidence belongs to another delivery'
                USING ERRCODE = '23514', CONSTRAINT = 'ck_evidence_delivery';
        END IF;
    ELSE
        IF NEW.resolved_at < parent_opened OR EXISTS (
            SELECT 1 FROM ilc.conflict_evidence WHERE conflict_key = NEW.conflict_key AND recorded_at > NEW.resolved_at
        ) OR EXISTS (
            SELECT 1 FROM ilc.completion_decisions WHERE completion_decision_key = NEW.completion_decision_key AND decided_at > NEW.resolved_at
        ) THEN
            RAISE EXCEPTION 'Resolution predates its context'
                USING ERRCODE = '23514', CONSTRAINT = 'ck_resolution_chronology';
        END IF;
        IF (parent_delivery IS NOT NULL AND NEW.delivery_key IS DISTINCT FROM parent_delivery)
            OR EXISTS (
                SELECT 1 FROM ilc.conflict_resolutions r WHERE r.conflict_key = NEW.conflict_key
                    AND r.delivery_key IS NOT NULL AND r.delivery_key IS DISTINCT FROM NEW.delivery_key
            ) OR (NEW.delivery_key IS NOT NULL AND EXISTS (
                SELECT 1 FROM ilc.conflict_evidence x
                LEFT JOIN ilc.events e ON e.event_key = x.event_key
                LEFT JOIN ilc.document_versions d ON d.document_key = x.document_key
                WHERE x.conflict_key = NEW.conflict_key
                    AND coalesce(e.delivery_key, d.delivery_key) IS NOT NULL
                    AND coalesce(e.delivery_key, d.delivery_key) <> NEW.delivery_key
            )) THEN
            RAISE EXCEPTION 'Resolution delivery disagrees with preserved context'
                USING ERRCODE = '23514', CONSTRAINT = 'ck_resolution_delivery';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION ilc.check_conflict_evidence_set() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM ilc.conflict_evidence WHERE conflict_key = NEW.conflict_key AND evidence_role = 'ORIGINAL')
        OR NOT EXISTS (SELECT 1 FROM ilc.conflict_evidence WHERE conflict_key = NEW.conflict_key AND evidence_role = 'ALTERNATIVE') THEN
        RAISE EXCEPTION 'Conflict requires original and alternative evidence'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_conflict_evidence_set';
    END IF;
    RETURN NULL;
END;
$$;

CREATE TRIGGER conflict_evidence_write BEFORE INSERT ON ilc.conflict_evidence
FOR EACH ROW EXECUTE FUNCTION ilc.check_conflict_write();
CREATE TRIGGER conflict_resolution_write BEFORE INSERT ON ilc.conflict_resolutions
FOR EACH ROW EXECUTE FUNCTION ilc.check_conflict_write();
CREATE CONSTRAINT TRIGGER conflicts_evidence_set AFTER INSERT ON ilc.conflicts
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ilc.check_conflict_evidence_set();
CREATE CONSTRAINT TRIGGER evidence_set AFTER INSERT ON ilc.conflict_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ilc.check_conflict_evidence_set();

CREATE TRIGGER completion_decisions_immutable BEFORE UPDATE OR DELETE ON ilc.completion_decisions
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER conflicts_immutable BEFORE UPDATE OR DELETE ON ilc.conflicts
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER conflict_evidence_immutable BEFORE UPDATE OR DELETE ON ilc.conflict_evidence
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER conflict_resolutions_immutable BEFORE UPDATE OR DELETE ON ilc.conflict_resolutions
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
