from fastapi import APIRouter

from app.services.llm_service import LLMService

router = APIRouter()

llm = LLMService()


@router.get("/test")
async def test_ai():
    result = await llm.chat("Xin chào, hãy giới thiệu bản thân.")

    return {
        "response": result
    }