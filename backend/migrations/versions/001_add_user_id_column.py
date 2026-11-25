"""Add user_id column to plants table for user data ownership

Revision ID: 001_add_user_id
Revises: 585058cc74e3
Create Date: 2026-11-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_user_id'
down_revision: Union[str, None] = '585058cc74e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id column to plants table (nullable for existing records)
    op.add_column('plants', sa.Column('user_id', sa.String(length=255), nullable=True))
    
    # Create index on user_id for query performance
    op.create_index('idx_plant_user_id', 'plants', ['user_id'], unique=False)


def downgrade() -> None:
    # Remove index
    op.drop_index('idx_plant_user_id', table_name='plants')
    
    # Remove user_id column
    op.drop_column('plants', 'user_id')
