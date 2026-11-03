-- Prática de João: substituir esta consulta por uma agregação de completion_cohort.
-- Colunas: eligible, on_time, missing_promise, contested, rate_pct.
-- Contestar tem precedência sobre falta de prazo; divisão por zero resulta NULL.
SELECT NULL::bigint AS eligible, NULL::bigint AS on_time,
       NULL::bigint AS missing_promise, NULL::bigint AS contested,
       NULL::numeric AS rate_pct;
