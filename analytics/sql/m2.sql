SELECT count(*) AS completed,
       count(*) FILTER (WHERE NOT has_received_document) AS missing_document
FROM fact_delivery_reference WHERE completed_at IS NOT NULL;
