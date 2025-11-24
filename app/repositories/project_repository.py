from sqlalchemy import select, func, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import models
from app.models.models import ProjectMember, Project, User
from app.schemas.project_schema import AddProjectMember, UpdateProject


async def is_user_member_of_project(db: AsyncSession, user_id: int, project_id: int) -> bool:
    stmt = select(exists().where(
        models.ProjectMember.user_id == user_id,
        models.ProjectMember.project_id == project_id
    ))
    result = await db.execute(stmt)
    return result.scalar()

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
    ).options(
            # Подгружаем участников и внутри них - пользователей
            selectinload(models.Project.members).selectinload(models.ProjectMember.user)
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

async def get_all_projects(
        db: AsyncSession,
        user_id: int,
        cursor: int
):
    stmt = (
        select(Project)
        .join(
            ProjectMember,
            ProjectMember.project_id == Project.id
        )
        .where(
            Project.id > cursor,
            ProjectMember.user_id == user_id,
        )
        .order_by(Project.id.asc())
        .limit(5)
        .options(
            selectinload(Project.members)
            .selectinload(ProjectMember.user)
        )
    )

    result = await db.execute(stmt)
    return result.scalars().all()

async def get_total_of_projects(
        db: AsyncSession,
        user_id: int,
):
    stmt = (
        select(func.count(Project.id))
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user_id)
    )

    total_projects = (await db.execute(stmt)).scalar_one()
    return total_projects

async def update_project_repository(
        db: AsyncSession,
        project: models.Project,
        update_data: dict
) -> models.Project:
    for key, value in update_data.items():
        setattr(project, key, value)

    db.add(project)

    await db.flush()

    await db.refresh(project)

    return project