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

{json.dumps(cv, indent=2)}

Job Description

{jd}
"""

        result = await self.llm.chat(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
        )

        return OutputParser.parse_json(result)