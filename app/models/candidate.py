from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from typing import Optional, List

class Candidate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = None
    address: Optional[str] = None
    summary: Optional[str] = None
    exp: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Matching AI results
    matched_job: Optional[str] = None
    score: Optional[int] = None
    
    # Save complex structures as JSON
    skills: Optional[list] = Field(default=[], sa_column=Column(JSON))
    experience: Optional[list] = Field(default=[], sa_column=Column(JSON))
    education: Optional[list] = Field(default=[], sa_column=Column(JSON))
    projects: Optional[list] = Field(default=[], sa_column=Column(JSON))
    languages: Optional[list] = Field(default=[], sa_column=Column(JSON))
    certifications: Optional[list] = Field(default=[], sa_column=Column(JSON))
    recommended_jobs: Optional[list] = Field(default=[], sa_column=Column(JSON))
