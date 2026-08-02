from supabase import create_client, Client
from app.core.config import SUPABASE_URL, SUPABASE_KEY, DATABASE_URL

# Khởi tạo Supabase client chính
supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("Warning: Missing SUPABASE_URL or SUPABASE_KEY in .env")

# Thư viện SQLModel / Engine (nếu dùng kết nối trực tiếp DB)
engine = None
if DATABASE_URL:
    try:
        from sqlmodel import create_engine
        engine = create_engine(DATABASE_URL, echo=False)
    except Exception as e:
        print(f"Warning: SQLModel engine not initialized: {e}")

def get_supabase() -> Client:
    """Dependency cung cấp Supabase client cho FastAPI"""
    if not supabase:
        raise RuntimeError("Supabase Client is not initialized.")
    return supabase

def get_session():
    """Dependency cung cấp DB session bằng SQLModel"""
    if not engine:
        raise RuntimeError("DATABASE_URL engine is not initialized.")
    from sqlmodel import Session
    with Session(engine) as session:
        yield session

def init_db():
    """Khởi tạo bảng (dev mode)"""
    if engine:
        try:
            from sqlmodel import SQLModel
            SQLModel.metadata.create_all(engine)
        except Exception as e:
            print(f"Warning: Could not create_all SQLModel metadata: {e}")
