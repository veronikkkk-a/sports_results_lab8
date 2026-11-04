"""Initial relational schema for sport results."""
from alembic import op
import sqlalchemy as sa
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table("sports", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(length=80), nullable=False), sa.Column("discipline", sa.String(length=80), nullable=False, server_default="general"), sa.UniqueConstraint("name", name="uq_sports_name"))
    op.create_table("athletes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(length=120), nullable=False), sa.Column("category", sa.String(length=80), nullable=False), sa.Column("sport_id", sa.Integer(), nullable=False), sa.ForeignKeyConstraint(["sport_id"], ["sports.id"], ondelete="CASCADE"), sa.UniqueConstraint("sport_id", "name", name="uq_athletes_sport_name"))
    op.create_index("ix_athletes_sport_id", "athletes", ["sport_id"])
    op.create_table("results", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("athlete_id", sa.Integer(), nullable=False), sa.Column("value", sa.Float(), nullable=False), sa.Column("competition_name", sa.String(length=120), nullable=False, server_default="Training"), sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"), sa.CheckConstraint("value >= 0", name="ck_results_value_nonnegative"))
    op.create_index("ix_results_athlete_id", "results", ["athlete_id"])
def downgrade() -> None:
    op.drop_index("ix_results_athlete_id", table_name="results")
    op.drop_table("results")
    op.drop_index("ix_athletes_sport_id", table_name="athletes")
    op.drop_table("athletes")
    op.drop_table("sports")
