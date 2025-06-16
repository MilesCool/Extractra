"""Task data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    DISCOVERY = "discovery"
    EXTRACTION = "extraction"
    INTEGRATION = "integration"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, Enum):
    """Agent type enumeration."""
    PAGE_DISCOVERY = "page_discovery"
    CONTENT_EXTRACTION = "content_extraction"
    RESULT_INTEGRATION = "result_integration"


class TaskRequest(BaseModel):
    """Task creation request model."""
    requirements: str = Field(..., description="Data extraction requirements")
    target_url: str = Field(..., description="Target website URL")
    user_id: str = Field(..., description="User identifier")


class ExecutionStep(BaseModel):
    """Execution step model."""
    step_id: str
    agent_name: str
    description: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ADKAgentState(BaseModel):
    """ADK agent state model."""
    active_agent: str
    execution_plan: List[ExecutionStep]
    current_step: int
    total_steps: int


class PageLink(BaseModel):
    """Page link model."""
    url: str
    title: str
    relevance_score: Optional[float] = None


class ExtractedData(BaseModel):
    """Extracted data model."""
    page_url: str
    extracted_data: Dict[str, Any]
    extraction_metadata: Dict[str, Any]
    issues_encountered: List[str] = []


class StructuredData(BaseModel):
    """Final structured data model."""
    integrated_data: Dict[str, Any]
    metadata: Dict[str, Any]
    quality_score: Optional[float] = None


class TaskResponse(BaseModel):
    """Task creation response model."""
    task_id: str
    status: TaskStatus
    message: str
    created_at: datetime


class TaskStatusResponse(BaseModel):
    """Task status response model."""
    task_id: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    current_agent: Optional[AgentType] = None
    agent_state: Optional[ADKAgentState] = None
    message: str
    result: Optional[StructuredData] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime 