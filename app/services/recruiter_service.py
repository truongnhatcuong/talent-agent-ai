import json

from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService
from app.services.output_parser import OutputParser


class RecruiterService:

    def __init__(self):
        self.llm = LLMService()

    async def match_cv(self, cv: dict, jd: str):
        system_prompt = PromptService.load("jd_matching.txt")

        user_prompt = f"""
Candidate CV

{json.dumps(cv, indent=2, ensure_ascii=False)}

Job Description

{jd}
"""

        result = await self.llm.chat(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
        )

        return OutputParser.parse_json(result)

    async def recommend_jobs(self, cv: dict, jobs: list[dict]):
        """
        Phân tích và đề xuất danh sách tất cả vị trí tuyển dụng phù hợp với CV ứng viên
        sắp xếp theo tỷ lệ % match score giảm dần.
        """
        if not jobs:
            return []

        system_prompt = PromptService.load("job_recommendation.txt")

        simplified_jobs = []
        for j in jobs:
            simplified_jobs.append({
                "job_id": j.get("id"),
                "title": j.get("title"),
                "department": j.get("department"),
                "description": j.get("description")
            })

        user_prompt = f"""
Candidate CV:
{json.dumps(cv, indent=2, ensure_ascii=False)}

Available Open Jobs:
{json.dumps(simplified_jobs, indent=2, ensure_ascii=False)}
"""

        result = await self.llm.chat(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
        )

        return OutputParser.parse_json(result)