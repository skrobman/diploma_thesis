from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ProjectInvitationTokens, User, ProjectMember


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

async def get_user_invite_token(
        db: AsyncSession,
        user_id: int
):
    result = await db.execute(
        select(ProjectInvitationTokens).where(
            ProjectInvitationTokens.user_id == user_id
        )
    )

    return result.scalars().first()

async def save_invitation_token(
        db: AsyncSession,
        token_model: ProjectInvitationTokens
):
    db.add(token_model)
    await db.flush()
    return token_model


async def delete_invitation_token(
        db: AsyncSession,
        token_value: str  # Принимаем значение токена (строку)
) -> ProjectInvitationTokens | None:
    # Сначала находим токен по его значению
    query = select(ProjectInvitationTokens).where(
        ProjectInvitationTokens.hashed_token == token_value
    )
    result = await db.execute(query)
    token = result.scalar_one_or_none()

    if token:
        await db.delete(token)
        await db.commit()
        return token

    return None

async def delete_invite_token_by_obj(
        db: AsyncSession,
        token_model: ProjectInvitationTokens
) -> ProjectInvitationTokens | None:
    try:
        await db.delete(token_model)
        await db.commit()
        return token_model
    except Exception as e:
        await db.rollback()
        raise e