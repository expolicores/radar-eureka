"""HTTP read-only chat, with the same current-user convention as Eureka Assistant."""

from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .chat import InvestigationChat, Reply
from .service import AssistantError

router = APIRouter(prefix="/api/v1/investigation/assistant", tags=["Asistente de investigación"])


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None
    run_id: UUID | None = None


@router.post("/chat", response_model=Reply)
def chat(body: ChatRequest, request: Request) -> Reply | JSONResponse:
    service: InvestigationChat = request.app.state.investigation_assistant_chat
    owner = request.app.state.current_user_provider(request)
    try:
        return service.chat(body.message, body.conversation_id, body.run_id, owner)
    except AssistantError as error:
        return JSONResponse(
            status_code=error.status,
            content={
                "code": error.code,
                "message": "No fue posible consultar los resultados investigativos. "
                "Verifica la corrida o inicia una conversación nueva.",
                "reset_conversation": True,
            },
        )
