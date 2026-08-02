from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class InterviewCreate(BaseModel):
    candidate_id: Optional[int] = None
    candidate_name: str
    role: Optional[str] = None
    date: str
    time: str
    type: Optional[str] = "Kỹ thuật (Technical)"
    interviewer: Optional[str] = None
    status: Optional[str] = "Chờ phỏng vấn"
    rating: Optional[int] = 0
    notes: Optional[str] = None


class InterviewUpdate(BaseModel):
    candidate_name: Optional[str] = None
    role: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    type: Optional[str] = None
    interviewer: Optional[str] = None
    status: Optional[str] = None
    rating: Optional[int] = None
    notes: Optional[str] = None


class InterviewResponse(InterviewCreate):
    id: int
    created_at: Optional[datetime] = None
