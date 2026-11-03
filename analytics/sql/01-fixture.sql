-- Times below are UTC. E1 on time, E2 late, E3 missing promise,
-- E4 contested, E5 missing document, E6 has zero receipt interval.
CREATE TEMP VIEW src_delivery AS
SELECT n::text AS delivery_key, 'F5-P02-E' || n AS delivery_id, n AS order_key,
       n AS order_id, '2026-10-15 00:00Z'::timestamptz AS released_at,
       CASE WHEN n <> 3 THEN '2026-10-16 17:00Z'::timestamptz END AS promised_at
FROM generate_series(1, 6) n;

CREATE TEMP VIEW src_completion AS
SELECT delivery_key, 1 AS decision_number,
       '2026-10-16 19:00Z'::timestamptz AS decided_at,
       '2026-10-16 17:00Z'::timestamptz +
           CASE WHEN delivery_key = '2' THEN interval '1 hour' ELSE interval '0' END AS occurred_at,
       '2026-10-16 19:00Z'::timestamptz AS accepted_at
FROM src_delivery;

CREATE TEMP VIEW src_conflict AS
SELECT '4' AS delivery_key, 'COMPLETION_CONFLICT' AS conflict_type,
       '2026-10-16 19:30Z'::timestamptz AS opened_at, NULL::timestamptz AS resolved_at;

CREATE TEMP VIEW src_document AS
SELECT k AS document_key, d AS delivery_key, k AS document_id, f AS family_key,
       n AS version, 'synthetic'::text AS source_system,
       accepted AS accepted_at, received AS received_at, accepted AS valid_from,
       until_at AS valid_to, conflicted AS identity_conflict
FROM (VALUES
 ('A1','1','A',1,'2026-10-16 17:10Z'::timestamptz,'2026-10-16 17:12Z'::timestamptz,'2026-10-16 18:00Z'::timestamptz,false),
 ('A2','1','A',2,'2026-10-16 17:50Z','2026-10-16 18:00Z',NULL,false),
 ('B1','1','B',1,'2026-10-16 17:30Z','2026-10-16 17:31Z',NULL,false),
 ('C1','2','C',1,'2026-10-16 17:59Z','2026-10-16 18:10Z',NULL,false),
 ('D1','3','D',1,'2026-10-16 17:15Z','2026-10-16 17:16Z',NULL,true),
 ('E1','6','E',1,'2026-10-16 17:00Z','2026-10-16 17:01Z',NULL,false),
 ('FUTURE','5','F',1,'2026-10-16 17:00Z','2026-10-18 17:01Z',NULL,false)
) s(k,d,f,n,received,accepted,until_at,conflicted);

CREATE TEMP VIEW src_evaluation AS
SELECT k || '-eval' AS evaluation_key, k AS document_key, 1 AS evaluation_number,
       result, 'synthetic-v1'::text AS rules_version, t AS evaluated_at,
       t AS valid_from, NULL::timestamptz AS valid_to
FROM (VALUES
 ('A1','REVIEW_REQUIRED','2026-10-16 17:20Z'::timestamptz),
 ('A2','APPROVED','2026-10-16 18:01Z'),
 ('B1','REVIEW_REQUIRED','2026-10-16 17:32Z'),
 ('C1','APPROVED','2026-10-16 18:11Z'),
 ('E1','APPROVED','2026-10-16 17:02Z')
) e(k,result,t);

CREATE TEMP VIEW fixture_reasons AS
SELECT 'B1-eval' AS evaluation_key, code, NULL::text AS affected_field FROM (VALUES ('VALUE_MISMATCH'), ('REFERENCE_MISMATCH')) r(code);

CREATE TEMP VIEW src_reason AS SELECT * FROM fixture_reasons;

CREATE TEMP VIEW dim_source AS
SELECT 'synthetic'::text AS source_system, 'Fixture F5-P02'::text AS description;
