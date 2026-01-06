from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dependencies import get_current_user
from app.database import get_db
from app.models.models import User
from app.schemas.task_schema import ReadTask, AllTasksResponse, CreateTask, ReadCreatedTask, PrioritiesRead, \
    CalendarTasksRead, UpdateTask, AddUserToTask, RemoveUserFromTask
from app.services.task_service import get_task_service, get_all_user_tasks_in_project_service, create_task_service, \
    get_all_priorities_service, get_all_calendar_tasks_service, update_task_service, delete_task_service, \
    add_user_to_task_service, remove_user_from_task_service
from app.utils.enums.enum_utils import TaskPeriod

router = APIRouter(prefix="/tasks", tags=["Tasks / Общие"])

@router.get(
    "/priorities",
    response_model=List[PrioritiesRead],
    summary="Получить список приоритетов",
    description="Возвращает список всех доступных приоритетов таски."
)
async def get_project_roles(db: AsyncSession = Depends(get_db)):
    return await get_all_priorities_service(db=db)

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
    priority_id: Optional[int] = Query(
        None,
        description="Фильтр по приоритету (необязательный)"
    ),
    filters: TaskPeriod | None = Query(
        None,
        description="Фильтр на today и week"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return await get_all_user_tasks_in_project_service(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
        cursor=cursor,
        limit=limit,
        priority_id=priority_id,
        period=filters
    )

@router.get(
    '/calendar/tasks',
    response_model=List[CalendarTasksRead],
    summary="Получение всех тасок с календаря",
    description="Получение тасок с календаря с использованием фильтрации по году и месяцу"
)
async def get_calendar_tasks(
        year: int = Query(..., ge=2025, le=2100),
        month: int = Query(..., ge=1, le=12),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await get_all_calendar_tasks_service(
        db=db,
        user_id=current_user.id,
        year=year,
        month=month,
    )

@router.patch(
    '/update/{task_id}',
    response_model=ReadTask,
    summary="Изменение таски",
    description="Все поля опциональные"
)
async def update_task(
        task_id: int,
        task_data: UpdateTask,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await update_task_service(
        db=db,
        task_id=task_id,
        task_data=task_data,
        user_id=current_user.id,
    )

@router.delete(
    '/delete/{task_id}',
    status_code=204,
    summary="Удаление таски"
)
async def delete_task(
        task_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await delete_task_service(db=db, task_id=task_id, user_id=current_user.id)

@router.post(
    '/add-user-to-task',
    status_code=201,
    summary='Добавление участника на таску'
)
async def add_user_to_task(
        data: AddUserToTask,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await add_user_to_task_service(
        db=db,
        data=data,
        user_id=current_user.id,
    )

@router.delete(
    '/remove-user-from-task',
    status_code=204,
    summary='Удаление пользователя'
)
async def remove_user_from_task(
        data: RemoveUserFromTask,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await remove_user_from_task_service(
        db=db,
        data=data,
        user_id=current_user.id,
    )