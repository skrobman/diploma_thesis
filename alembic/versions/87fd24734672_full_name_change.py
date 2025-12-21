"""full_name change

Revision ID: 87fd24734672
Revises: 174f096f7187
Create Date: 2025-12-21 04:27:32.498824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87fd24734672'
down_revision: Union[str, Sequence[str], None] = '174f096f7187'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "users",
        "full_name",
        existing_type=sa.String(length=100),
        nullable=True,
    )

def downgrade():
    op.alter_column(
        "users",
        "full_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )

