from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config.dependencies import get_current_user
from app.models.models import User
from app.schemas.project_schema import ProjectRead, UpdateProjectArchiveStatus
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["Проекты / Архив"])

@router.patch(
    "/{project_id}/change-archive-status",
    response_model=ProjectRead,
    summary="Изменение статуса архива проекта",
    description="Позволяет архивировать или разархивировать проект. "
                "Доступно только для участников с соответствующими правами.",
    response_description="Информация о проекте после изменения статуса архива"
)
async def update_project_archive_status(
    project_id: int,
    data: UpdateProjectArchiveStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await project_service.update_project_archive_status_service(
        db=db,
        initiator_id=current_user.id,
        project_id=project_id,
        data=data
    )
