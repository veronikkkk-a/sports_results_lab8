"""Add competition date to persisted results."""
from alembic import op
import sqlalchemy as sa
revision = "0002_competition_date"
down_revision = "0001_initial"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.add_column("results", sa.Column("competition_date", sa.Date(), nullable=True))
def downgrade() -> None:
    op.drop_column("results", "competition_date")
