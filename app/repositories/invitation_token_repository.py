from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ProjectInvitationTokens

async def get_invitation_token(
        db: AsyncSession,
        token_str: str
):
    stmt = select(ProjectInvitationTokens).where(
        ProjectInvitationTokens.hashed_token == token_str
    )

    result = await db.execute(stmt)

    db_token = result.scalars().first()

    return db_token

async def save_invitation_token(
        db: AsyncSession,
        token_model: ProjectInvitationTokens
):
    db.add(token_model)
    await db.flush()
    return token_model

async def delete_invitation_token(db: AsyncSession, token: ProjectInvitationTokens) -> ProjectInvitationTokens | None:
    await db.delete(token)
    await db.commit()