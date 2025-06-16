"""Task API endpoints."""

from typing import Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

from models.task import TaskRequest, TaskResponse, TaskStatusResponse
from services.task_service import task_manager

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest) -> TaskResponse:
    """
    Create a new data extraction task.
    
    Args:
        request: Task creation request
        
    Returns:
        Task creation response
    """
    try:
        logger.info(f"Creating task for user {request.user_id} with URL {request.target_url}")
        response = await task_manager.create_task(request)
        return response
    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get task status and progress information.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Task status response
    """
    try:
        status_response = await task_manager.get_task_status(task_id)
        if not status_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        return status_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/tasks/{task_id}/stream")
async def stream_task_progress(task_id: str):
    """
    Stream real-time task progress updates using Server-Sent Events.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Streaming response with task updates
    """
    async def generate_progress_stream():
        """Generate progress stream for the task."""
        try:
            # Check if task exists
            status_response = await task_manager.get_task_status(task_id)
            if not status_response:
                yield f"data: {{'error': 'Task {task_id} not found'}}\n\n"
                return
            
            # Stream progress updates
            last_progress = -1
            while True:
                current_status = await task_manager.get_task_status(task_id)
                if not current_status:
                    break
                
                # Send update if progress changed or task completed/failed
                if (current_status.progress != last_progress or 
                    current_status.status in ["completed", "failed"]):
                    
                    status_data = {
                        "task_id": current_status.task_id,
                        "status": current_status.status,
                        "progress": current_status.progress,
                        "current_agent": current_status.current_agent,
                        "message": current_status.message,
                        "error": current_status.error,
                        "updated_at": current_status.updated_at.isoformat(),
                    }
                    
                    yield f"data: {status_data}\n\n"
                    last_progress = current_status.progress
                    
                    # Stop streaming if task is completed or failed
                    if current_status.status in ["completed", "failed"]:
                        break
                
                # Wait before next check
                import asyncio
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in progress stream for task {task_id}: {str(e)}")
            yield f"data: {{'error': 'Stream error: {str(e)}'}}\n\n"
    
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str) -> Dict:
    """
    Get final task result.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Task result data
    """
    try:
        status_response = await task_manager.get_task_status(task_id)
        if not status_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        if status_response.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task {task_id} is not completed yet. Current status: {status_response.status}"
            )
        
        if not status_response.result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No result available for task {task_id}"
            )
        
        return {
            "task_id": task_id,
            "result": status_response.result.dict(),
            "completed_at": status_response.updated_at.isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task result for {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task result: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def cleanup_task(task_id: str) -> Dict[str, str]:
    """
    Cleanup task data and resources.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Success message
    """
    try:
        success = await task_manager.cleanup_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        return {"message": f"Task {task_id} cleaned up successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup task: {str(e)}"
        ) 