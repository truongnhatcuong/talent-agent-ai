from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    email: str
    current_password: str
    new_password: str


class AuthResponse(BaseModel):
    success: bool
    email: str
    full_name: Optional[str] = "HR Admin"
    role: Optional[str] = "admin"
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    message: Optional[str] = None

