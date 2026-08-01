from pydantic import BaseModel


class MatchRequest(BaseModel):
    cv: dict
    jd: str