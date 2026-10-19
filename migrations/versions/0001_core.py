"""First physical slice: traceability, orders, deliveries and events."""

from pathlib import Path

from alembic import op

revision = "0001_core"
down_revision = None
branch_labels = None
depends_on = None


def add_event_identity_constraint():
    """Garante identidade unica do evento dentro de cada origem."""
    op.create_unique_constraint(
        "uq_events_source_event",
        "events",
        ["source_system", "event_id"],
        schema="ilc",
    )


def upgrade():
    sql_path = Path(__file__).resolve().parents[1] / "sql" / "0001_core.sql"
    op.execute(sql_path.read_text(encoding="utf-8"))
    add_event_identity_constraint()


def downgrade():
    for table in (
        "events",
        "deliveries",
        "orders",
        "attempts",
        "runs",
        "receipts",
        "inputs",
        "sources",
    ):
        op.drop_table(table, schema="ilc")
    op.execute("DROP FUNCTION ilc.reject_history_change()")
    op.execute("DROP SCHEMA ilc")
