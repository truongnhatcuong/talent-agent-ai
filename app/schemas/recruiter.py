from pydantic import BaseModel
from typing import Optional


class MatchRequest(BaseModel):
    cv: dict
    jd: str


class MatchCandidateRequest(BaseModel):
    candidate_id: int
    jd: str


class MatchJobRequest(BaseModel):
    candidate_id: int
    job_id: int


class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str