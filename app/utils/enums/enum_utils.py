from enum import Enum

class TaskPeriod(str, Enum):
    today = "today"
    week = "week"
    overdue = "overdue"

class TaskStatus(str, Enum):
    active = False
    completed = True