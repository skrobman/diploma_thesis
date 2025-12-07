from typing import List

from fastapi import APIRouter, status, Query, HTTPException, Response
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import current_user

from app.database import get_db
from app.config.dependencies import get_current_user
from app.schemas import project_schema
from app.models.models import User
from app.schemas.project_schema import JoinProjectRequest, AllProjectsResponse, ProjectRead, InviteUserRequest, \
    UpdateProjectMemberRole

from app.services import project_service
from app.services.project_service import join_to_project, get_user_projects, update_project_service, \
    delete_project_service, invite_users_to_project_service, update_project_member_role_service
from app.utils.rateLimiters.rate_limiters import PROJECT_UPDATE_LIMITER, PROJECT_READ_LIMITER, PROJECT_CREATE_LIMITER

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
    if not await PROJECT_CREATE_LIMITER.is_allowed(str(current_user.id)):
        raise HTTPException(status_code=429, detail="Too many requests, try again later")

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

@router.get("/roles", response_model=List[project_schema.RolesRead])
async def get_project_roles(
        db: AsyncSession = Depends(get_db),
):
    return await project_service.get_project_roles(db=db)

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
    # Защита от Ddos
    if not await PROJECT_READ_LIMITER.is_allowed(str(current_user.id)):
        raise HTTPException(status_code=429, detail="Too many requests, try again later")

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
    #Защита от Ddos
    if not await PROJECT_READ_LIMITER.is_allowed(str(current_user.id)):
        raise HTTPException(status_code=429, detail="Too many requests, try again later")

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
    if not await PROJECT_UPDATE_LIMITER.is_allowed(str(current_user.id)):
        raise HTTPException(status_code=429, detail="Too many updates. Chill out.")

    return await update_project_service(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        update_schema=project_data
    )

@router.post(
    "/add-user-to-project/{project_id}",
    summary="Добавление пользователя в проект",
    description="Добавление пользователей в проект. Мы можем пригласить пользователя только в том случае, если у залогиненного юзера роль = 1 или 2",
    status_code=status.HTTP_200_OK
)
async def add_user_to_user_project(
    project_id: int,
    list_of_emails: InviteUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await invite_users_to_project_service(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        emails_to_invite=list_of_emails.emails,
    )

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление проекта",
    responses={
        403: {"description": "Not the owner"},
        404: {"description": "Project not found"},
    }
)
async def delete_project(
        project_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    await delete_project_service(
        db=db,
        project_id=project_id,
        user_id=current_user.id
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch(
    "/{project_id}/change-member-role",
    summary="Поменять статус пользователя в проекте(Повысить или понизить)",
    status_code=status.HTTP_200_OK
)
async def update_project_member_role(
        project_id: int,
        data: UpdateProjectMemberRole,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return await update_project_member_role_service(
        db = db,
        initiator_id=current_user.id,
        project_id=project_id,
        data=data,
    )