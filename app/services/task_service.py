from datetime import datetime, timezone, timedelta
from typing import List, Dict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Tasks, User, PriorityLevels
from app.repositories.project_repository import get_project_by_id, is_user_member_of_project, get_project_member_by_id, \
    get_project_members_with_roles, get_project_owner

from app.repositories.task_repository import get_task_by_id_repository, is_user_task_member, \
    get_all_user_tasks_from_project_repository, create_task_repository, get_all_priorities, \
    get_all_user_tasks_for_calendar, get_task_member_by_id, is_task_name_exists
from app.repositories.user_repository import get_user_by_id
from app.schemas.task_schema import ReadTask, TaskMemberRead, AllTasksResponse, CreateTask, ReadCreatedTask, \
    CalendarTasksRead, UpdateTask
from app.schemas.user_schema import UserRead
from app.utils.enums.enum_utils import TaskPeriod
from app.utils.error_handler import handle_db_errors


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
        "priority_id": task.priority_id,
        "priority_name": task.priority.name if task.priority else None,
        "task_name": task.name,
        "created_by": task.created_by,
        "creator": task.creator,
        "is_completed": task.is_completed,
        "without_time": task.without_time,
        "weight": task.priority.weight if task.priority else None,
        "description": task.description,
        "start_at": task.start_at,
        "deadline_at": task.deadline_at,
        "members": members
    })

async def get_all_priorities_service(
        db: AsyncSession,
) -> List[PriorityLevels]:
    return list(
        await get_all_priorities(db)
    )

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
        limit: int = 5,
        priority_id: int = None,
        period: TaskPeriod | None = None,
) -> AllTasksResponse:
    tasks = await get_all_user_tasks_from_project_repository(
        db,
        user_id,
        project_id,
        cursor,
        limit,
        priority_id,
        period
    )

    if not tasks:
        return AllTasksResponse(items=[], next_cursor=None)

    tasks_list = [build_read_task(task) for task in tasks]

    next_cursor = tasks_list[-1].id if len(tasks_list) == limit else None

    return AllTasksResponse(
        items=tasks_list,
        next_cursor=next_cursor
    )

@handle_db_errors
async def create_task_service(
    db: AsyncSession,
    task_data: CreateTask,
    user_id: int
):
    project = await get_project_by_id(db=db, project_id=task_data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    initiator = await get_project_member_by_id(
        db=db, user_id=user_id, project_id=project.id
    )
    if not initiator:
        raise HTTPException(status_code=403, detail="You are not a member of this project")
    if initiator.role_id == 3:
        raise HTTPException(status_code=403, detail="No permission")

    final_members_map: Dict[int, int] = {
        user_id: initiator.role_id
    }

    if task_data.users:
        requested_emails = {str(e).lower().strip() for e in task_data.users}

        found_users_map = await get_project_members_with_roles(
            db=db,
            project_id=task_data.project_id,
            emails=list(requested_emails)
        )

        found_emails = set(found_users_map.keys())
        missing_emails = requested_emails - found_emails
        if missing_emails:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot find users in project: {', '.join(missing_emails)}"
            )

        for email in found_emails:
            uid, role_id = found_users_map[email]
            final_members_map[uid] = role_id

    task = await create_task_repository(
        db=db,
        task_data=task_data,
        creator_id=user_id,
        members_with_roles=final_members_map
    )

    creator = await db.get(User, task.created_by)

    return ReadCreatedTask(
        project_id=task.project_id,
        name=task.name,
        description=task.description,
        priority_name=task.priority.name,
        start_at=task.start_at,
        deadline_at=task.deadline_at,
        created_by=UserRead.model_validate(creator),
        without_time=task.without_time,
        is_completed=task.is_completed,
        members=[
            TaskMemberRead(
                role=ut.role.name,
                users=ut.user
            )
            for ut in task.task_users
        ]
    )

async def get_all_calendar_tasks_service(
    db: AsyncSession,
    user_id: int,
    year: int,
    month: int,
):
    current_user = await get_user_by_id(
        db=db,
        user_id=user_id
    )

    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    start_of_month = datetime(year, month, 1, tzinfo=timezone.utc)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

    tasks_from_db = await get_all_user_tasks_for_calendar(
        db=db,
        year=year,
        month=month,
        user_id=user_id
    )

    # Обрабатываем задачи, добавляем is_overdue
    now_utc = datetime.now(timezone.utc)
    calendar_tasks = []
    for task in tasks_from_db:
        task_dict = task.model_dump()
        task_dict["is_overdue"] = task.deadline_at < now_utc and not getattr(task, "is_completed", False)
        calendar_tasks.append(CalendarTasksRead.model_validate(task_dict))

    return calendar_tasks

async def update_task_service(
    db: AsyncSession,
    task_data: UpdateTask,
    task_id: int,
    user_id: int,
):
    current_user = await get_user_by_id(db=db, user_id=user_id)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    task = await get_task_by_id_repository(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    project_member = await get_project_member_by_id(
        db=db,
        project_id=task.project_id,
        user_id=user_id,
    )

    owner = await get_project_owner(
        db=db,
        project_id=task.project_id,
    )

    if not project_member:
        raise HTTPException(status_code=403, detail="Access denied")

    if project_member.role_id == 1:
        pass

    elif task.created_by == user_id:
        pass

    elif project_member.role_id == 2:
        if task.created_by == owner.user_id:
            raise HTTPException(status_code=403, detail="Admins cannot modify owner's tasks")

        task_member = await get_task_member_by_id(
            db=db,
            user_id=user_id,
            task_id=task.id
        )
        if not task_member:
            raise HTTPException(
                status_code=403,
                detail="Admin must be assigned to the task"
            )

    else:
        raise HTTPException(status_code=403, detail="No permission")

    update_data = task_data.model_dump(exclude_unset=True)

    #Проверка на существование таски с таким же именем
    new_name = update_data.get("name")
    if new_name and new_name != task.name:
        exists = await is_task_name_exists(db, task.project_id, new_name, exclude_task_id=task.id)
        if exists:
            raise HTTPException(
                status_code=400,
                detail=f"A task with the name '{new_name}' already exists in this project"
            )

    changed = False

    for field, new_value in update_data.items():
        old_value = getattr(task, field)

        if new_value == old_value:
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field}' must be different from the current value"
            )
        setattr(task, field, new_value)
        changed = True

    if not changed:
        return build_read_task(task)

    await db.commit()

    task = await get_task_by_id_repository(db=db, task_id=task.id)
    return build_read_task(task)
