"""Derived normalization and CSV provenance; raw inputs remain immutable."""

from pathlib import Path

from alembic import op

revision = "0005_business_processing"
down_revision = "0004_api_capture"
branch_labels = None
depends_on = None


def upgrade():
    path = Path(__file__).resolve().parents[1] / "sql" / "0005_business_processing.sql"
    op.execute(path.read_text(encoding="utf-8"))


def downgrade():
    for name in (
        "event_processing_results",
        "supplement_payloads",
        "reference_results",
        "reference_imports",
    ):
        op.drop_table(name, schema="ilc")
