from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class JobCreate(BaseModel):
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    salary: Optional[str] = None
    deadline: Optional[str] = None
    description: str


class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    salary: Optional[str] = None
    deadline: Optional[str] = None
    description: Optional[str] = None


class JobResponse(JobCreate):
    id: int
    created_at: datetime

