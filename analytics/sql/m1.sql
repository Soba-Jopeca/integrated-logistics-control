-- Prática de João: substituir esta consulta por uma agregação de completion_cohort.
-- Colunas: eligible, on_time, missing_promise, contested, rate_pct.
-- Contestar tem precedência sobre falta de prazo; divisão por zero resulta NULL.
WITH counts AS (
    SELECT
        COUNT(*) FILTER (
            WHERE NOT contested AND promised_at IS NOT NULL
        ) AS eligible,
        COUNT(*) FILTER (
            WHERE NOT contested
              AND promised_at IS NOT NULL
              AND completed_at <= promised_at
        ) AS on_time,
        COUNT(*) FILTER (
            WHERE NOT contested AND promised_at IS NULL
        ) AS missing_promise,
        COUNT(*) FILTER (
            WHERE contested
        ) AS contested
    FROM completion_cohort
)
SELECT
    eligible,
    on_time,
    missing_promise,
    contested,
    100.0 * on_time / NULLIF(eligible, 0) AS rate_pct
FROM counts;
