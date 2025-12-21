"""Fix work_weeks unique constraint for multi-user

Revision ID: 004_fix_unique
Revises: 003_add_users
Create Date: 2025-12-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004_fix_unique'
down_revision = '003_add_users'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old unique index on just week_start (if it exists)
    try:
        op.drop_index('ix_work_weeks_week_start', table_name='work_weeks')
    except:
        pass  # Index might not exist
    
    # Create a new non-unique index on week_start for performance
    try:
        op.create_index('ix_work_weeks_week_start', 'work_weeks', ['week_start'], unique=False)
    except:
        pass  # Index might already exist
    
    # Create unique constraint on user_id + week_start (if it doesn't exist)
    try:
        op.create_unique_constraint('uq_user_week', 'work_weeks', ['user_id', 'week_start'])
    except:
        pass  # Constraint might already exist


def downgrade():
    try:
        op.drop_constraint('uq_user_week', 'work_weeks', type_='unique')
    except:
        pass
    
    try:
        op.drop_index('ix_work_weeks_week_start', table_name='work_weeks')
        op.create_index('ix_work_weeks_week_start', 'work_weeks', ['week_start'], unique=True)
    except:
        pass
