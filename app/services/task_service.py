from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.task_repository import get_task_by_id_repository, is_user_task_member
from app.schemas.task_schema import ReadTask, TaskMemberRead


async def get_task_service(
    db: AsyncSession,
    task_id: int,
    user_id: int
) -> ReadTask:
    task = await get_task_by_id_repository(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not await is_user_task_member(db, task_id, user_id):
        raise HTTPException(status_code=403, detail="You are not a member of this task")

    # Формируем участников
    members = [
        TaskMemberRead.model_validate({
            "users": ut.user,
            "role": ut.role.name if ut.role else None
        })
        for ut in task.task_users
    ]

    # Формируем DTO задачи
    return ReadTask.model_validate({
        "id": task.id,
        "name": task.name,
        "priority_id": task.priority_id,
        "created_by": task.user,
        "description": task.description,
        "start_at": task.start_at,
        "deadline_at": task.deadline_at,
        "members": members
    })