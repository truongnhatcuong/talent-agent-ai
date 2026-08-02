import os
from dotenv import load_dotenv

load_dotenv()

AI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL")
AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "talent_agent_ai_super_secret_jwt_key_2026_x89a")

EMAIL_USER = os.getenv("EMAIL_USER", "truongnhatcuong2222004@gmail.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "fexm bkjv godd viaw")
