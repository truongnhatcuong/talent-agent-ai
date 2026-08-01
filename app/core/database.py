from supabase import create_client, Client
from app.core.config import SUPABASE_URL, SUPABASE_KEY

# Khởi tạo Supabase client
supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("Warning: Chưa cấu hình SUPABASE_URL và SUPABASE_KEY trong file .env")
