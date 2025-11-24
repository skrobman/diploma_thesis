from typing import List

from fastapi import APIRouter, status, Query
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import current_user

from app.database import get_db
from app.config.dependencies import get_current_user
from app.schemas import project_schema
from app.models.models import User
from app.schemas.project_schema import JoinProjectRequest, AllProjectsResponse, ProjectRead, UpdateProject

from app.services import project_service
from app.services.project_service import join_to_project, get_user_projects, update_project_service

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post(
    "",
    response_model=project_schema.ProjectRead,
    status_code=status.HTTP_201_CREATED
)
async def handle_create_project(
        project_to_create: project_schema.CreateProject,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    new_project = await project_service.create_project(
        db=db,
        project_data=project_to_create,
        user_id=current_user.id
    )

    return new_project

@router.get("/purposes", response_model=List[project_schema.PurposesRead])
async def get_project_purposes(
        db: AsyncSession = Depends(get_db),
):
    return await project_service.get_project_purposes(db=db)

@router.get("/invite/{token}")
async def accept_invite_link(
        token: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return await join_to_project(
        db=db,
        token_str=token,
        current_user=current_user
    )

@router.post("/join")
async def join_project_manual(
    data: JoinProjectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await project_service.join_to_project(
        db=db,
        token_str=data.token,
        current_user=current_user
    )

@router.get("/", response_model=AllProjectsResponse)
async def get_projects(
        cursor: int = Query(0, description="ID последнего проекта с предыдущей страницы"),
        limit: int = Query(5, le=10, description="Количество проектов на странице"),

        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return await get_user_projects(
        db=db,
        user_id=current_user.id,
        cursor=cursor,
        limit=limit
    )

@router.get(
    "/{project_id}",
    response_model=ProjectRead
)
async def get_project(
        project_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return await project_service.get_project_by_id_service(
        db=db,
        project_id=project_id,
        user_id=current_user.id
    )

@router.patch(
    "/{project_id}",
    response_model=project_schema.ProjectRead
)
async def update_project(
    project_id: int,
    project_data: project_schema.UpdateProject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await project_service.update_project_service(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        update_schema=project_data
    )