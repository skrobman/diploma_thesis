from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User

async def get_user_by_email(db: AsyncSession, email: EmailStr):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def create_user(db: AsyncSession, full_name: str, email: EmailStr, password: str):
    user = User(
        full_name=full_name,
        email=str(email),
        password_hash=password
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user