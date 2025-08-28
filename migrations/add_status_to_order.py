"""Add status column to order table

Revision ID: add_status_to_order
Revises: 
Create Date: 2024-06-02 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_status_to_order'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add status column to order table with default value 'completada'
    op.add_column('order', sa.Column('status', sa.String(20), server_default='completada', nullable=False))

def downgrade():
    # Remove status column if rollback is needed
    op.drop_column('order', 'status')
