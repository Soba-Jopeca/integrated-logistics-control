"""Completion choices and immutable conflict evidence/resolution chains."""

from pathlib import Path

from alembic import op

revision = "0003_decisions_conflicts"
down_revision = "0002_documents"
branch_labels = None
depends_on = None


def add_completion_event_link():
    """Exige evento DELIVERED pertencente a mesma entrega."""
    op.create_foreign_key(
        "fk_completion_event_delivery",
        "completion_decisions",
        "events",
        ["event_key", "delivery_key", "event_type"],
        ["event_key", "delivery_key", "event_type"],
        source_schema="ilc",
        referent_schema="ilc",
        ondelete="RESTRICT",
    )


def upgrade():
    sql_path = (
        Path(__file__).resolve().parents[1] / "sql" / "0003_decisions_conflicts.sql"
    )
    op.execute(sql_path.read_text(encoding="utf-8"))
    add_completion_event_link()


def downgrade():
    for table in (
        "conflict_resolutions",
        "conflict_evidence",
        "conflicts",
        "completion_decisions",
    ):
        op.drop_table(table, schema="ilc")
    op.execute("DROP FUNCTION ilc.check_conflict_evidence_set()")
    op.execute("DROP FUNCTION ilc.check_conflict_write()")
    op.drop_constraint("uq_events_key_input", "events", schema="ilc", type_="unique")
