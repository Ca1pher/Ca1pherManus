# app/api/v1/endpoints.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest
from app.services.chat_service import stream_langgraph_response

router = APIRouter()

@router.post("/chat/stream", summary="Stream LangGraph chat responses")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Initiates a chat session with the LangGraph agent and streams
    intermediate states and the final answer back to the client.
    """
    return StreamingResponse(
        stream_langgraph_response(request),
        media_type="text/event-stream" # Standard for Server-Sent Events
    )
