import os
import jwt
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.core.config import (
  SECRET_KEY,
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7



def hash_password(password: str) -> str:
    """
    Mã hóa mật khẩu an toàn sử dụng PBKDF2-HMAC-SHA256 với Salt.
    """
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu khớp với chuỗi đã mã hóa hay không.
    Hỗ trợ cả plain text fallback cho tài khoản khởi tạo ban đầu.
    """
    if not hashed_password:
        return False

    # Check PBKDF2 hashed format (salt$hash)
    if "$" in hashed_password:
        salt, key_hex = hashed_password.split("$", 1)
        new_key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return hmac.compare_digest(new_key.hex(), key_hex)

    # Fallback to plain text compare if legacy
    return hmac.compare_digest(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Tạo mã định danh JWT Access Token ký bằng mã hóa mã hóa HS256.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Giải mã và xác thực mã Token JWT.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
