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