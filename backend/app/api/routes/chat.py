import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse, StreamEvent
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await ChatService().chat(request)


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        async for event in ChatService().stream_chat(request):
            payload = event.model_dump(mode="json")
            yield f"event: {event.event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/cancel")
async def cancel_chat() -> dict[str, bool]:
    return {"success": True}

