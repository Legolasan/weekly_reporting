"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-12-19

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('work_weeks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('week_end', sa.Date(), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=True, default=100),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_work_weeks_week_start'), 'work_weeks', ['week_start'], unique=True)

    op.create_table('work_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('week_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('assigned_points', sa.Integer(), nullable=False, default=0),
        sa.Column('completion_points', sa.Integer(), nullable=True),
        sa.Column('planned_work', sa.Text(), nullable=True),
        sa.Column('actual_work', sa.Text(), nullable=True),
        sa.Column('next_week_plan', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['week_id'], ['work_weeks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('work_items')
    op.drop_index(op.f('ix_work_weeks_week_start'), table_name='work_weeks')
    op.drop_table('work_weeks')
