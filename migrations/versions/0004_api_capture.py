"""Preserve HTTP response bytes and map capture positions to existing inputs."""

from pathlib import Path

from alembic import op

revision = "0004_api_capture"
down_revision = "0003_decisions_conflicts"
branch_labels = None
depends_on = None


def upgrade():
    path = Path(__file__).resolve().parents[1] / "sql" / "0004_api_capture.sql"
    op.execute(path.read_text(encoding="utf-8"))


def downgrade():
    op.drop_table("capture_items", schema="ilc")
    op.drop_table("capture_pages", schema="ilc")
