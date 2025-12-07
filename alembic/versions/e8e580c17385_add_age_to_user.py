"""add_updated_at_to_project_members

Revision ID: e8e580c17385
Revises: ee73da718dd3
Create Date: 2025-12-07 02:10:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'e8e580c17385'
down_revision = 'ee73da718dd3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'project_members',
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(),
            server_default=sa.func.now(),
            nullable=False
        )
    )

def downgrade() -> None:
    op.drop_column('project_members', 'updated_at')
