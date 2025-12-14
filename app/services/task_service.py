from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Tasks
from app.repositories.task_repository import get_task_by_id_repository, is_user_task_member, \
    get_all_user_tasks_from_project_repository
from app.schemas.task_schema import ReadTask, TaskMemberRead, AllTasksResponse


def build_read_task(task: Tasks) -> ReadTask:
    members = [
        TaskMemberRead.model_validate({
            "users": ut.user,
            "role": ut.role.name if ut.role else None
        })
        for ut in task.task_users
    ]

    return ReadTask.model_validate({
        "id": task.id,
        "name": task.name,
        "priority": task.priority_id,
        "created_by": task.user,
        "description": task.description,
        "start_at": task.start_at,
        "deadline_at": task.deadline_at,
        "members": members
    })

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

    return build_read_task(task)

async def get_all_user_tasks_in_project_service(
        db: AsyncSession,
        user_id: int,
        project_id: int,
        cursor: int = 0,
        limit: int = 5
) -> AllTasksResponse:
    tasks = await get_all_user_tasks_from_project_repository(db, user_id, project_id, cursor, limit)

    if not tasks:
        return AllTasksResponse(items=[], next_cursor=None)

    tasks_list = [build_read_task(task) for task in tasks]

    next_cursor = tasks_list[-1].id if len(tasks_list) == limit else None

    return AllTasksResponse(
        items=tasks_list,
        next_cursor=next_cursor
    )