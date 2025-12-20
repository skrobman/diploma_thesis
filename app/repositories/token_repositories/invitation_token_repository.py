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

async def get_invitation_with_role(db: AsyncSession, token_str: str):
    result = await db.execute(
        select(ProjectInvitationTokens, User, ProjectMember.role_id)
        .join(
            User,
            User.id == ProjectInvitationTokens.user_id
        )
        .join(
            ProjectMember,
            (ProjectMember.user_id == User.id) &
            (ProjectMember.project_id == ProjectInvitationTokens.project_id)
        )
        .where(ProjectInvitationTokens.hashed_token == token_str)
    )

    db_token, user, role_id = result.first()


    return {
        "token": db_token,
        "user": user,
        "role_id": role_id
    }


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