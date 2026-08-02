from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    salary: Optional[str] = None
    deadline: Optional[str] = None
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
