from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import models

from app.schemas.project_schema import CreateProject

async def create_project(
        db: AsyncSession,
        project_data: CreateProject,
        user_id: int
) -> models.Project:
    #Создаем проект
    project_data_dict = project_data.model_dump()

    project_data_name = project_data_dict.get('name')

    project_data_purpose_id = project_data_dict.get('purpose_id')

    stmt = select(models.ProjectPurposes).where(models.ProjectPurposes.id == project_data_purpose_id)
    result = await db.execute(stmt)
    db_purpose = result.scalars().first()

    #db_purpose = db.query(models.ProjectPurposes).filter(models.ProjectPurposes.id == project_data_purpose_id).first()

    if not db_purpose:
        raise HTTPException(
            status_code=404,  # 404 Not Found
            detail=f"Purpose with id {project_data_purpose_id} not found."
        )

    #Проверка на существующий проект(Содержит имя и его создал один и тот же пользователь)
    # existing_project = db.query(models.Project).filter_by(
    #         name=project_data_name,
    #         created_by=user_id
    #     ).first()

    project_stmt = select(models.Project).where(
        models.Project.name == project_data_name,
        models.Project.created_by == user_id
    )
    project_result = await db.execute(project_stmt)
    existing_project = project_result.scalars().first()

    if existing_project:
        raise HTTPException(
            status_code=409,
            detail=f"Project {project_data_name} already exists."
        )

    db_project = models.Project(
        **project_data_dict,
        created_by=user_id
    )

    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    return db_project

async def get_project_purposes(
        db: AsyncSession
) -> List[models.ProjectPurposes]:
    stmt = select(models.ProjectPurposes)
    result = await db.execute(stmt)
    return list(result.scalars().all())
    # return db.query(models.ProjectPurposes).all()