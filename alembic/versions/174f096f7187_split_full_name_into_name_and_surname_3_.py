"""split full_name into name and surname 3.0

Revision ID: 174f096f7187
Revises: df636556fdc5
Create Date: 2025-12-21 03:36:37.565963

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '174f096f7187'
down_revision: Union[str, Sequence[str], None] = 'df636556fdc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    users_table = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('full_name', sa.String),
        sa.column('name', sa.String),
        sa.column('surname', sa.String)
    )

    conn = op.get_bind()
    results = conn.execute(sa.select(users_table.c.id, users_table.c.full_name))
    for row in results:
        full_name = row.full_name or 'doesntExist doesntExist'
        parts = full_name.split(' ', 1)
        first = parts[0] if len(parts) > 0 else 'doesntExist'
        last = parts[1] if len(parts) > 1 else 'doesntExist'
        conn.execute(
            users_table.update()
            .where(users_table.c.id == row.id)
            .values(name=first, surname=last)
        )

def downgrade():
    # Вниз можно ничего не делать, либо очищать name и surname
    pass
