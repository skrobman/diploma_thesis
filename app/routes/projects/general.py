from typing import List
from fastapi import APIRouter, status, Query, HTTPException, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config.dependencies import get_current_user
from app.models.models import User
from app.schemas.project_schema import CreateProject, ProjectRead, AllProjectsResponse, PurposesRead, RolesRead
from app.services import project_service
from app.utils.rateLimiters.rate_limiters import PROJECT_CREATE_LIMITER, PROJECT_READ_LIMITER, PROJECT_UPDATE_LIMITER

router = APIRouter(prefix="/projects", tags=["Проекты / Общие"])

@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый проект",
    description="Позволяет создать новый проект. Пользователь, создающий проект, автоматически становится его владельцем. "
                "Защита от частых запросов реализована через rate limiter."
)
async def create_project(
    project_to_create: CreateProject,
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


@router.get(
    "/",
    response_model=AllProjectsResponse,
    summary="Получить список проектов пользователя",
    description="Возвращает список всех проектов, к которым принадлежит текущий пользователь. "
                "Поддерживается пагинация через cursor и limit. "
                "Защита от частых запросов через rate limiter."
)
async def get_projects(
    cursor: int = Query(0, description="ID последнего проекта с предыдущей страницы"),
    limit: int = Query(5, le=10, description="Количество проектов на странице"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not await PROJECT_READ_LIMITER.is_allowed(str(current_user.id)):
        raise HTTPException(status_code=429, detail="Too many requests, try again later")

    return await project_service.get_user_projects(
        db=db,
        user_id=current_user.id,
        cursor=cursor,
        limit=limit
    )


@router.get(
    "/purposes",
    response_model=List[PurposesRead],
    summary="Получить список целей проекта",
    description="Возвращает список всех доступных целей (purpose) для проектов."
)
async def get_project_purposes(db: AsyncSession = Depends(get_db)):
    return await project_service.get_project_purposes(db=db)


@router.get(
    "/roles",
    response_model=List[RolesRead],
    summary="Получить список ролей проекта",
    description="Возвращает список всех доступных ролей (role) для участников проекта."
)
async def get_project_roles(db: AsyncSession = Depends(get_db)):
    return await project_service.get_project_roles(db=db)


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Получить конкретный проект",
    description="Возвращает информацию о конкретном проекте по его ID, если пользователь состоит в проекте. "
                "Защита от частых запросов через rate limiter."
)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not await PROJECT_READ_LIMITER.is_allowed(str(current_user.id)):
        raise HTTPException(status_code=429, detail="Too many requests, try again later")

    return await project_service.get_project_by_id_service(
        db=db,
        project_id=project_id,
        user_id=current_user.id
    )


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Обновить проект",
    description="Позволяет обновить данные проекта (название, описание). "
                "Только участники с соответствующими правами могут изменять проект. "
                "Защита от частых обновлений через rate limiter."
)
async def update_project(
    project_id: int,
    project_data: project_service.UpdateProject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not await PROJECT_UPDATE_LIMITER.is_allowed(str(current_user.id)):
        raise HTTPException(status_code=429, detail="Too many requests, try again later")

    return await project_service.update_project_service(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        update_schema=project_data
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить проект",
    description="Позволяет удалить проект. Только владелец проекта может выполнить эту операцию. "
                "Если проект не найден — возвращается 404, если текущий пользователь не владелец — 403."
)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await project_service.delete_project_service(
        db=db,
        project_id=project_id,
        user_id=current_user.id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
