from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.sync import update

from app.models.models import User
from app.schemas.user_schema import ChangeUsername


async def get_user_by_email(db: AsyncSession, email: EmailStr):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def create_user(
    db: AsyncSession,
    name: str,
    surname: str,
    email: str,
    password_hash: str,
):
    user = User(
        name=name,
        surname=surname,
        email=email,
        password_hash=password_hash,
    )

    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise

    await db.refresh(user)
    return user


async def change_username_repository(
        db: AsyncSession,
        user: User,
        update_data: dict
):
    for key, value in update_data.items():
        setattr(user, key, value)

    db.add(user)

    await db.flush()

    await db.refresh(user)

    return user