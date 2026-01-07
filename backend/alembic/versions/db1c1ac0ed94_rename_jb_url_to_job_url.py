"""Rename jb_url to job_url

Revision ID: db1c1ac0ed94
Revises: ed9c373e02d1
Create Date: 2026-01-07 17:39:45.548613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db1c1ac0ed94'
down_revision: Union[str, Sequence[str], None] = 'ed9c373e02d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename the column
    op.alter_column('applications', 'jb_url', new_column_name='job_url')
    # Update indices
    op.drop_index('ix_applications_jb_url', table_name='applications')
    op.create_index(op.f('ix_applications_job_url'), 'applications', ['job_url'], unique=True)


def downgrade() -> None:
    # Rename back
    op.alter_column('applications', 'job_url', new_column_name='jb_url')
    # Update indices back
    op.drop_index('ix_applications_job_url', table_name='applications')
    op.create_index(op.f('ix_applications_jb_url'), 'applications', ['jb_url'], unique=True)
