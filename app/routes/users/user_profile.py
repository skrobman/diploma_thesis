from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.config.dependencies import get_current_user
from app.database import get_db
from app.models.models import User
from app.schemas.user_schema import ChangeUsername, ProfileRead, ChangePasswordScheme
from app.services.auth_service import get_user_profile_service
from app.services.profile_service import change_user_username, change_password_service

router = APIRouter(prefix="/user/profile", tags=["Профиль Пользователя"])

@router.get(
    "/me",
    status_code=status.HTTP_200_OK
)
async def get_user_profile(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    user_data = await get_user_profile_service(
        db, current_user.id
    )

    return {
        "name": user_data.name,
        "surname": user_data.surname,
        "email": user_data.email
    }

@router.patch(
    "/{user_id}",
    status_code=status.HTTP_200_OK
)
async def update_user_username(
        update_schema: ChangeUsername,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> ProfileRead:
    return await change_user_username(
        db, current_user.id, update_schema
    )

@router.patch(
    "/{user_id}/change_password",
    status_code=status.HTTP_200_OK
)
async def update_user_password(
        data: ChangePasswordScheme,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return await change_password_service(
        db, current_user.id, data
    )