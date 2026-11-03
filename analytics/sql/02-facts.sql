CREATE TEMP VIEW dim_delivery AS
SELECT d.* FROM src_delivery d CROSS JOIN reference r WHERE d.released_at <= r.cutoff;

CREATE TEMP VIEW dim_document AS
SELECT d.document_key, d.document_id, d.family_key, d.version, d.source_system
FROM src_document d CROSS JOIN reference r WHERE d.accepted_at <= r.cutoff;

CREATE TEMP VIEW dim_date AS
SELECT r.period_start + n AS local_date,
       extract(year FROM r.period_start + n)::int AS year,
       extract(month FROM r.period_start + n)::int AS month
FROM reference r CROSS JOIN LATERAL generate_series(0, r.period_end - r.period_start - 1) n;

CREATE TEMP VIEW fact_delivery_reference AS
SELECT r.reference_key, d.delivery_key, d.delivery_id, d.promised_at,
       c.occurred_at AS completed_at,
       (c.occurred_at AT TIME ZONE r.zone)::date AS completed_local_date,
       EXISTS (SELECT 1 FROM src_conflict f
          WHERE f.delivery_key = d.delivery_key AND f.conflict_type <> 'DOCUMENT_IDENTITY'
            AND f.opened_at <= r.cutoff AND (f.resolved_at IS NULL OR f.resolved_at > r.cutoff)
       ) AS contested,
       receipts.received_count > 0 AS has_received_document,
       receipts.first_valid_at,
       extract(epoch FROM (receipts.first_valid_at - c.occurred_at)) / 3600 AS receipt_hours
FROM dim_delivery d CROSS JOIN reference r
LEFT JOIN LATERAL (
    SELECT c.occurred_at FROM src_completion c
    WHERE c.delivery_key = d.delivery_key AND c.decided_at <= r.cutoff
      AND c.accepted_at <= r.cutoff
    ORDER BY c.decision_number DESC LIMIT 1
) c ON c.occurred_at <= r.cutoff
CROSS JOIN LATERAL (
    SELECT count(*) AS received_count,
           min(s.received_at) FILTER (WHERE NOT s.identity_conflict) AS first_valid_at
    FROM src_document s WHERE s.delivery_key = d.delivery_key
      AND s.accepted_at <= r.cutoff AND s.received_at <= r.cutoff
) receipts;

CREATE TEMP VIEW fact_document_reference AS
SELECT r.reference_key, d.document_key, d.delivery_key, d.source_system,
       e.evaluation_key, COALESCE(e.result, 'NOT_EVALUATED') AS result,
       e.rules_version, d.received_at
FROM src_document d CROSS JOIN reference r
LEFT JOIN src_evaluation e ON e.document_key = d.document_key
    AND e.valid_from <= r.cutoff AND (e.valid_to IS NULL OR e.valid_to > r.cutoff)
WHERE d.accepted_at <= r.cutoff AND d.valid_from <= r.cutoff
  AND (d.valid_to IS NULL OR d.valid_to > r.cutoff);

CREATE TEMP VIEW completion_cohort AS
SELECT f.* FROM fact_delivery_reference f JOIN reference r USING (reference_key)
WHERE f.completed_local_date >= r.period_start AND f.completed_local_date < r.period_end;

CREATE TEMP VIEW fact_evaluation_history AS
SELECT DISTINCT e.evaluation_key, e.document_key, e.evaluation_number,
       e.result, e.rules_version, e.evaluated_at
FROM src_evaluation e JOIN dim_document d USING (document_key)
CROSS JOIN reference r WHERE e.evaluated_at <= r.cutoff;

CREATE TEMP VIEW bridge_evaluation_reason AS
SELECT s.* FROM src_reason s JOIN fact_evaluation_history e USING (evaluation_key);

CREATE TEMP VIEW dim_result AS
SELECT result FROM (VALUES ('NOT_EVALUATED'), ('APPROVED'), ('REVIEW_REQUIRED')) x(result);

CREATE TEMP VIEW dim_reason AS
SELECT DISTINCT code FROM bridge_evaluation_reason;

CREATE TEMP VIEW dim_rules AS
SELECT DISTINCT rules_version FROM fact_evaluation_history;
