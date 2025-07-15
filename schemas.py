from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str

class Task(BaseModel):
    id: int
    title: str
    is_completed: bool