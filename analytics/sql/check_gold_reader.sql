-- Run logged in as the dedicated reader. Catalog visibility is normal.
DO $$
BEGIN
    IF current_user <> 'ilc_gold_reader' OR current_database() <> 'ilc_f2p02b_test'
       OR has_schema_privilege(current_user, 'ilc', 'USAGE')
       OR has_schema_privilege(current_user, 'analytics', 'CREATE')
       OR EXISTS (
           SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
           WHERE n.nspname IN ('analytics','ilc','public') AND c.relkind IN ('r','p','v','m','f')
           AND (has_table_privilege(c.oid,'INSERT,UPDATE,DELETE,TRUNCATE')
                OR (has_table_privilege(c.oid,'SELECT')
                    AND NOT (n.nspname='analytics' AND c.relname IN
                        ('consume_publication','consume_scenarios','consume_deliveries',
                         'consume_documents','consume_reasons'))))
       )
    THEN RAISE EXCEPTION 'Gold reader privilege boundary failed';
    END IF;
END $$;
SELECT 'publication' AS object, count(*) FROM analytics.consume_publication
UNION ALL SELECT 'scenarios', count(*) FROM analytics.consume_scenarios
UNION ALL SELECT 'deliveries', count(*) FROM analytics.consume_deliveries
UNION ALL SELECT 'documents', count(*) FROM analytics.consume_documents
UNION ALL SELECT 'reasons', count(*) FROM analytics.consume_reasons;
