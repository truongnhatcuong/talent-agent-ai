import httpx

from app.core.config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
)

from app.services.prompt_service import PromptService


class LLMService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=60,
            verify=False,  # Nếu API có SSL hợp lệ thì đổi thành True hoặc bỏ hẳn
        )

        self.api_key = AI_API_KEY
        self.base_url = AI_BASE_URL
        self.model = AI_MODEL

    async def chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = await self.client.post(
            url=url,
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(
                f"LLM API Error ({response.status_code}): {response.text}"
            )

        data = response.json()

        choices = data.get("choices")

        if not choices:
            raise Exception("LLM returned empty response.")

        return choices[0]["message"]["content"]

    async def parse_cv(self, cv_text: str) -> str:
        """
        Parse CV thành JSON
        """

        system_prompt = PromptService.load("cv_parser.txt")

        return await self.chat(
            prompt=cv_text,
            system_prompt=system_prompt,
            temperature=0.1,
        )