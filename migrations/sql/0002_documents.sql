-- No IF NOT EXISTS: never adopt and later remove a pre-existing extension.
CREATE SCHEMA ilc_gist;
CREATE EXTENSION btree_gist WITH SCHEMA ilc_gist;

ALTER TABLE ilc.events ADD CONSTRAINT uq_events_key_delivery_type
    UNIQUE (event_key, delivery_key, event_type);

CREATE TABLE ilc.document_families (
    family_key uuid PRIMARY KEY,
    source_system text NOT NULL REFERENCES ilc.sources(source_system) ON DELETE RESTRICT,
    document_family_id text NOT NULL,
    delivery_key uuid NOT NULL REFERENCES ilc.deliveries(delivery_key) ON DELETE RESTRICT,
    CONSTRAINT uq_families_source_id UNIQUE (source_system, document_family_id),
    CONSTRAINT uq_families_source_delivery UNIQUE (family_key, source_system, delivery_key),
    CONSTRAINT ck_families_id CHECK (document_family_id <> '' AND document_family_id = btrim(document_family_id))
);

CREATE TABLE ilc.document_versions (
    document_key uuid PRIMARY KEY,
    family_key uuid NOT NULL,
    source_system text NOT NULL,
    delivery_key uuid NOT NULL,
    document_id text NOT NULL,
    version integer NOT NULL,
    supersedes_document_key uuid,
    predecessor_version integer GENERATED ALWAYS AS (version - 1) STORED,
    schema_version text NOT NULL,
    media_type text NOT NULL,
    file_sha256 text NOT NULL,
    file_reference text NOT NULL,
    file_size_bytes bigint NOT NULL,
    input_key uuid NOT NULL,
    accepted_attempt_id uuid NOT NULL,
    accepted_at timestamptz NOT NULL,
    input_type text NOT NULL DEFAULT 'DOCUMENT',
    CONSTRAINT uq_documents_source_id UNIQUE (source_system, document_id),
    CONSTRAINT uq_documents_family_version UNIQUE (family_key, version),
    CONSTRAINT uq_documents_key_family_version UNIQUE (document_key, family_key, version),
    CONSTRAINT uq_documents_key_family UNIQUE (document_key, family_key),
    CONSTRAINT uq_documents_key_input UNIQUE (document_key, input_key),
    CONSTRAINT uq_documents_key_input_delivery UNIQUE (document_key, input_key, delivery_key),
    CONSTRAINT uq_documents_input UNIQUE (input_key),
    CONSTRAINT uq_documents_successor UNIQUE (supersedes_document_key),
    CONSTRAINT fk_documents_family_source_delivery FOREIGN KEY (family_key, source_system, delivery_key)
        REFERENCES ilc.document_families(family_key, source_system, delivery_key) ON DELETE RESTRICT,
    CONSTRAINT fk_documents_predecessor_family FOREIGN KEY (supersedes_document_key, family_key, predecessor_version)
        REFERENCES ilc.document_versions(document_key, family_key, version) ON DELETE RESTRICT,
    CONSTRAINT fk_documents_input_source FOREIGN KEY (input_key, source_system, input_type)
        REFERENCES ilc.inputs(input_key, source_system, input_type) ON DELETE RESTRICT,
    CONSTRAINT fk_documents_attempt_input FOREIGN KEY (accepted_attempt_id, input_key)
        REFERENCES ilc.attempts(attempt_id, input_key) ON DELETE RESTRICT,
    CONSTRAINT ck_documents_id CHECK (document_id <> '' AND document_id = btrim(document_id)),
    CONSTRAINT ck_documents_version CHECK (version >= 1),
    CONSTRAINT ck_documents_predecessor CHECK (
        (version = 1 AND supersedes_document_key IS NULL)
        OR (version > 1 AND supersedes_document_key IS NOT NULL)
    ),
    CONSTRAINT ck_documents_schema CHECK (schema_version = '1.0'),
    CONSTRAINT ck_documents_media CHECK (media_type IN ('application/pdf', 'application/xml')),
    CONSTRAINT ck_documents_hash CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_documents_reference CHECK (btrim(file_reference) <> ''),
    CONSTRAINT ck_documents_size CHECK (file_size_bytes > 0),
    CONSTRAINT ck_documents_input_type CHECK (input_type = 'DOCUMENT'),
    CONSTRAINT ck_documents_accepted_time CHECK (isfinite(accepted_at))
);

CREATE TABLE ilc.extractions (
    extraction_key uuid PRIMARY KEY,
    document_key uuid NOT NULL,
    input_key uuid NOT NULL,
    attempt_id uuid NOT NULL,
    extractor_version text NOT NULL,
    outcome text NOT NULL,
    extracted_at timestamptz NOT NULL,
    error_category text,
    declared_delivery_id text,
    delivered_at timestamptz,
    received_quantity integer,
    quantity_unit text,
    receiver_name text,
    CONSTRAINT uq_extractions_document UNIQUE (extraction_key, document_key),
    CONSTRAINT fk_extractions_document_input FOREIGN KEY (document_key, input_key)
        REFERENCES ilc.document_versions(document_key, input_key) ON DELETE RESTRICT,
    CONSTRAINT fk_extractions_attempt_input FOREIGN KEY (attempt_id, input_key)
        REFERENCES ilc.attempts(attempt_id, input_key) ON DELETE RESTRICT,
    CONSTRAINT ck_extractions_version CHECK (btrim(extractor_version) <> ''),
    CONSTRAINT ck_extractions_outcome CHECK (outcome IN ('EXTRACTED', 'PARSING_FAILED')),
    CONSTRAINT ck_extractions_error CHECK (outcome <> 'PARSING_FAILED' OR
        (error_category IS NOT NULL AND btrim(error_category) <> ''))
);

CREATE TABLE ilc.evaluations (
    evaluation_key uuid PRIMARY KEY,
    document_key uuid NOT NULL,
    input_key uuid NOT NULL,
    delivery_key uuid NOT NULL,
    attempt_id uuid NOT NULL,
    extraction_key uuid,
    completion_event_key uuid,
    completion_event_type text NOT NULL DEFAULT 'DELIVERED',
    evaluation_number integer NOT NULL,
    previous_evaluation_key uuid,
    previous_evaluation_number integer,
    result text NOT NULL,
    rules_version text NOT NULL,
    evaluated_at timestamptz NOT NULL,
    expected_quantity integer NOT NULL,
    expected_quantity_unit text NOT NULL,
    expected_delivered_at timestamptz,
    is_manual boolean NOT NULL DEFAULT false,
    author text,
    justification text,
    CONSTRAINT uq_evaluations_document_number UNIQUE (document_key, evaluation_number),
    CONSTRAINT uq_evaluations_key_document UNIQUE (evaluation_key, document_key),
    CONSTRAINT uq_evaluations_key_document_number UNIQUE (evaluation_key, document_key, evaluation_number),
    CONSTRAINT fk_evaluations_document_input_delivery FOREIGN KEY (document_key, input_key, delivery_key)
        REFERENCES ilc.document_versions(document_key, input_key, delivery_key) ON DELETE RESTRICT,
    CONSTRAINT fk_evaluations_attempt_input FOREIGN KEY (attempt_id, input_key)
        REFERENCES ilc.attempts(attempt_id, input_key) ON DELETE RESTRICT,
    CONSTRAINT fk_evaluations_completion_delivery FOREIGN KEY (completion_event_key, delivery_key, completion_event_type)
        REFERENCES ilc.events(event_key, delivery_key, event_type) ON DELETE RESTRICT,
    CONSTRAINT fk_evaluations_previous_document FOREIGN KEY (previous_evaluation_key, document_key, previous_evaluation_number)
        REFERENCES ilc.evaluations(evaluation_key, document_key, evaluation_number) ON DELETE RESTRICT,
    CONSTRAINT ck_evaluations_number CHECK (evaluation_number >= 1),
    CONSTRAINT ck_evaluations_previous CHECK (
        (previous_evaluation_key IS NULL AND previous_evaluation_number IS NULL)
        OR (previous_evaluation_key IS NOT NULL AND previous_evaluation_number IS NOT NULL
            AND previous_evaluation_number >= 1 AND previous_evaluation_number < evaluation_number)
    ),
    CONSTRAINT ck_evaluations_result CHECK (result IN ('APPROVED', 'REVIEW_REQUIRED')),
    CONSTRAINT ck_evaluations_prerequisites CHECK (result <> 'APPROVED' OR
        (extraction_key IS NOT NULL AND completion_event_key IS NOT NULL)),
    CONSTRAINT ck_evaluations_event_type CHECK (completion_event_type = 'DELIVERED'),
    CONSTRAINT ck_evaluations_rules CHECK (btrim(rules_version) <> ''),
    CONSTRAINT ck_evaluations_quantity CHECK (expected_quantity >= 0),
    CONSTRAINT ck_evaluations_unit CHECK (btrim(expected_quantity_unit) <> ''),
    CONSTRAINT ck_evaluations_manual CHECK (NOT is_manual OR (
        author IS NOT NULL AND btrim(author) <> '' AND justification IS NOT NULL AND btrim(justification) <> ''))
);

CREATE TABLE ilc.evaluation_reasons (
    reason_key uuid PRIMARY KEY,
    evaluation_key uuid NOT NULL REFERENCES ilc.evaluations(evaluation_key) ON DELETE RESTRICT,
    code text NOT NULL,
    affected_field text,
    detail text,
    CONSTRAINT uq_reasons_code_field UNIQUE NULLS NOT DISTINCT (evaluation_key, code, affected_field),
    CONSTRAINT ck_reasons_code CHECK (code IN ('MISSING_REQUIRED_FIELD', 'INVALID_REFERENCE',
        'REFERENCE_MISMATCH', 'VALUE_MISMATCH', 'PARSING_ERROR', 'DELIVERY_NOT_CONFIRMED', 'IDENTITY_CONFLICT')),
    CONSTRAINT ck_reasons_field CHECK (affected_field IS NULL OR btrim(affected_field) <> '')
);

CREATE TABLE ilc.document_validities (
    document_validity_key uuid PRIMARY KEY,
    family_key uuid NOT NULL,
    document_key uuid NOT NULL,
    valid_from timestamptz NOT NULL,
    valid_to timestamptz,
    CONSTRAINT uq_document_validity_version UNIQUE (document_key),
    CONSTRAINT fk_document_validity_family FOREIGN KEY (document_key, family_key)
        REFERENCES ilc.document_versions(document_key, family_key) ON DELETE RESTRICT,
    CONSTRAINT ck_document_validity_interval CHECK (isfinite(valid_from) AND
        (valid_to IS NULL OR (isfinite(valid_to) AND valid_to > valid_from))),
    CONSTRAINT ex_document_validity_overlap EXCLUDE USING gist (
        family_key ilc_gist.gist_uuid_ops WITH =,
        tstzrange(valid_from, valid_to, '[)') WITH &&
    )
);

CREATE TABLE ilc.evaluation_validities (
    evaluation_validity_key uuid PRIMARY KEY,
    document_key uuid NOT NULL,
    evaluation_key uuid NOT NULL,
    valid_from timestamptz NOT NULL,
    valid_to timestamptz,
    CONSTRAINT fk_evaluation_validity_document FOREIGN KEY (evaluation_key, document_key)
        REFERENCES ilc.evaluations(evaluation_key, document_key) ON DELETE RESTRICT,
    CONSTRAINT ck_evaluation_validity_interval CHECK (isfinite(valid_from) AND
        (valid_to IS NULL OR (isfinite(valid_to) AND valid_to > valid_from))),
    CONSTRAINT ex_evaluation_validity_overlap EXCLUDE USING gist (
        document_key ilc_gist.gist_uuid_ops WITH =,
        tstzrange(valid_from, valid_to, '[)') WITH &&
    )
);

-- This checks the final state of the transaction: every accepted version has
-- one interval starting at acceptance, ending at the successor's acceptance.
CREATE FUNCTION ilc.check_document_chain_validity() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    target_family uuid;
BEGIN
    target_family := NEW.family_key;
    IF NOT EXISTS (SELECT 1 FROM ilc.document_versions WHERE family_key = target_family)
        OR (SELECT count(*) FROM ilc.document_validities WHERE family_key = target_family AND valid_to IS NULL) <> 1
        OR EXISTS (
            SELECT 1 FROM ilc.document_versions d
            LEFT JOIN ilc.document_validities v ON v.document_key = d.document_key
            LEFT JOIN ilc.document_versions s ON s.supersedes_document_key = d.document_key
            WHERE d.family_key = target_family AND (
                v.document_key IS NULL OR v.valid_from <> d.accepted_at
                OR (s.document_key IS NULL AND v.valid_to IS NOT NULL)
                OR (s.document_key IS NOT NULL AND (v.valid_to IS NULL OR v.valid_to <> s.accepted_at))
            )
        ) THEN
        RAISE EXCEPTION 'Inconsistent document chain and validity'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_family_chain_validity';
    END IF;
    RETURN NULL;
END;
$$;

CREATE FUNCTION ilc.check_evaluation_reasons() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    target_evaluation uuid;
    evaluation_result text;
    reason_count bigint;
BEGIN
    target_evaluation := NEW.evaluation_key;
    SELECT result INTO evaluation_result FROM ilc.evaluations WHERE evaluation_key = target_evaluation;
    SELECT count(*) INTO reason_count FROM ilc.evaluation_reasons WHERE evaluation_key = target_evaluation;
    IF (evaluation_result = 'REVIEW_REQUIRED' AND reason_count = 0)
        OR (evaluation_result = 'APPROVED' AND reason_count <> 0) THEN
        RAISE EXCEPTION 'Result and blocker reasons disagree'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_evaluation_reason_set';
    END IF;
    RETURN NULL;
END;
$$;

CREATE FUNCTION ilc.check_evaluation_prerequisites() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    extraction_outcome text;
BEGIN
    IF NEW.result = 'APPROVED' THEN
        SELECT outcome INTO extraction_outcome FROM ilc.extractions WHERE extraction_key = NEW.extraction_key;
        IF extraction_outcome IS DISTINCT FROM 'EXTRACTED' THEN
            RAISE EXCEPTION 'Approval requires a successful extraction'
                USING ERRCODE = '23514', CONSTRAINT = 'ck_evaluation_successful_extraction';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION ilc.check_evaluation_validity() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    produced_at timestamptz;
BEGIN
    SELECT evaluated_at INTO produced_at FROM ilc.evaluations WHERE evaluation_key = NEW.evaluation_key;
    IF produced_at > NEW.valid_from THEN
        RAISE EXCEPTION 'Evaluation selected before production'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_evaluation_validity_production';
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION ilc.close_validity_once() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Validity history cannot be deleted' USING ERRCODE = '23514';
    END IF;
    IF OLD.valid_to IS NOT NULL OR NEW.valid_to IS NULL
        OR (to_jsonb(NEW) - 'valid_to') IS DISTINCT FROM (to_jsonb(OLD) - 'valid_to') THEN
        RAISE EXCEPTION 'Only an open interval may be closed once' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER families_immutable BEFORE UPDATE OR DELETE ON ilc.document_families
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER documents_immutable BEFORE UPDATE OR DELETE ON ilc.document_versions
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER extractions_immutable BEFORE UPDATE OR DELETE ON ilc.extractions
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER evaluations_immutable BEFORE UPDATE OR DELETE ON ilc.evaluations
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER reasons_immutable BEFORE UPDATE OR DELETE ON ilc.evaluation_reasons
FOR EACH ROW EXECUTE FUNCTION ilc.reject_history_change();
CREATE TRIGGER document_validities_close_once BEFORE UPDATE OR DELETE ON ilc.document_validities
FOR EACH ROW EXECUTE FUNCTION ilc.close_validity_once();
CREATE TRIGGER evaluation_validities_close_once BEFORE UPDATE OR DELETE ON ilc.evaluation_validities
FOR EACH ROW EXECUTE FUNCTION ilc.close_validity_once();
CREATE TRIGGER evaluations_prerequisites BEFORE INSERT ON ilc.evaluations
FOR EACH ROW EXECUTE FUNCTION ilc.check_evaluation_prerequisites();
CREATE TRIGGER evaluation_validity_production BEFORE INSERT ON ilc.evaluation_validities
FOR EACH ROW EXECUTE FUNCTION ilc.check_evaluation_validity();

CREATE CONSTRAINT TRIGGER families_complete AFTER INSERT ON ilc.document_families
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ilc.check_document_chain_validity();
CREATE CONSTRAINT TRIGGER documents_complete AFTER INSERT ON ilc.document_versions
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ilc.check_document_chain_validity();
CREATE CONSTRAINT TRIGGER document_validities_complete AFTER INSERT OR UPDATE ON ilc.document_validities
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ilc.check_document_chain_validity();
CREATE CONSTRAINT TRIGGER evaluations_complete AFTER INSERT ON ilc.evaluations
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ilc.check_evaluation_reasons();
CREATE CONSTRAINT TRIGGER reasons_complete AFTER INSERT ON ilc.evaluation_reasons
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ilc.check_evaluation_reasons();
