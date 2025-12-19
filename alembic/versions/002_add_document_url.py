"""Add document_url column

Revision ID: 002
Revises: 001
Create Date: 2024-12-19

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('work_items', sa.Column('document_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('work_items', 'document_url')
