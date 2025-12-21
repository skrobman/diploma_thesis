"""split full_name into name and surname

Revision ID: bfc98a23ac8d
Revises: 2020b22015f5
Create Date: 2025-12-21 03:20:47.971302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision: str = 'bfc98a23ac8d'
down_revision: Union[str, Sequence[str], None] = '2020b22015f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Добавляем новые колонки
    op.add_column('users', sa.Column('name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('surname', sa.String(length=255), nullable=True))

    # Обновляем данные одним SQL-запросом (для PostgreSQL)
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE users
        SET 
            name = split_part(full_name, ' ', 1),
            surname = substring(full_name from position(' ' in full_name) + 1)
    """))

    # Делаем NOT NULL, если нужно
    op.alter_column('users', 'name', nullable=False)
    op.alter_column('users', 'surname', nullable=False)


def downgrade():
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE users
        SET full_name = name || ' ' || surname
    """))

    op.drop_column('users', 'name')
    op.drop_column('users', 'surname')