SELECT count(*) FILTER (WHERE result = 'REVIEW_REQUIRED') AS review_required,
       count(*) FILTER (WHERE result = 'NOT_EVALUATED') AS not_evaluated
FROM fact_document_reference;
