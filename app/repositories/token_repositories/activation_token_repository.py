from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import ActivationToken

async def save_activation_token(db: AsyncSession, token: ActivationToken) -> ActivationToken:
    db.add(token)
    await db.commit()
    await db.refresh(token)

    return token

async def get_activation_token(db: AsyncSession, token_str: str, token_purpose: str) -> ActivationToken | None:
    stmt = select(ActivationToken).where(
        ActivationToken.token == token_str,
        ActivationToken.token_purpose == token_purpose
    )

    result = await db.execute(stmt)

    db_token = result.scalars().first()

    return db_token

async def delete_activation_token(db: AsyncSession, token: ActivationToken) -> ActivationToken | None:
    await db.delete(token)
    await db.commit()