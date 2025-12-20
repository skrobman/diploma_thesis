import asyncio
import hashlib
import secrets
import string
from typing import List

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.config.config import settings
from app.redis_client import redis_client
from app.models import models
from app.models.models import ProjectInvitationTokens, User
from app.repositories.token_repositories.invitation_token_repository import save_invitation_token, get_invitation_token, \
    delete_invitation_token
from app.repositories.project_repository import get_project_purpose, check_existing_project, create_project_repository, \
    get_all_project_purposes_repository, add_member_to_project, get_project_by_id, get_total_of_projects, \
    get_all_projects, is_user_member_of_project, update_project_repository, get_all_project_roles_repository, \
    delete_project_repository, get_project_member_by_id, change_participant_role, update_project_archive_status, \
    delete_user_from_project_by_id, get_all_project_members_repository
from app.repositories.user_repository import get_user_by_id, get_user_by_email

from app.schemas.project_schema import CreateProject, AddProjectMember, AllProjectsResponse, ProjectRead, UpdateProject, \
    UpdateProjectMemberRole, UpdateProjectArchiveStatus, ProjectMemberRead
from app.services.mail_service import send_email
from app.utils.error_handler import handle_db_errors


def generate_token(length=6):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

async def invalidate_user_projects_cache(user_id: int):
    """
    Удаляет весь кэш проектов для конкретного пользователя.
    Вызывается при создании, удалении или изменении проектов.
    """
    # Шаблон поиска всех страниц кэша этого юзера
    pattern = f"projects:user:{user_id}:*"

    # Получаем список ключей,
    keys = await redis_client.keys(pattern)

    if keys:
        await redis_client.delete(*keys)

async def invalidate_project_detail_cache(project_id: int):
    await redis_client.delete(f"project_id:{project_id}")

async def get_project(
        db: AsyncSession,
        project_id: int,
        user_id:int,
        msg: str = "Not enough permissions to invite",
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    initiator_member = await get_project_member_by_id(
        db=db,
        user_id=user_id,
        project_id=project_id
    )

    if not initiator_member:
        raise HTTPException(status_code=403, detail="You are not a member of this project")

    if initiator_member.role_id == 3:
        raise HTTPException(status_code=403, detail=msg)

    return project

#TODO Подключить Redis для фоновых задач.
# Переписать отправку email на асинхронные задачи через RQ.
# Запускать воркеры отдельно, чтобы не блокировать FastAPI.
# Перенести генерацию и хэширование токенов в очередь, чтобы ускорить API.
# Настроить Docker-контейнеры для Redis и воркеров.
@handle_db_errors
async def create_project(
        db: AsyncSession,
        project_data: CreateProject,
        user_id: int
) -> models.Project:
    project_data_dict = project_data.model_dump()
    project_data_name = project_data_dict.get('name')
    project_data_purpose_id = project_data_dict.get('purpose_id')
    project_data_users = project_data_dict.pop('users')

    db_purpose = await get_project_purpose(db, project_data_purpose_id)
    if not db_purpose:
        raise HTTPException(status_code=404, detail=f"Purpose not found.")

    existing_project = await check_existing_project(db, user_id, project_data_name)
    if existing_project:
        raise HTTPException(status_code=409, detail=f"Project exists.")

    project_creator = await get_user_by_id(db, user_id)
    if project_creator.email in project_data_users:
        raise HTTPException(status_code=400, detail="Cannot invite yourself.")

    # Находим юзеров и сохраняем их в список
    users_to_invite = []
    for user_email in list(set(project_data_users)):
        existing_user = await get_user_by_email(db, user_email)
        if not existing_user:
            raise HTTPException(status_code=404, detail=f"User {user_email} not found.")
        users_to_invite.append(existing_user)

    try:
        #Создаем проект
        db_project = models.Project(
            **project_data_dict,
            created_by=user_id
        )
        await create_project_repository(db, db_project)

        #Добавляем владельца
        member_schema = AddProjectMember(
            project_id=db_project.id,
            user_id=db_project.created_by,
            role_id=1
        )
        await add_member_to_project(db, member_schema)

        #Создаем приглашения для пользователей
        for user_obj in users_to_invite:
            #Генерируем чистый токен (для письма)
            raw_token = await asyncio.to_thread(generate_token)

            #Хэшируем токен
            hashed_token = await asyncio.to_thread(hash_token, raw_token)

            #Создаем объект модели
            invitation_model = ProjectInvitationTokens(
                hashed_token=hashed_token,
                project_id=db_project.id,
                user_id=user_obj.id
            )

            await save_invitation_token(db, invitation_model)

            #Отправляем письмо
            activation_link = f"{settings.RENDER_LINK}/projects/join/{raw_token}"
            activation_link2 = f"{settings.BASE_LINK}/projects/invite/{raw_token}"

            await send_email(
                to_email=user_obj.email,
                subject=f"{project_creator.full_name} invites you to project",
                text=f"Code: {raw_token}. Link: {activation_link}",
                html=f"<p>Code: <b>{raw_token}</b>. <a href='{activation_link}'>Link</a></p>"
            )

        await db.execute(
            update(models.Project)
            .where(models.Project == db_project.id)
            .values(updated_at=func.now())
        )

        await db.commit()

        await invalidate_user_projects_cache(user_id)

        full_project = await get_project_by_id(db, db_project.id)

        return full_project

    except Exception as e:
        await db.rollback()
        raise e


async def check_invite(
    db: AsyncSession,
    token: str,
):
    hashed_token = hash_token(token)
    invite = await get_invitation_token(db, hashed_token)

    if not invite:
        raise HTTPException(400, "Invalid or expired invite")

    return invite

@handle_db_errors
async def join_to_project(
        db: AsyncSession,
        token_str: str,
        current_user: User
):
    hashed_token = hash_token(token_str)
    token = await get_invitation_token(db, hashed_token)

    if not token:
        raise HTTPException(
            status_code=400,
            detail="Invalid token"
        )

    user = await is_user_member_of_project(
        db=db,
        user_id=current_user.id,
        project_id=token.project_id
    )

    if user:
        raise HTTPException(
            status_code=400,
            detail="You are already a member of this project"
        )

    member_schema = AddProjectMember(
        project_id=token.project_id,
        user_id=current_user.id,
        role_id=3
    )
    await add_member_to_project(db, member_schema)

    await delete_invitation_token(db, token)

    await invalidate_user_projects_cache(current_user.id)

    return {"message": "user joined"}

async def get_project_purposes(
        db: AsyncSession
) -> List[models.ProjectPurposes]:
    return list(
        await get_all_project_purposes_repository(db)
    )

async def get_project_roles(
        db: AsyncSession
) -> List[models.Role]:
    return list(
        await get_all_project_roles_repository(db)
    )

#TODO: cache invalidation func
async def get_user_projects(
        db: AsyncSession,
        user_id: int,
        cursor: int = 0,
        limit: int = 5
) -> AllProjectsResponse:
    # cache_key = f"projects:user:{user_id}:cursor:{cursor}:limit:{limit}"
    #
    # cached_data = await redis_client.get(cache_key)
    # if cached_data:
    #     return AllProjectsResponse.model_validate_json(cached_data)

    # 1. Получаем ORM-объекты
    projects_orm, total_count = await asyncio.gather(
        get_all_projects(db, user_id, cursor, limit),
        get_total_of_projects(db, user_id)
    )

    projects_list = []

    for p in projects_orm:
        members_filtered = [
            m for m in p.members
            if m.user_id != p.created_by
        ]

        project_pd = ProjectRead.model_validate({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "is_archived": p.is_archived,
            "created_at": p.created_at,

            # владелец проекта
            "creator": p.creator,

            # участники без владельца
            "members": [
                ProjectMemberRead.model_validate(m)
                for m in members_filtered
            ]
        })

        projects_list.append(project_pd)

    # 3. Пагинация
    next_cursor = None
    if projects_list:
        last_project = projects_list[-1]
        if len(projects_list) == limit:
            next_cursor = last_project.id

    response = AllProjectsResponse(
        items=projects_list,
        total=total_count,
        next_cursor=next_cursor
    )

    # json_to_cache = response.model_dump_json(
    #     exclude=
    # )
    #
    # # 4. Кэш
    # await redis_client.set(
    #     cache_key,
    #     response.model_dump_json(),
    #     ex=600
    # )

    return response


async def get_project_users_service(
        db: AsyncSession,
        user_id: int,
        project_id: int,
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_member = await get_project_member_by_id(
        db=db,
        user_id=user_id,
        project_id=project.id
    )

    if not project_member:
        raise HTTPException(status_code=403, detail="You are not a member of this project")

    return await get_all_project_members_repository(
        db,
        project_id
    )

async def get_project_member_service(
        db: AsyncSession,
        initiator_id: int,
        project_id: int,
        member_id: int
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    #Проверяем состоит ли пользователь который делал запрос в проекте
    requester_membership = await get_project_member_by_id(
        db=db,
        user_id=initiator_id,
        project_id=project.id
    )

    if not requester_membership:
        raise HTTPException(status_code=403, detail="You are not a member of this project")

    #Получаем конкретного пользователя
    target_member = await get_project_member_by_id(
        db=db,
        user_id=member_id,
        project_id=project.id
    )
    if not target_member:
        raise HTTPException(status_code=404, detail=f"Cannot find user in project")

    return target_member

async def get_project_by_id_service(
        db: AsyncSession,
        project_id: int,
        user_id: int,
) -> ProjectRead:
    is_member = await is_user_member_of_project(db, user_id, project_id)

    if not is_member:
        raise HTTPException(status_code=404, detail="Project not found")

    cache_key = f"project_id:{project_id}"

    cached_data = await redis_client.get(cache_key)

    if cached_data:
        return ProjectRead.model_validate_json(cached_data)

    project = await get_project_by_id(db, project_id)

    project_dto = ProjectRead.model_validate(project)

    json_to_cache = project_dto.model_dump_json(
        exclude={'last_activity'}
    )

    await redis_client.set(
        cache_key,
        json_to_cache,
        ex=600
    )

    return project

async def update_project_service(
        db: AsyncSession,
        project_id: int,
        user_id: int,
        update_schema: UpdateProject
):
    project = await get_project_by_id(db, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.created_by != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if project.is_archived:
        raise HTTPException(status_code=409, detail="Cannot modify an archived project.")

    new_name = update_schema.name
    if new_name and new_name != project.name:
        duplicate = await check_existing_project(db, user_id, new_name)
        if duplicate:
            raise HTTPException(status_code=409, detail="Project name already taken")

    update_data = update_schema.model_dump(exclude_unset=True)

    updated_project = await update_project_repository(db, project, update_data)

    await db.commit()

    await invalidate_user_projects_cache(user_id)

    await invalidate_project_detail_cache(project_id)

    return updated_project

async def delete_project_service(
        db: AsyncSession,
        project_id: int,
        user_id: int
):
    project = await get_project_by_id(db, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.created_by != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    await delete_project_repository(db, project_id)

    await db.commit()

    await invalidate_user_projects_cache(user_id)
    await invalidate_project_detail_cache(project_id)

@handle_db_errors
async def invite_users_to_project_service(
        db: AsyncSession,
        project_id: int,
        user_id: int,
        emails_to_invite: List[EmailStr]
):
    project = await get_project(
        db=db,
        project_id=project_id,
        user_id=user_id
    )

    if project.is_archived:
        raise HTTPException(status_code=409, detail="Cannot invite users to an archived project.")

    initiator_user = await get_user_by_id(db, user_id)

    users_to_invite_objs = []

    for email in list(set(emails_to_invite)):
        if email == initiator_user.email:
            raise HTTPException(status_code=400, detail="Cannot invite yourself")

        user_target = await get_user_by_email(db, email)
        if not user_target:
            raise HTTPException(status_code=404, detail=f"User {email} not registered")

        is_already_member = await is_user_member_of_project(db, user_target.id, project_id)
        if is_already_member:
            raise HTTPException(status_code=409, detail=f"User {email} is already a member")

        users_to_invite_objs.append(user_target)

    try:
        for user_obj in users_to_invite_objs:
            raw_token = await asyncio.to_thread(generate_token)
            hashed_token = await asyncio.to_thread(hash_token, raw_token)

            invitation_model = ProjectInvitationTokens(
                hashed_token=hashed_token,
                project_id=project_id,
                user_id=user_obj.id
            )
            await save_invitation_token(db, invitation_model)

            activation_link = f"{settings.RENDER_LINK}/projects/invite/{raw_token}"

            await send_email(
                to_email=user_obj.email,
                subject=f"{initiator_user.full_name} invites you to '{project.name}'",
                text=f"Join code: {raw_token}",
                html=f"<p>Code: <b>{raw_token}</b>. <a href='{activation_link}'>Join Project</a></p>"
            )

        await db.execute(
            update(models.Project)
            .where(models.Project.id == project.id)
            .values(updated_at=func.now())
        )

        await db.commit()
        return {"message": f"Invites sent to {len(users_to_invite_objs)} users"}

    except Exception as e:
        await db.rollback()
        raise e

@handle_db_errors
async def update_project_member_role_service(
        db: AsyncSession,
        initiator_id: int,
        project_id: int,
        data: UpdateProjectMemberRole
):
    project = await get_project(
        db=db,
        project_id=project_id,
        user_id=initiator_id,
        msg="You dont have permission to update member role."
    )

    if project.is_archived:
        raise HTTPException(status_code=409, detail="Cannot update roles in an archived project.")

    member_user = await get_user_by_email(db, data.user_email)

    project_member = await get_project_member_by_id(
        db = db,
        user_id = member_user.id,
        project_id = project.id
    )
    if not project_member:
        raise HTTPException(status_code=404, detail=f"User {data.user_email} is not a member of this project")

    if data.role_id == project_member.role_id:
        raise HTTPException(status_code=400, detail="Role is already the same")

    if data.role_id == 1:
        raise HTTPException(status_code=400, detail="Cannot assign to owner")

    if data.role_id not in [2, 3]:
        raise HTTPException(status_code=400, detail="Invalid role_id")

    updated_member = await change_participant_role(
        db,
        user_to_update_id=member_user.id,
        project_id=project_id,
        data=data
    )

    return updated_member

@handle_db_errors
async def update_project_archive_status_service(
        db: AsyncSession,
        project_id: int,
        initiator_id: int,
        data: UpdateProjectArchiveStatus
):
    project = await get_project(
        db=db,
        project_id=project_id,
        user_id=initiator_id,
        msg=f"You dont have permission to {'archive' if data.is_archived else 'unarchive'}"
    )

    if project.is_archived == data.is_archived:
        raise HTTPException(
            status_code=400,
            detail=f"Project is already {'archived' if project.is_archived else 'not archived'}"
        )

    archive_status = await update_project_archive_status(
        db = db,
        project_id = project.id,
        data=data
    )

    return archive_status

@handle_db_errors
async def leave_project_service(
        db: AsyncSession,
        project_id: int,
        initiator_id: int
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_member = await get_project_member_by_id(
        db=db,
        user_id=initiator_id,
        project_id=project.id
    )

    if not project_member:
        raise HTTPException(status_code=404, detail=f"You are not a member of this project")

    if project_member.role_id == 1:
        raise HTTPException(
            status_code=400,
            detail="Owner cannot leave the project. Transfer ownership first."
        )

    await delete_user_from_project_by_id(
        db = db,
        user_id=project_member.user_id,
        project_id=project.id
    )

    await db.commit()

@handle_db_errors
async def delete_user_from_project(
        db: AsyncSession,
        initiator_id: int,
        id_of_user_to_delete: int,
        project_id: int,
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_member = await get_project_member_by_id(
        db=db,
        user_id=initiator_id,
        project_id=project.id
    )

    if not project_member:
        raise HTTPException(status_code=404, detail="You are not a member of this project")

    user_to_delete = await get_project_member_by_id(
        db=db,
        user_id=id_of_user_to_delete,
        project_id=project.id
    )

    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found in project.")

    if project_member.role_id == 3:
        raise HTTPException(403, "You don't have permission to delete users.")

    if user_to_delete.role_id == 1 and project_member.role_id != 1:
        raise HTTPException(403, "You cannot delete the owner of the project.")

    await delete_user_from_project_by_id(
        db=db,
        user_id=user_to_delete.user_id,
        project_id=project.id
    )

    await db.commit()