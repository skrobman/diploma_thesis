from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dependencies import get_current_user
from app.database import get_db
from app.models.models import User
from app.schemas.task_schema import ReadTask, AllTasksResponse, CreateTask, ReadCreatedTask
from app.services.task_service import get_task_service, get_all_user_tasks_in_project_service, create_task_service

router = APIRouter(prefix="/tasks", tags=["Tasks / Общие"])

@router.post(
    "/create",
    response_model=ReadCreatedTask,
    summary="Создать тацку",
    description="Создание таски с использованием опционального времени"
)
async def create_task(
        task_data: CreateTask,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await create_task_service(
        db=db,
        task_data=task_data,
        user_id=current_user.id,
    )

@router.get(
    "/task/{task_id}",
    response_model=ReadTask,
    summary="Получить конкретную тацку",
    description="Возвращает информацию о конкретной тацке по его ID, если пользователь привязан к тацке. "
)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_task_service(
        db=db,
        task_id=task_id,
        user_id=current_user.id
    )

@router.get(
    "/{project_id}",
    response_model=AllTasksResponse,
    summary="Получить список Тацок пользователя",
    description="Возвращает список всех Тацок, к которым принадлежит текущий пользователь на проекте. "
                "Поддерживается пагинация через cursor и limit. "
)
async def get_tasks(
    project_id: int,
    cursor: int = Query(0, description="ID последней таски с предыдущей страницы"),
    limit: int = Query(5, le=10, description="Количество тацок на странице"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return await get_all_user_tasks_in_project_service(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
        cursor=cursor,
        limit=limit
    )

