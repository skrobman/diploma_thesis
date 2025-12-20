from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config.dependencies import get_current_user
from app.models.models import User
from app.schemas.project_schema import JoinProjectRequest
from app.services.project_service import join_to_project, check_invite

router = APIRouter(prefix="/projects/join", tags=["Проекты / Присоединение"])

@router.get(
    "/{token}",
    summary="Принять приглашение в проект по токену",
)
async def accept_invite_link(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    message_props = await check_invite(db, token)

    return {
        "project_id": message_props.project_id
    }

@router.post(
    "",
    summary="Присоединиться к проекту вручную по токену",
    description=(
        "Позволяет пользователю присоединиться к проекту, отправив токен вручную. "
        "Токен передаётся в теле запроса в формате JSON. "
        "Если токен недействителен, возвращается ошибка 404. "
        "Пользователь должен быть авторизован."
    ),
    response_description="Информация о проекте, к которому присоединился пользователь"
)
async def join_project_manual(
    token: str = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await join_to_project(
            db=db,
            token_str=token,
            current_user=current_user
        )
    except HTTPException as e:
        raise e