"""Add OOO tracking to work_weeks

Revision ID: 005_add_ooo
Revises: 004_fix_unique
Create Date: 2025-12-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '005_add_ooo'
down_revision = '004_fix_unique'
branch_labels = None
depends_on = None


def upgrade():
    # Add ooo_days column
    op.add_column('work_weeks', sa.Column('ooo_days', sa.Integer(), nullable=False, server_default='0'))
    
    # Update total_points based on ooo_days for existing rows
    # total_points = (5 - ooo_days) * 20
    op.execute("""
        UPDATE work_weeks 
        SET total_points = (5 - ooo_days) * 20
        WHERE ooo_days IS NOT NULL
    """)


def downgrade():
    # Revert total_points to 100 for all rows
    op.execute("UPDATE work_weeks SET total_points = 100")
    
    # Drop ooo_days column
    op.drop_column('work_weeks', 'ooo_days')
