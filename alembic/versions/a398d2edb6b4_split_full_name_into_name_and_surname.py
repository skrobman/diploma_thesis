"""split full_name into name and surname

Revision ID: a398d2edb6b4
Revises: bfc98a23ac8d
Create Date: 2025-12-21 03:20:49.019228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a398d2edb6b4'
down_revision: Union[str, Sequence[str], None] = 'bfc98a23ac8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
