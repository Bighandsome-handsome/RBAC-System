"""add is_shared to resources
Revision ID: f526ae057299
Revises: 06cad9a2aa84
Create Date: 2026-06-04 17:55:46.047869
"""
from alembic import op
import sqlalchemy as sa

revision = 'f526ae057299'
down_revision = '06cad9a2aa84'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_shared', sa.Boolean(), nullable=False, server_default='0'))

def downgrade():
    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.drop_column('is_shared')
