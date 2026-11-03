SELECT count(*) FILTER (WHERE NOT contested AND receipt_hours >= 0) AS eligible,
       count(*) FILTER (WHERE NOT contested AND first_valid_at IS NULL) AS missing_valid,
       count(*) FILTER (WHERE NOT contested AND receipt_hours < 0) AS negative,
       count(*) FILTER (WHERE contested) AS contested,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY receipt_hours)
          FILTER (WHERE NOT contested AND receipt_hours >= 0) AS median_hours
FROM completion_cohort;
