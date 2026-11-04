"""Persistent, versioned analytical fixture publications."""

from pathlib import Path

from alembic import op

revision = "0007_gold_fixture"
down_revision = "0006_reliability"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        (Path(__file__).resolve().parents[1] / "sql/0007_gold_fixture.sql")
        .read_text(encoding="utf-8")
    )


def downgrade():
    for name in ("reasons", "documents", "deliveries", "scenarios", "publication"):
        op.execute(f"DROP VIEW analytics.consume_{name}")
    for name in ("reasons", "documents", "deliveries", "scenarios", "runs", "publication"):
        op.drop_table(name, schema="analytics")
    op.execute("DROP SCHEMA analytics")
