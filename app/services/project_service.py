from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import models

from app.schemas.project_schema import CreateProject

def create_project(
        db: Session,
        project_data: CreateProject,
        user_id: int
) -> models.Project:
    #Создаем проект
    project_data_dict = project_data.model_dump()

    project_data_name = project_data_dict.get('name')

    project_data_purpose_id = project_data_dict.get('purpose_id')
    db_purpose = db.query(models.ProjectPurposes).filter(models.ProjectPurposes.id == project_data_purpose_id).first()

    if not db_purpose:
        raise HTTPException(
            status_code=404,  # 404 Not Found или 400 Bad Request
            detail=f"Purpose with id {project_data_purpose_id} not found."
        )

    #Проверка на существующий проект(Содержит имя и его создал один и тот же пользователь)
    existing_project = db.query(models.Project).filter_by(
            name=project_data_name,
            created_by=user_id
        ).first()

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
    db.commit()
    db.refresh(db_project)

    return db_project

def get_project_purposes(
        db: Session
) -> List[models.ProjectPurposes]:
    return db.query(models.ProjectPurposes).all()