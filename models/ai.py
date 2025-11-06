from pydantic import BaseModel

class ParseRequest(BaseModel):
    prompt: str