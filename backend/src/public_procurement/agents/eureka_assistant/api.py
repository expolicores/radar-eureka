"""HTTP adapter for the read-only assistant. No provider details in public schemas."""

import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .chat import AssistantChat, ChatError, ChatReply

router = APIRouter(prefix="/api/eureka/assistant", tags=["Asistente Eureka"])


def get_chat(request: Request) -> AssistantChat:
    service: AssistantChat = request.app.state.assistant_chat
    return service


def get_owner(request: Request) -> uuid.UUID:
    provider: Callable[[Request], uuid.UUID] = request.app.state.current_user_provider
    return provider(request)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = None


class ChatFailure(BaseModel):
    code: str
    message: str
    reset_conversation: bool


@router.post(
    "/chat",
    response_model=ChatReply,
    responses={code: {"model": ChatFailure} for code in (404, 409, 429, 502, 503, 504)},
)
def chat(
    payload: ChatRequest,
    service: Annotated[AssistantChat, Depends(get_chat)],
    owner: Annotated[uuid.UUID, Depends(get_owner)],
) -> ChatReply | JSONResponse:
    try:
        return service.chat(payload.message, payload.conversation_id, owner)
    except ChatError as error:
        message = "No pude consultar Eureka en este momento. Intenta nuevamente."
        if error.code in {"conversation_expired", "conversation_limit"}:
            message = "La conversación terminó o expiró. Inicia una nueva conversación."
        elif error.code in {"conversation_busy", "assistant_busy"}:
            message = (
                "Eureka está atendiendo otra consulta. Espera un momento e intenta nuevamente."
            )
        return JSONResponse(
            status_code=error.status,
            content=ChatFailure(
                code=error.code, message=message, reset_conversation=error.reset
            ).model_dump(),
        )
