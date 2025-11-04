from typing import List

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.config.dependencies import get_current_user
from app.schemas import project_schema
from app.models.models import User

from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=project_schema.ProjectRead)
def handle_create_project(
        project_to_create: project_schema.CreateProject,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    new_project = project_service.create_project(
        db=db,
        project_data=project_to_create,
        user_id=current_user.id
    )

    return new_project

@router.get("/purposes", response_model=List[project_schema.PurposesRead])
def get_project_purposes(
        db: Session = Depends(get_db),
):
    return project_service.get_project_purposes(db=db)