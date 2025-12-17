from sqlalchemy import select, func, exists, delete, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import models
from app.models.models import ProjectMember, Project, User
from app.schemas.project_schema import AddProjectMember, UpdateProject, UpdateProjectMemberRole, \
    UpdateProjectArchiveStatus


async def is_user_member_of_project(db: AsyncSession, user_id: int, project_id: int) -> bool:
    stmt = select(exists().where(
        and_(
            models.ProjectMember.user_id == user_id,
            models.ProjectMember.project_id == project_id
        )
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

async def get_all_project_roles_repository(db: AsyncSession):
    stmt = select(models.Role)
    result = await db.execute(stmt)

    return result.scalars().all()

async def get_all_project_members_repository(
    db: AsyncSession,
    project_id: int
):
    stmt = select(ProjectMember).where(ProjectMember.project_id == project_id)
    result = await db.execute(stmt)

    return result.scalars().all()

async def get_project_member_by_id(
    db: AsyncSession,
    project_id: int,
    user_id: int
):
    stmt = select(models.ProjectMember).where(
        and_(
            models.ProjectMember.user_id == user_id,
            models.ProjectMember.project_id == project_id
        )
    )

    result = await db.execute(stmt)

    return result.scalars().first()

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
        cursor: int,
        limit: int
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
        .limit(limit)
        .options(
            selectinload(Project.members)
            .selectinload(ProjectMember.user),
            selectinload(Project.creator)
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

async def delete_project_repository(
        db: AsyncSession,
        project_id: int
) -> bool :
    stmt = delete(Project).where(Project.id == project_id)

    result = await db.execute(stmt)

    return result.rowcount > 0

async def change_participant_role(
        db: AsyncSession,
        user_to_update_id: int,
        project_id: int,
        data: UpdateProjectMemberRole
):
    stmt = (
        update(ProjectMember)
        .where(
            ProjectMember.user_id == user_to_update_id,
            ProjectMember.project_id == project_id ,
        )
        .values(role_id = data.role_id)
        .returning(ProjectMember)
    )

    result = await db.execute(stmt)
    updated_member = result.scalar_one_or_none()

    await db.commit()

    return updated_member

async def update_project_archive_status(
        db: AsyncSession,
        project_id: int,
        data: UpdateProjectArchiveStatus
):
    stmt = (
        update(Project)
        .where(
            Project.id == project_id,
        )
        .values(
            is_archived = data.is_archived
        )
        .returning(Project)
    )

    result = await db.execute(stmt)
    updated_project = result.scalar_one_or_none()

    await db.commit()

    return updated_project

async def delete_user_from_project_by_id(
    db: AsyncSession,
    project_id: int,
    user_id: int
):
    stmt = (
        delete(ProjectMember)
        .where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id
        )
    )

    result = await db.execute(stmt)

    return result.rowcount > 0