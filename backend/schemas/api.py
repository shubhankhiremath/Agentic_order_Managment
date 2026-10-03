from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)


class ToolTrace(BaseModel):
    tool: str | None = None
    purpose: str | None = None
    status: str | None = None


class ActionTrace(BaseModel):
    action: str | None = None
    status: str | None = None
    ticket_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tools_used: list[ToolTrace] = []
    sources: list[str] = []
    actions: list[ActionTrace] = []


class SupportTicketRequest(BaseModel):
    order_id: str = Field(..., min_length=8, max_length=64)
    issue: str = Field(..., min_length=3, max_length=128)
    description: str = Field(..., min_length=3, max_length=2000)
