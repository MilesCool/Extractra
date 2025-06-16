"""WebSocket endpoints for real-time data extraction."""

import asyncio
import json
import uuid
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from loguru import logger

# from parallel_extraction_workflow import ParallelExtractionWorkflow
from models.extraction import ExtractionRequest, ExtractionStatus

router = APIRouter()

# Store active extraction sessions
active_sessions: Dict[str, Dict[str, Any]] = {}


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """Send message to specific session."""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)


manager = ConnectionManager()


@router.websocket("/ws/extraction/{session_id}")
async def websocket_extraction(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time extraction updates."""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_message(session_id, {"type": "pong"})
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        # Clean up session data
        if session_id in active_sessions:
            del active_sessions[session_id]
        logger.info(f"Session {session_id} disconnected and cleaned up")


@router.post("/extraction/start")
async def start_extraction(request: ExtractionRequest):
    """Start a new extraction process."""
    session_id = str(uuid.uuid4())
    
    # Initialize session
    active_sessions[session_id] = {
        "url": request.url,
        "requirements": request.requirements,
        "status": "initializing",
        "created_at": datetime.now(),
        "stages": [
            {
                "name": "Page Discovery",
                "description": "Discovering and mapping website structure",
                "status": "pending",
                "progress": 0,
                "details": "Waiting to start..."
            },
            {
                "name": "Content Extraction",
                "description": "Extracting relevant data based on requirements",
                "status": "pending",
                "progress": 0,
                "details": "Waiting to start..."
            },
            {
                "name": "Result Integration",
                "description": "Processing and formatting extracted data",
                "status": "pending",
                "progress": 0,
                "details": "Waiting to start..."
            }
        ]
    }
    
    # Start extraction in background
    asyncio.create_task(run_extraction(session_id, request.url, request.requirements))
    
    return {"session_id": session_id, "status": "started"}


async def run_extraction(session_id: str, url: str, requirements: str):
    """Run the extraction process and send updates via WebSocket."""
    try:
        # Initialize workflow
        # workflow = ParallelExtractionWorkflow()
        
        # Stage 1: Page Discovery
        await update_stage_status(session_id, 0, "in-progress", 0, "Starting page discovery...")
        
        # Simulate page discovery with progress updates
        discovered_pages = []
        for i in range(1, 16):  # Simulate discovering 15 pages
            await asyncio.sleep(10)  # Simulate work
            progress = (i / 15) * 100
            await update_stage_status(
                session_id, 0, "in-progress", progress, 
                f"Discovered {i} subpages"
            )
        
        await update_stage_status(session_id, 0, "completed", 100, "Page discovery completed")
        
        # Stage 2: Content Extraction
        await update_stage_status(session_id, 1, "in-progress", 0, "Starting content extraction...")
        
        # Simulate content extraction
        for i in range(1, 16):
            await asyncio.sleep(0.2)
            progress = (i / 15) * 100
            await update_stage_status(
                session_id, 1, "in-progress", progress,
                f"Extracted {i}/15 pages"
            )
        
        await update_stage_status(session_id, 1, "completed", 100, "Content extraction completed")
        
        # Stage 3: Result Integration
        await update_stage_status(session_id, 2, "in-progress", 0, "Processing data...")
        
        integration_steps = ["Processing data...", "Formatting results...", "Generating file...", "Finalizing..."]
        for i, step in enumerate(integration_steps):
            await asyncio.sleep(0.8)
            progress = ((i + 1) / len(integration_steps)) * 100
            await update_stage_status(session_id, 2, "in-progress", progress, step)
        
        await update_stage_status(session_id, 2, "completed", 100, "Integration completed")
        
        # Mark extraction as completed
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "completed"
            active_sessions[session_id]["result"] = {
                "format": "CSV File",
                "size": "1.2 MB",
                "records": 2847,
                "fields": 12,
                "download_url": f"/api/v1/extraction/{session_id}/download"
            }
        
        # Send completion message
        await manager.send_message(session_id, {
            "type": "extraction_completed",
            "result": active_sessions[session_id]["result"]
        })
        
    except Exception as e:
        logger.error(f"Extraction failed for session {session_id}: {e}")
        await manager.send_message(session_id, {
            "type": "extraction_error",
            "error": str(e)
        })
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "failed"
            active_sessions[session_id]["error"] = str(e)


async def update_stage_status(session_id: str, stage_index: int, status: str, progress: int, details: str):
    """Update stage status and send via WebSocket."""
    if session_id not in active_sessions:
        return
    
    # Update session data
    active_sessions[session_id]["stages"][stage_index].update({
        "status": status,
        "progress": progress,
        "details": details
    })
    
    # Calculate overall progress
    completed_stages = sum(1 for stage in active_sessions[session_id]["stages"] if stage["status"] == "completed")
    current_stage_progress = active_sessions[session_id]["stages"][stage_index]["progress"] if status == "in-progress" else 0
    overall_progress = (completed_stages * 100 + current_stage_progress) / 3
    
    # Send update via WebSocket
    await manager.send_message(session_id, {
        "type": "stage_update",
        "stage_index": stage_index,
        "stage": active_sessions[session_id]["stages"][stage_index],
        "overall_progress": overall_progress
    })


@router.get("/extraction/{session_id}/status")
async def get_extraction_status(session_id: str):
    """Get current extraction status."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]


@router.get("/extraction/{session_id}/download")
async def download_result(session_id: str):
    """Download extraction result."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Extraction not completed")
    
    # Generate sample CSV data
    import io
    from fastapi.responses import StreamingResponse
    
    csv_data = """Title,Price,Category,URL
Sample Product 1,$29.99,Electronics,https://example.com/product1
Sample Product 2,$15.50,Books,https://example.com/product2
Sample Product 3,$45.00,Clothing,https://example.com/product3
Sample Product 4,$12.99,Home & Garden,https://example.com/product4
Sample Product 5,$89.99,Sports,https://example.com/product5"""
    
    # Clean up session after download
    del active_sessions[session_id]
    
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=extraction_{session_id}.csv"}
    ) 