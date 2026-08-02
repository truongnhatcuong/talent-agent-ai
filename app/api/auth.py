from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, status
from supabase import Client
from postgrest.exceptions import APIError

from app.core.database import get_supabase
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.schemas.auth import LoginRequest, ChangePasswordRequest, AuthResponse

router = APIRouter(
    prefix="/auth",
    tags=["Auth & HR Account"]
)


@router.post("/login", response_model=AuthResponse)
async def login_hr(payload: LoginRequest, supabase: Client = Depends(get_supabase)):
    """
    Đăng nhập tài khoản HR nội bộ qua CSDL Supabase & Tạo mã JWT Token.
    """
    try:
        res = supabase.table("user_account").select("*").eq("email", payload.email).execute()
        
        if not res.data:
            # Check default admin if not in DB yet
            if payload.email == "admin@talentagent.ai" and payload.password == "password123":
                token = create_access_token({"sub": payload.email, "role": "admin"})
                return AuthResponse(
                    success=True,
                    email=payload.email,
                    full_name="HR Admin",
                    role="admin",
                    access_token=token,
                    token_type="bearer",
                    message="Đăng nhập thành công và khởi tạo JWT Token!"
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không chính xác!"
            )

        user = res.data[0]
        stored_password = user.get("password", "")

        # Verify password with PBKDF2 salt check
        if not verify_password(payload.password, stored_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mật khẩu không chính xác!"
            )

        # Generate JWT Token
        token = create_access_token({
            "sub": user.get("email"),
            "role": user.get("role", "admin"),
            "full_name": user.get("full_name", "HR Admin")
        })

        return AuthResponse(
            success=True,
            email=user.get("email"),
            full_name=user.get("full_name", "HR Admin"),
            role=user.get("role", "admin"),
            access_token=token,
            token_type="bearer",
            message="Đăng nhập thành công và mã hóa JWT Token!"
        )
    except APIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.post("/change-password", response_model=AuthResponse)
async def change_password(
    payload: ChangePasswordRequest,
    supabase: Client = Depends(get_supabase)
):
    """
    Đổi mật khẩu tài khoản HR nội bộ và mã hóa Hash PBKDF2 vào Supabase CSDL.
    """
    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu mới phải có độ dài ít nhất 6 ký tự!"
        )

    # Hash the new password securely with Salt
    new_hashed_password = hash_password(payload.new_password)

    try:
        res = supabase.table("user_account").select("*").eq("email", payload.email).execute()

        if not res.data:
            # If not present yet, insert user account with hashed password
            new_user = {
                "email": payload.email,
                "password": new_hashed_password,
                "full_name": "HR Admin",
                "role": "admin"
            }
            supabase.table("user_account").insert(new_user).execute()
            
            token = create_access_token({"sub": payload.email, "role": "admin"})
            return AuthResponse(
                success=True,
                email=payload.email,
                access_token=token,
                message="Đã khởi tạo và mã hóa đổi mật khẩu Supabase DB thành công!"
            )

        user = res.data[0]
        stored_password = user.get("password", "")

        # Verify current password
        if not verify_password(payload.current_password, stored_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu hiện tại không đúng!"
            )

        # Update password hash in Supabase DB
        supabase.table("user_account").update({
            "password": new_hashed_password,
            "updated_at": datetime.now().isoformat()
        }).eq("email", payload.email).execute()

        # Issue new JWT Token
        token = create_access_token({"sub": payload.email, "role": "admin"})

        return AuthResponse(
            success=True,
            email=payload.email,
            access_token=token,
            token_type="bearer",
            message="Đổi mật khẩu tài khoản HR & mã hóa CSDL Supabase thành công!"
        )
    except APIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.get("/me")
async def get_current_user(
    authorization: str = Header(None),
    supabase: Client = Depends(get_supabase)
):
    """
    Lấy thông tin tài khoản HR từ mã Token JWT.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return {"email": "admin@talentagent.ai", "full_name": "HR Admin", "role": "admin"}

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mã JWT Token không hợp lệ hoặc đã hết hạn!"
        )

    email = payload.get("sub")
    return {
        "email": email,
        "full_name": payload.get("full_name", "HR Admin"),
        "role": payload.get("role", "admin"),
        "exp": payload.get("exp")
    }
