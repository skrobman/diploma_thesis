from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dependencies import get_current_user
from app.database import get_db
from app.models.models import User
from app.schemas.task_schema import ReadTask
from app.services.task_service import get_task_service

router = APIRouter(prefix="/tasks", tags=["Tasks / Общие"])

@router.get(
    "/{task_id}",
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
