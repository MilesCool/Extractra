"""WebSocket endpoints for real-time data extraction with enhanced security."""

import asyncio
import json
import uuid
from typing import Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.websockets import WebSocketState
from loguru import logger

# Import workflow components
from parallel_extraction_workflow import ParallelExtractionWorkflow
from models.extraction import ExtractionRequest, ExtractionStatus

router = APIRouter()

# Store active extraction sessions with enhanced security
active_sessions: Dict[str, Dict[str, Any]] = {}

# Connection timeout settings
CONNECTION_TIMEOUT = 300  # 5 minutes
PING_INTERVAL = 30  # 30 seconds
PONG_TIMEOUT = 10  # 10 seconds


class ConnectionManager:
    """Manage WebSocket connections with enhanced security."""
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection with security checks."""
        try:
            await websocket.accept()
            
            # Store connection with metadata
            self.active_connections[session_id] = {
                "websocket": websocket,
                "connected_at": datetime.now(),
                "last_ping": datetime.now(),
                "is_alive": True
            }
            
            logger.info(f"Secure WebSocket connected: {session_id}")
            
            # Start heartbeat monitoring
            asyncio.create_task(self._monitor_connection(session_id))
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection for {session_id}: {e}")
            raise
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection and cleanup."""
        if session_id in self.active_connections:
            connection_info = self.active_connections[session_id]
            connection_info["is_alive"] = False
            
            # Close WebSocket if still open
            websocket = connection_info["websocket"]
            if websocket.client_state == WebSocketState.CONNECTED:
                asyncio.create_task(websocket.close(code=1000, reason="Session ended"))
            
            del self.active_connections[session_id]
            logger.info(f"Secure WebSocket disconnected: {session_id}")
            
            # Clean up session data when WebSocket disconnects
            if session_id in active_sessions:
                logger.info(f"Cleaning up session data for {session_id}")
                del active_sessions[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        """Send message to specific session with error handling."""
        if session_id not in self.active_connections:
            logger.warning(f"Attempted to send message to non-existent session: {session_id}")
            return False
        
        connection_info = self.active_connections[session_id]
        websocket = connection_info["websocket"]
        
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(message))
                return True
            else:
                logger.warning(f"WebSocket not connected for session {session_id}")
                self.disconnect(session_id)
                return False
                
        except Exception as e:
            logger.error(f"Error sending message to {session_id}: {e}")
            self.disconnect(session_id)
            return False
    
    async def _monitor_connection(self, session_id: str):
        """Monitor connection health with heartbeat."""
        while session_id in self.active_connections:
            try:
                connection_info = self.active_connections[session_id]
                
                if not connection_info["is_alive"]:
                    break
                
                # Check if connection is stale
                last_ping = connection_info["last_ping"]
                if datetime.now() - last_ping > timedelta(seconds=CONNECTION_TIMEOUT):
                    logger.warning(f"Connection timeout for session {session_id}")
                    self.disconnect(session_id)
                    break
                
                await asyncio.sleep(PING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error monitoring connection {session_id}: {e}")
                self.disconnect(session_id)
                break
    
    def update_last_ping(self, session_id: str):
        """Update last ping timestamp."""
        if session_id in self.active_connections:
            self.active_connections[session_id]["last_ping"] = datetime.now()


manager = ConnectionManager()


@router.websocket("/ws/extraction/{session_id}")
async def websocket_extraction(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time extraction updates with enhanced security."""
    
    logger.info(f"WebSocket connection attempt for session: {session_id}")
    
    # Validate session exists
    if session_id not in active_sessions:
        logger.warning(f"Invalid session ID: {session_id}")
        await websocket.close(code=4004, reason="Invalid session ID")
        return
    
    logger.info(f"Session {session_id} found, establishing WebSocket connection")
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Set receive timeout to detect dead connections
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message = json.loads(data)
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Update last ping time and respond with pong
                    manager.update_last_ping(session_id)
                    await manager.send_message(session_id, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif message_type == "heartbeat":
                    # Client heartbeat - just update timestamp
                    manager.update_last_ping(session_id)
                    
                else:
                    logger.warning(f"Unknown message type '{message_type}' from session {session_id}")
                    
            except asyncio.TimeoutError:
                # No message received within timeout - check if connection is still alive
                if session_id in manager.active_connections:
                    connection_info = manager.active_connections[session_id]
                    last_ping = connection_info["last_ping"]
                    
                    if datetime.now() - last_ping > timedelta(seconds=PONG_TIMEOUT):
                        logger.warning(f"Client {session_id} failed to respond to heartbeat")
                        break
                else:
                    break
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from session {session_id}")
                await manager.send_message(session_id, {
                    "type": "error",
                    "message": "Invalid message format"
                })
                
    except WebSocketDisconnect:
        logger.info(f"Client {session_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        manager.disconnect(session_id)
        logger.info(f"Session {session_id} cleaned up")


@router.post("/extraction/start")
async def start_extraction(request: ExtractionRequest):
    """Start a new extraction process."""
    session_id = str(uuid.uuid4())
    
    # Define progress callback function
    async def progress_callback(session_id: str, stage_index: int, progress: int, details: str):
        """Callback function to update progress in real-time."""
        await update_stage_status(session_id, stage_index, "in-progress", progress, details)
    
    # Create workflow instance for this session with progress callback
    workflow = ParallelExtractionWorkflow(user_id=session_id, progress_callback=progress_callback)
    
    # Initialize session
    active_sessions[session_id] = {
        "url": request.url,
        "requirements": request.requirements,
        "status": "initializing",
        "created_at": datetime.now(),
        "workflow": workflow,  # Store workflow instance
        "stages": [
            {
                "name": "Page Discovery",
                "description": "Analyzing website structure and discovering pages",
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
    """Run the extraction process using ParallelExtractionWorkflow and send updates via WebSocket."""
    try:
        # Wait a bit to ensure WebSocket connection is established
        await asyncio.sleep(1)
        
        # Get workflow instance from session
        if session_id not in active_sessions:
            logger.error(f"Session {session_id} not found")
            return
            
        workflow = active_sessions[session_id]["workflow"]
        
        # Stage 1: Page Discovery
        logger.info(f"Starting page discovery for session {session_id}")
        await update_stage_status(session_id, 0, "in-progress", 0, "")
        
        try:
            discovered_links = await workflow.page_discovery(url, requirements)
            logger.info(f"Page discovery completed for session {session_id}")
            await update_stage_status(session_id, 0, "completed", 100, f"Discovered {len(discovered_links)} pages")
        except Exception as e:
            logger.error(f"Page discovery failed for session {session_id}: {e}")
            await update_stage_status(session_id, 0, "completed", 100, f"Discovery failed: {str(e)}")
            # Continue with mock data for demo
            discovered_links = []
        
        # Stage 2: Content Extraction

        # await asyncio.sleep(40)

        logger.info(f"Starting content extraction for session {session_id}")
        await update_stage_status(session_id, 1, "in-progress", 0, "Starting content extraction...")
        
        try:
            if discovered_links:
                # The workflow will now handle progress updates automatically through the callback
                extraction_results = await workflow.parallel_extraction(requirements)
                logger.info(f"Content extraction completed for session {session_id}")
                await update_stage_status(session_id, 1, "completed", 100, f"Extracted data from {len(extraction_results)} sources")
            else:
                await update_stage_status(session_id, 1, "completed", 100, "No links discovered")
                extraction_results = []
        except Exception as e:
            logger.error(f"Content extraction failed for session {session_id}: {e}")
            await update_stage_status(session_id, 1, "completed", 100, f"Extraction failed: {str(e)}")
            extraction_results = []
        
        # Stage 3: Result Integration
        logger.info(f"Starting result integration for session {session_id}")
        await update_stage_status(session_id, 2, "in-progress", 0, "Integrating results...")
        
        try:
            if extraction_results:
                final_data = await workflow.result_integration()
                integration_message = f"Integrated {len(final_data.get('integrated_data', []))} items"
            else:
                integration_message = "No data to integrate"
        
            # Mark extraction as completed
            if session_id in active_sessions:
                active_sessions[session_id]["status"] = "completed"
                
                # Store workflow results if available
                workflow_data = {}
                if hasattr(workflow, 'final_data') and workflow.final_data:
                    workflow_data = workflow.final_data
                
                # Generate CSV data and calculate file size
                csv_data = ""
                file_size = "0 KB"
                record_count = 0
                field_count = 0
                
                integrated_data = workflow_data.get("integrated_data", [])[0]
                if integrated_data:
                    # Generate CSV from real data
                    # Get all unique keys from integrated_data
                    all_keys = set()
                    for item in integrated_data:
                        if isinstance(item, dict):
                            all_keys.update(item.keys())
                    
                    # Create header row with all keys
                    headers = sorted(list(all_keys))
                    csv_lines = [",".join(headers)]
                    
                    # Process each item in integrated_data
                    for item in integrated_data:
                        if isinstance(item, dict):
                            row_values = []
                            for key in headers:
                                value = str(item.get(key, "")).replace(",", ";").replace("\n", " ").replace("\r", " ")
                                # Keep full value without truncation
                                row_values.append(value)
                            csv_lines.append(",".join(row_values))
                    
                    csv_data = "\n".join(csv_lines)
                    record_count = len(integrated_data)
                    field_count = len(headers)
                
                # Calculate file size
                csv_size_bytes = len(csv_data.encode('utf-8'))
                if csv_size_bytes < 1024:
                    file_size = f"{csv_size_bytes} B"
                elif csv_size_bytes < 1024 * 1024:
                    file_size = f"{csv_size_bytes / 1024:.1f} KB"
                else:
                    file_size = f"{csv_size_bytes / (1024 * 1024):.1f} MB"
                
                # Store CSV data and metadata in session
                active_sessions[session_id]["result"] = {
                    "format": "CSV File",
                    "size": file_size,
                    "records": record_count,
                    "fields": field_count,
                    "download_url": f"/api/v1/extraction/{session_id}/download",
                    "workflow_data": workflow_data,
                    "csv_data": csv_data  # Store generated CSV data
                }
                
            await update_stage_status(session_id, 2, "completed", 100, integration_message)
            
        except Exception as e:
            logger.error(f"Result integration failed for session {session_id}: {e}")
            await update_stage_status(session_id, 2, "completed", 100, f"Integration failed: {str(e)}")
        
        # Send completion message
        logger.info(f"Extraction completed for session {session_id}")
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
        logger.warning(f"Session {session_id} not found in active_sessions")
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
    
    # Prepare message
    message = {
        "type": "stage_update",
        "stage_index": stage_index,
        "stage": active_sessions[session_id]["stages"][stage_index],
        "overall_progress": overall_progress
    }
    
    # Log the update
    logger.info(f"Updating stage {stage_index} for session {session_id}: {status} - {details}")
    
    # Send update via WebSocket
    success = await manager.send_message(session_id, message)
    if success:
        logger.info(f"Stage update sent successfully for session {session_id}")
    else:
        logger.warning(f"Failed to send stage update for session {session_id}")


@router.get("/extraction/{session_id}/status")
async def get_extraction_status(session_id: str):
    """Get current extraction status."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]


@router.get("/extraction/{session_id}/preview")
async def get_preview_data(session_id: str, limit: int = 5):
    """Get preview data for extraction result."""
    logger.info(f"Preview request for session {session_id}")
    
    if session_id not in active_sessions:
        logger.error(f"Session {session_id} not found in active_sessions")
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    logger.info(f"Session {session_id} status: {session['status']}")
    
    if session["status"] != "completed":
        logger.error(f"Session {session_id} extraction not completed, status: {session['status']}")
        raise HTTPException(status_code=400, detail=f"Extraction not completed, current status: {session['status']}")
    
    # Get workflow data
    result_data = session.get("result", {})
    logger.info(f"Session {session_id} result keys: {list(result_data.keys())}")
    
    workflow_data = result_data.get("workflow_data", {})
    logger.info(f"Session {session_id} workflow_data keys: {list(workflow_data.keys())}")
    
    integrated_data = workflow_data.get("integrated_data", [])
    logger.info(f"Session {session_id} integrated_data length: {len(integrated_data)}")
    
    if not integrated_data:
        logger.info(f"Session {session_id} no integrated_data, returning empty")
        return {
            "headers": [],
            "data": [],
            "total_records": 0
        }
    
    integrated_data_list = integrated_data[0] if integrated_data else []
    logger.info(f"Session {session_id} integrated_data_list length: {len(integrated_data_list) if isinstance(integrated_data_list, list) else 'not a list'}")
    
    if not integrated_data_list:
        logger.info(f"Session {session_id} no integrated_data_list, returning empty")
        return {
            "headers": [],
            "data": [],
            "total_records": 0
        }
    
    # Get preview data (limited)
    preview_data = integrated_data_list[:limit] if isinstance(integrated_data_list, list) else []
    logger.info(f"Session {session_id} preview_data length: {len(preview_data)}")
    
    # Extract headers from the first item
    headers = []
    if preview_data and isinstance(preview_data[0], dict):
        headers = list(preview_data[0].keys())
        logger.info(f"Session {session_id} headers: {headers}")
    
    logger.info(f"Session {session_id} returning preview with {len(preview_data)} items")
    return {
        "headers": headers,
        "data": preview_data,
        "total_records": len(integrated_data_list) if isinstance(integrated_data_list, list) else 0
    }


@router.get("/extraction/{session_id}/download")
async def download_result(session_id: str):
    """Download extraction result."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Extraction not completed")
    
    # Get pre-generated CSV data
    import io
    from fastapi.responses import StreamingResponse
    
    csv_data = session.get("result", {}).get("csv_data", "")
    
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=extraction_{session_id}.csv"}
    ) 