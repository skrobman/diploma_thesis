import asyncio

import bcrypt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.token_repositories.jwt_token_repository import revoke_refresh_token, revoke_all_user_tokens
from app.repositories.user_repository import get_user_by_id, change_username_repository
from app.schemas.user_schema import ChangeUsername, ProfileRead, ChangePasswordScheme
from app.utils.error_handler import handle_db_errors


@handle_db_errors
async def change_user_username(
        db: AsyncSession,
        user_id: int,
        update_schema: ChangeUsername
):
    initiator = await get_user_by_id(db, user_id)
    if not initiator:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = update_schema.model_dump(exclude_unset=True)

    if update_data.get("name") == initiator.name:
        update_data.pop("name", None)

    if update_data.get("surname") == initiator.surname:
        update_data.pop("surname", None)

    # 4. Если словарь пуст - кидаем ошибку
    if not update_data:
        raise HTTPException(
            status_code=409,
            detail="No changes detected. Name and surname are the same."
        )

    updated_profile = await change_username_repository(db, initiator, update_data)

    await db.commit()

    return updated_profile

@handle_db_errors
async def change_password_service(
        db: AsyncSession,
        user_id: int,
        data: ChangePasswordScheme
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    password_correct = await asyncio.to_thread(
        bcrypt.checkpw,
        data.old_password.encode('utf-8'),
        user.password_hash.encode('utf-8')
    )

    if not password_correct:
        raise HTTPException(status_code=401, detail="Incorrect password")

    if bcrypt.checkpw(data.new_password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the old one")

    user.password_hash = bcrypt.hashpw(data.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    await revoke_all_user_tokens(db, user_id)

    await db.commit()

    return {"message": "Password changed successfully"}