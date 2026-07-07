"""create users table

Revision ID: 001
Revises: 
Create Date: 2026-07-05 19:08:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sqldev

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create table
    op.create_table(
        'users',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('email', sqldev.String(length=255), nullable=False),
        sqldev.Column('password_hash', sqldev.String(length=255), nullable=False),
        sqldev.Column('full_name', sqldev.String(length=100), nullable=False),
        sqldev.Column('role', sqldev.String(length=50), nullable=False, server_default='student'),
        sqldev.Column('profile_picture_url', sqldev.String(length=512), nullable=True),
        sqldev.Column('bio', sqldev.String(length=500), nullable=True),
        sqldev.Column('preferences', sqldev.JSON(), nullable=False, server_default='{}'),
        sqldev.Column('created_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('updated_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('deleted_at', sqldev.DateTime(timezone=True), nullable=True),
        sqldev.PrimaryKeyConstraint('id'),
        sqldev.UniqueConstraint('email')
    )
    
    # 2. Create indices
    op.create_index('idx_user_email', 'users', ['email'], unique=True)
    op.create_index('idx_user_role', 'users', ['role'], unique=False)
    op.create_index('idx_user_deleted_at', 'users', ['deleted_at'], unique=False)

def downgrade() -> None:
    # 1. Drop indices
    op.drop_index('idx_user_deleted_at', table_name='users')
    op.drop_index('idx_user_role', table_name='users')
    op.drop_index('idx_user_email', table_name='users')
    
    # 2. Drop table
    op.drop_table('users')
