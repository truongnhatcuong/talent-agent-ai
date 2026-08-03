from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.upload import router as upload_router
from app.api.recruiter import router as recruiter_router
from app.api.job import router as job_router
from app.api.interview import router as interview_router
from app.api.auth import router as auth_router
from app.core.database import init_db


from app.models.candidate import Candidate
from app.models.job import Job

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Talent Agent AI API", version="1.0.0", lifespan=lifespan)

# Bật CORS cho phép kết nối từ React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(recruiter_router)
app.include_router(job_router)
app.include_router(interview_router)
app.include_router(auth_router)



@app.get("/")
def read_root():
    return {"message": "Welcome to the Talent Agent AI API"}
