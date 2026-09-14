from pydantic import BaseModel

class AssistantQuery(BaseModel):
    message: str
    project_id: int
    context: dict = {} # Optional extra context

class AssistantResponse(BaseModel):
    response: str
    sources: list[str] = []
