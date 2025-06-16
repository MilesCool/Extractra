"""Pydantic models for extraction API."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, HttpUrl


class ExtractionStatus(str, Enum):
    """Extraction status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionRequest(BaseModel):
    """Request model for starting extraction."""
    url: str
    requirements: str


class StageInfo(BaseModel):
    """Information about extraction stage."""
    name: str
    description: str
    status: ExtractionStatus
    progress: int = 0
    details: str = "Waiting to start..."


class ExtractionResult(BaseModel):
    """Extraction result information."""
    format: str
    size: str
    records: int
    fields: int
    download_url: str


class ExtractionSession(BaseModel):
    """Complete extraction session information."""
    session_id: str
    url: str
    requirements: str
    status: ExtractionStatus
    created_at: datetime
    stages: List[StageInfo]
    result: Optional[ExtractionResult] = None
    error: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: str
    data: Optional[Dict[str, Any]] = None


class StageUpdateMessage(WebSocketMessage):
    """Stage update WebSocket message."""
    stage_index: int
    stage: StageInfo
    overall_progress: float


class ExtractionCompletedMessage(WebSocketMessage):
    """Extraction completed WebSocket message."""
    result: ExtractionResult


class ExtractionErrorMessage(WebSocketMessage):
    """Extraction error WebSocket message."""
    error: str 