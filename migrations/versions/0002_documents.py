"""Document versions, structural evaluation links and temporal validity."""

from pathlib import Path

from alembic import op

revision = "0002_documents"
down_revision = "0001_core"
branch_labels = None
depends_on = None


def add_evaluation_extraction_link():
    """Exige extracao e avaliacao da mesma versao documental."""
    op.create_foreign_key(
        "fk_evaluations_extraction_document",
        "evaluations",
        "extractions",
        ["extraction_key", "document_key"],
        ["extraction_key", "document_key"],
        source_schema="ilc",
        referent_schema="ilc",
        ondelete="RESTRICT",
    )


def upgrade():
    sql_path = Path(__file__).resolve().parents[1] / "sql" / "0002_documents.sql"
    op.execute(sql_path.read_text(encoding="utf-8"))
    add_evaluation_extraction_link()


def downgrade():
    for table in (
        "evaluation_validities",
        "document_validities",
        "evaluation_reasons",
        "evaluations",
        "extractions",
        "document_versions",
        "document_families",
    ):
        op.drop_table(table, schema="ilc")
    op.execute("""
        DROP FUNCTION ilc.check_document_chain_validity();
        DROP FUNCTION ilc.check_evaluation_reasons();
        DROP FUNCTION ilc.check_evaluation_prerequisites();
        DROP FUNCTION ilc.check_evaluation_validity();
        DROP FUNCTION ilc.close_validity_once();
    """)
    op.drop_constraint(
        "uq_events_key_delivery_type", "events", schema="ilc", type_="unique"
    )
    op.execute("DROP EXTENSION btree_gist")
    op.execute("DROP SCHEMA ilc_gist")
