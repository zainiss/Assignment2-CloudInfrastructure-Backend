from pydantic import BaseModel
from typing import Optional, Literal


class TaskCreate(BaseModel):
    title: str
    description: str
    status: Literal["pending", "done"] = "pending"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["pending", "done"]] = None


class Task(BaseModel):
    taskId: str
    title: str
    description: str
    status: str
    createdAt: str
    attachmentUrl: Optional[str] = None

