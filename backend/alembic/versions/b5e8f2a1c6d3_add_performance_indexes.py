"""add performance indexes

Revision ID: b5e8f2a1c6d3
Revises: a3f7c9d1e2b4
Create Date: 2026-06-22 00:01:00.000000

Without indexes, every query scans the full table.
With 1,000+ jobs and 10,000+ analyses these become slow.
These indexes cover the columns filtered/sorted most often.
"""
from typing import Sequence, Union
from alembic import op


revision: str = 'b5e8f2a1c6d3'
down_revision: Union[str, Sequence[str], None] = 'a3f7c9d1e2b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # jobs — most common filter columns
    op.create_index("ix_jobs_country",      "jobs", ["country"])
    op.create_index("ix_jobs_is_processed", "jobs", ["is_processed"])
    op.create_index("ix_jobs_scraped_at",   "jobs", ["scraped_at"])

    # job_analyses — all common filter and join columns
    op.create_index("ix_job_analyses_job_id",   "job_analyses", ["job_id"])
    op.create_index("ix_job_analyses_user_id",  "job_analyses", ["user_id"])
    op.create_index("ix_job_analyses_ats_score","job_analyses", ["ats_score"])
    op.create_index("ix_job_analyses_status",   "job_analyses", ["status"])
    op.create_index("ix_job_analyses_dismissed","job_analyses", ["dismissed"])

    # Composite — covers the feed query (filter by user_id, sort by ats_score) in one lookup
    op.create_index("ix_job_analyses_user_score", "job_analyses", ["user_id", "ats_score"])

    # applications — used by the tracker (Phase 3, but table already exists)
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_status",  "applications", ["status"])


def downgrade() -> None:
    op.drop_index("ix_applications_status")
    op.drop_index("ix_applications_user_id")
    op.drop_index("ix_job_analyses_user_score")
    op.drop_index("ix_job_analyses_dismissed")
    op.drop_index("ix_job_analyses_status")
    op.drop_index("ix_job_analyses_ats_score")
    op.drop_index("ix_job_analyses_user_id")
    op.drop_index("ix_job_analyses_job_id")
    op.drop_index("ix_jobs_scraped_at")
    op.drop_index("ix_jobs_is_processed")
    op.drop_index("ix_jobs_country")
