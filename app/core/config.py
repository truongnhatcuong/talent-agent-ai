import os
from dotenv import load_dotenv

load_dotenv()

AI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL")
AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")