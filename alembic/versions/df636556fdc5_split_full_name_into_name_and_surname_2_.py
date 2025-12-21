"""split full_name into name and surname 2.0

Revision ID: df636556fdc5
Revises: a398d2edb6b4
Create Date: 2025-12-21 03:27:01.872751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select, update
from sqlalchemy import String, text

# revision identifiers, used by Alembic.
revision: str = 'df636556fdc5'
down_revision: Union[str, Sequence[str], None] = 'a398d2edb6b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()

    # 1️⃣ Создаем колонки, только если их нет
    if not conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='users' AND column_name='name'
        """)
    ).fetchone():
        op.add_column('users', sa.Column('name', sa.String(), nullable=True))

    if not conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='users' AND column_name='surname'
        """)
    ).fetchone():
        op.add_column('users', sa.Column('surname', sa.String(), nullable=True))

    # 2️⃣ Обновляем данные из full_name
    conn.execute(text("""
        UPDATE users
        SET name = split_part(full_name, ' ', 1),
            surname = CASE 
                        WHEN full_name LIKE '% %' 
                        THEN substring(full_name from position(' ' in full_name)+1) 
                        ELSE '' 
                      END
    """))

    # 3️⃣ Делаем колонки NOT NULL после обновления
    op.alter_column('users', 'name', nullable=False)
    op.alter_column('users', 'surname', nullable=False)


def downgrade():
    # Опционально откатываем обратно (удаляем колонки name и surname)
    conn = op.get_bind()
    if conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='users' AND column_name='name'
        """)
    ).fetchone():
        op.drop_column('users', 'name')

    if conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='users' AND column_name='surname'
        """)
    ).fetchone():
        op.drop_column('users', 'surname')
