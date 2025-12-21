import hashlib
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User, RefreshToken

async def find_jwt_token(db: AsyncSession, token: str):
    stmt = select(RefreshToken).where(
        RefreshToken.hashed_token == token,
        RefreshToken.is_revoked == False
    )

    result = await db.execute(stmt)

    db_token = result.scalars().first()

    return db_token

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

async def save_jwt_token(
        db: AsyncSession,
        user: User,
        token: str,
        expires_in_days: int = 7
):
    hashed = hash_token(token)
    expiry_date = datetime.utcnow() + timedelta(days=expires_in_days)

    db_token = RefreshToken(
        hashed_token=hashed,
        user_id=user.id,
        expiry_date=expiry_date,
        is_revoked=False
    )

    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)

async def verify_jwt_token(db: AsyncSession, token: str):
    hashed = hash_token(token)

    db_token = await find_jwt_token(db, hashed)

    if not db_token or db_token.expiry_date < datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

async def revoke_refresh_token(db: AsyncSession, token: str):
    hashed = hash_token(token)

    db_token = await find_jwt_token(db, hashed)

    if db_token:
        db_token.is_revoked = True
        await db.commit()

async def revoke_all_user_tokens(db: AsyncSession, user_id: int):
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id)
        .where(RefreshToken.is_revoked == False)
        .values(is_revoked=True)
    )