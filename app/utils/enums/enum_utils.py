from enum import Enum

class TaskPeriod(str, Enum):
    today = "today"
    week = "week"
    overdue = "overdue"
    completed = "completed"
    upcoming = "upcoming"

class TaskStatus(str, Enum):
    active = False
    completed = True