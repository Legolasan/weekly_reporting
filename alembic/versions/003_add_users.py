"""Add users table and user_id to work_weeks

Revision ID: 003
Revises: 002
Create Date: 2024-12-19

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from passlib.context import CryptContext

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    # Get connection for inspection
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create users table only if it doesn't exist
    if 'users' not in existing_tables:
        op.create_table('users',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('is_admin', sa.Boolean(), nullable=True, default=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create admin user if not exists
    admin_id = uuid.uuid4()
    admin_password_hash = pwd_context.hash("12345")
    op.execute(
        f"""
        INSERT INTO users (id, email, password_hash, is_admin, created_at, updated_at)
        SELECT '{admin_id}', 'arun.sunderraj@hevodata.com', '{admin_password_hash}', true, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'arun.sunderraj@hevodata.com')
        """
    )
    
    # Check if user_id column already exists in work_weeks
    columns = [col['name'] for col in inspector.get_columns('work_weeks')]
    
    if 'user_id' not in columns:
        # Add user_id column to work_weeks (nullable first for existing data)
        op.add_column('work_weeks', sa.Column('user_id', sa.UUID(), nullable=True))
        
        # Get admin user id for updating existing work_weeks
        result = conn.execute(sa.text("SELECT id FROM users WHERE email = 'arun.sunderraj@hevodata.com'"))
        row = result.fetchone()
        if row:
            admin_user_id = row[0]
            # Update existing work_weeks to belong to admin user
            op.execute(f"UPDATE work_weeks SET user_id = '{admin_user_id}' WHERE user_id IS NULL")
        
        # Now make user_id not nullable and add foreign key
        op.alter_column('work_weeks', 'user_id', nullable=False)
        op.create_foreign_key('fk_work_weeks_user_id', 'work_weeks', 'users', ['user_id'], ['id'])
        op.create_index(op.f('ix_work_weeks_user_id'), 'work_weeks', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_work_weeks_user_id'), table_name='work_weeks')
    op.drop_constraint('fk_work_weeks_user_id', 'work_weeks', type_='foreignkey')
    op.drop_column('work_weeks', 'user_id')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
