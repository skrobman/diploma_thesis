from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import models
from app.models.models import ProjectMember, Project
from app.schemas.project_schema import AddProjectMember

async def get_project_purpose(db: AsyncSession, purpose_id: int):
    result = await db.execute(
        select(models.ProjectPurposes).where(
            models.ProjectPurposes.id == purpose_id
        )
    )
    return result.scalars().first()

async def get_project_by_id(
        db: AsyncSession,
        project_id: int
):
    project_stmt = select(models.Project).where(
        models.Project.id == project_id
    )

    result = await db.execute(project_stmt)

    return result.scalars().first()

async def check_existing_project(
        db: AsyncSession,
        user_id: int,
        project_name: str
):
    project_stmt = select(models.Project).where(
        models.Project.name == project_name,
        models.Project.created_by == user_id
    )
    project_result = await db.execute(project_stmt)
    return project_result.scalars().first()

async def create_project_repository(db: AsyncSession, project: models.Project) -> models.Project:
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project

async def get_all_project_purposes_repository(db: AsyncSession):
    stmt = select(models.ProjectPurposes)
    result = await db.execute(stmt)

    return result.scalars().all()

async def add_member_to_project(db:AsyncSession, schema: AddProjectMember):
    project_member = ProjectMember(
        project_id=schema.project_id,
        user_id=schema.user_id,
        role_id=schema.role_id
    )

    db.add(project_member)
    await db.flush()

    return project_member