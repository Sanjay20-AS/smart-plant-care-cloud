"""Extend user_id column to accommodate full Supabase JWT tokens.

Revision ID: 002_extend_user_id
Revises: 001_add_user_id
Create Date: 2026-11-26 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_extend_user_id'
down_revision = '001_add_user_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend user_id column from 255 to 2048 characters
    # This is needed to store full Supabase JWT tokens (600+ chars)
    op.alter_column('plants', 'user_id',
               existing_type=sa.String(length=255),
               type_=sa.String(length=2048),
               existing_nullable=True)


def downgrade() -> None:
    # Downgrade back to 255 characters (may lose data if any tokens exceed this)
    op.alter_column('plants', 'user_id',
               existing_type=sa.String(length=2048),
               type_=sa.String(length=255),
               existing_nullable=True)
