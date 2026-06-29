"""add status and error_message to job_analyses

Revision ID: a3f7c9d1e2b4
Revises: 60db4ea0fa32
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a3f7c9d1e2b4'
down_revision: Union[str, Sequence[str], None] = '60db4ea0fa32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_analyses', sa.Column('status', sa.String(), nullable=True))
    op.add_column('job_analyses', sa.Column('error_message', sa.Text(), nullable=True))
    # Mark existing rows that already have scores as complete
    op.execute("UPDATE job_analyses SET status = 'complete' WHERE ats_score IS NOT NULL")
    op.execute("UPDATE job_analyses SET status = 'pending'  WHERE status IS NULL")


def downgrade() -> None:
    op.drop_column('job_analyses', 'error_message')
    op.drop_column('job_analyses', 'status')
