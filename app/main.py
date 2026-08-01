from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.api.test import router as test_router
from app.api.recruiter import router as recruiter_router

app = FastAPI(title="Talent Agent AI API", version="1.0.0")

app.include_router(upload_router)
app.include_router(test_router)
app.include_router(recruiter_router)
@app.get("/")
def read_root():
    return {"message": "Welcome to the Talent Agent AI API"}