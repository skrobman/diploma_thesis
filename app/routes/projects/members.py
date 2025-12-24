from typing import List
from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config.dependencies import get_current_user
from app.models.models import User
from app.schemas.project_schema import ProjectMemberRead, InviteUserRequest, UpdateProjectMemberRole
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["Проекты / Участники"])

@router.get(
    "/{project_id}/members",
    response_model=List[ProjectMemberRead],
    summary="Получение всех участников проекта",
    description="Возвращает список всех пользователей, которые являются участниками указанного проекта. "
                "Доступно только для участников проекта.",
    response_description="Список участников проекта с их ролями"
)
async def get_project_members(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await project_service.get_project_users_service(
        db=db,
        project_id=project_id,
        user_id=current_user.id
    )


@router.get(
    "/{project_id}/members/{user_id}",
    response_model=ProjectMemberRead,
    summary="Получение конкретного участника проекта",
    description="Возвращает информацию о конкретном пользователе в проекте. "
                "Доступно только для участников проекта.",
    response_description="Данные выбранного участника проекта"
)
async def get_project_member(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await project_service.get_project_member_service(
        db=db,
        project_id=project_id,
        initiator_id=current_user.id,
        member_id=user_id
    )


@router.post(
    "/add-user-to-project/{project_id}",
    status_code=status.HTTP_200_OK,
    summary="Приглашение пользователя в проект",
    description="Позволяет пригласить пользователя в проект по email. "
                "Доступно только для участников с ролью Owner или Admin.",
    response_description="Информация о приглашённых пользователях"
)
async def add_user_to_project(
    project_id: int,
    list_of_emails: InviteUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await project_service.invite_users_to_project_service(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        emails_to_invite=list_of_emails.emails
    )


@router.patch(
    "/{project_id}/change-member-role",
    response_model=ProjectMemberRead,
    summary="Изменение роли участника проекта",
    description="Позволяет повысить или понизить роль участника проекта. "
                "Доступно только для пользователей с соответствующими правами.",
    response_description="Обновлённая информация о роли участника"
)
async def update_project_member_role(
    project_id: int,
    data: UpdateProjectMemberRole,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await project_service.update_project_member_role_service(
        db=db,
        initiator_id=current_user.id,
        project_id=project_id,
        data=data
    )


@router.delete(
    "/{project_id}/leave-project",
    status_code=status.HTTP_200_OK,
    summary="Покинуть проект",
    description="Позволяет текущему пользователю покинуть проект. После выхода пользователь больше не будет участником проекта.",
    response_description="Сообщение о успешном выходе из проекта"
)
async def leave_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await project_service.leave_project_service(
        db=db,
        project_id=project_id,
        initiator_id=current_user.id
    )
    return {"message": "You have left the project."}


@router.delete(
    "/{project_id}/users/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Удаление участника из проекта",
    description="Позволяет удалить пользователя из проекта. "
                "Доступно только для участников с правами Owner или Admin.",
    response_description="Сообщение об успешном удалении пользователя"
)
async def delete_user_from_project(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await project_service.delete_user_from_project(
        db=db,
        current_user=current_user,
        id_of_user_to_delete=user_id,
        project_id=project_id
    )
    return {"message": "User was successfully deleted from the project"}
