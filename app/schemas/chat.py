# app/schemas/chat.py

from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str

class StreamEvent(BaseModel):
    """
    Represents a single event to be streamed to the client.
    """
    event_type: str  # e.g., "node_update", "final_answer", "error"
    node: Optional[str] = None # Which node just executed (for node_update)
    data: Dict[str, Any] # The state or relevant data for the event
    message: Optional[str] = None # A human-readable message for the event
