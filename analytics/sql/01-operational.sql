-- Session-local views only, runner rolls back and never writes operational tables.
CREATE TEMP VIEW src_delivery AS
SELECT d.delivery_key, d.delivery_id, d.order_key, o.order_id,
       o.released_at, d.promised_at
FROM ilc.deliveries d JOIN ilc.orders o USING (order_key);

CREATE TEMP VIEW src_completion AS
SELECT c.delivery_key, c.decision_number, c.decided_at, e.occurred_at, e.accepted_at
FROM ilc.completion_decisions c JOIN ilc.events e USING (event_key);

CREATE TEMP VIEW src_conflict AS
SELECT f.delivery_key, f.conflict_type, f.opened_at,
       (SELECT min(r.resolved_at) FROM ilc.conflict_resolutions r
        WHERE r.conflict_key = f.conflict_key) AS resolved_at
FROM ilc.conflicts f;

CREATE TEMP VIEW src_document AS
SELECT d.document_key, d.delivery_key, d.document_id, d.family_key, d.version,
       d.source_system, d.accepted_at, i.received_at, v.valid_from, v.valid_to,
       EXISTS (
           SELECT 1 FROM ilc.inputs j JOIN ilc.attempts a USING (input_key)
           WHERE j.source_system = d.source_system AND j.declared_id = d.document_id
             AND j.input_type = 'DOCUMENT' AND a.error_category = 'IDENTITY_CONFLICT'
             AND a.ended_at <= (SELECT cutoff FROM reference)
       ) OR EXISTS (
           SELECT 1 FROM ilc.conflict_evidence ce JOIN ilc.conflicts f USING (conflict_key)
           WHERE ce.document_key = d.document_key AND ce.recorded_at <= (SELECT cutoff FROM reference)
             AND f.opened_at <= (SELECT cutoff FROM reference)
             AND NOT EXISTS (SELECT 1 FROM ilc.conflict_resolutions cr
                 WHERE cr.conflict_key = f.conflict_key AND cr.resolved_at <= (SELECT cutoff FROM reference))
       ) AS identity_conflict
FROM ilc.document_versions d
JOIN ilc.inputs i USING (input_key)
JOIN ilc.document_validities v USING (document_key);

CREATE TEMP VIEW src_evaluation AS
SELECT e.evaluation_key, e.document_key, e.evaluation_number, e.result,
       e.rules_version, e.evaluated_at, v.valid_from, v.valid_to
FROM ilc.evaluations e JOIN ilc.evaluation_validities v USING (evaluation_key);

CREATE TEMP VIEW src_reason AS
SELECT evaluation_key, code, affected_field FROM ilc.evaluation_reasons;

CREATE TEMP VIEW dim_source AS
SELECT source_system, description FROM ilc.sources;
