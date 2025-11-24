import asyncio
import hashlib
import secrets
import string
from typing import List

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.redis_client import redis_client
from app.models import models
from app.models.models import ProjectInvitationTokens, User
from app.repositories.invitation_token_repository import save_invitation_token, get_invitation_token, \
    delete_invitation_token
from app.repositories.project_repository import get_project_purpose, check_existing_project, create_project_repository, \
    get_all_project_purposes_repository, add_member_to_project, get_project_by_id, get_total_of_projects, \
    get_all_projects, is_user_member_of_project
from app.repositories.user_repository import get_user_by_id, get_user_by_email

from app.schemas.project_schema import CreateProject, AddProjectMember, AllProjectsResponse, ProjectRead
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
            activation_link = f"http://localhost:8000/projects/invite/{raw_token}"

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

    #project = await get_project_by_id(db, token.project_id)

    user = await get_user_by_id(db, token.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="This invitation is not intended for your account."
        )

    member_schema = AddProjectMember(
        project_id=token.project_id,
        user_id=user.id,
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

async def get_user_projects(
        db: AsyncSession,
        user_id: int,
        cursor: int = 0,
        limit: int = 5
) -> AllProjectsResponse:
    cache_key = f"projects:user:{user_id}:cursor:{cursor}:limit:{limit}"

    cached_data = await redis_client.get(cache_key)

    if cached_data:
        return AllProjectsResponse.model_validate_json(cached_data)

    projects_list, total_count = await asyncio.gather(
        get_all_projects(db, user_id, cursor),
        get_total_of_projects(db, user_id)
    )

    next_cursor = None

    if projects_list:
        last_project = projects_list[-1]
        next_cursor = last_project.id

        if len(projects_list) < limit:
            next_cursor = None


    response = AllProjectsResponse(
        items=projects_list,
        total=total_count,
        next_cursor=next_cursor
    )

    json_to_cache = response.model_dump_json(
        exclude={
            'items': {'__all__': {'last_activity'}}
        }
    )

    await redis_client.set(
        cache_key,
        json_to_cache,
        ex=600
    )

    return response

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
        exclude={
            'items': {'__all__': {'last_activity'}}
        }
    )

    await redis_client.set(
        cache_key,
        json_to_cache,
        ex=600
    )

    return project