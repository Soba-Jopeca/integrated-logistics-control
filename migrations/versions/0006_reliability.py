"""Atomic capture progress, HTTP attempt audit and recovery lineage."""

from pathlib import Path

from alembic import op

revision = "0006_reliability"
down_revision = "0005_business_processing"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        (Path(__file__).resolve().parents[1] / "sql/0006_reliability.sql").read_text()
    )


def downgrade():
    for name in (
        "reprocessing_links",
        "capture_request_log",
        "capture_checkpoint_history",
        "capture_checkpoints",
    ):
        op.drop_table(name, schema="ilc")
