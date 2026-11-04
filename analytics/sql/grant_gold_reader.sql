-- Run as analytics owner after the DBA creates a dedicated login with no memberships.
BEGIN;
DO $$
BEGIN
    IF current_database() <> 'ilc_f2p02b_test' THEN
        RAISE EXCEPTION 'Gold reader grants require the test database';
    END IF;
END $$;
GRANT USAGE ON SCHEMA analytics TO ilc_gold_reader;
GRANT SELECT ON analytics.consume_publication, analytics.consume_scenarios,
    analytics.consume_deliveries, analytics.consume_documents, analytics.consume_reasons
    TO ilc_gold_reader;
COMMIT;
