"""Task management service."""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from models.task import (
    ADKAgentState,
    AgentType,
    ExecutionStep,
    StructuredData,
    TaskRequest,
    TaskResponse,
    TaskStatus,
    TaskStatusResponse,
)


class TaskManager:
    """Task management service."""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.task_lock = asyncio.Lock()
    
    async def create_task(self, request: TaskRequest) -> TaskResponse:
        """
        Create a new extraction task.
        
        Args:
            request: Task creation request
            
        Returns:
            Task creation response
        """
        task_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        async with self.task_lock:
            self.tasks[task_id] = {
                "id": task_id,
                "request": request,
                "status": TaskStatus.PENDING,
                "progress": 0,
                "current_agent": None,
                "agent_state": None,
                "message": "Task created successfully",
                "result": None,
                "error": None,
                "created_at": created_at,
                "updated_at": created_at,
            }
        
        # Start task execution in background
        asyncio.create_task(self._execute_task(task_id))
        
        logger.info(f"Created task {task_id} for user {request.user_id}")
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Task created successfully",
            created_at=created_at,
        )
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatusResponse]:
        """
        Get task status.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status response or None if not found
        """
        async with self.task_lock:
            task_data = self.tasks.get(task_id)
            if not task_data:
                return None
            
            return TaskStatusResponse(
                task_id=task_id,
                status=task_data["status"],
                progress=task_data["progress"],
                current_agent=task_data["current_agent"],
                agent_state=task_data["agent_state"],
                message=task_data["message"],
                result=task_data["result"],
                error=task_data["error"],
                created_at=task_data["created_at"],
                updated_at=task_data["updated_at"],
            )
    
    async def cleanup_task(self, task_id: str) -> bool:
        """
        Cleanup task data.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task was found and cleaned up
        """
        async with self.task_lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.info(f"Cleaned up task {task_id}")
                return True
            return False
    
    async def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: int,
        current_agent: Optional[AgentType] = None,
        message: str = "",
        result: Optional[StructuredData] = None,
        error: Optional[str] = None,
        agent_state: Optional[ADKAgentState] = None,
    ):
        """Update task status."""
        async with self.task_lock:
            if task_id in self.tasks:
                self.tasks[task_id].update({
                    "status": status,
                    "progress": progress,
                    "current_agent": current_agent,
                    "agent_state": agent_state,
                    "message": message,
                    "result": result,
                    "error": error,
                    "updated_at": datetime.utcnow(),
                })
    
    async def _execute_task(self, task_id: str):
        """
        Execute extraction task.
        
        Args:
            task_id: Task identifier
        """
        try:
            task_data = self.tasks.get(task_id)
            if not task_data:
                return
            
            request = task_data["request"]
            logger.info(f"Starting execution of task {task_id}")
            
            # Phase 1: Page Discovery
            await self._update_task_status(
                task_id,
                TaskStatus.DISCOVERY,
                10,
                AgentType.PAGE_DISCOVERY,
                "Discovering relevant pages...",
            )
            
            discovery_result = await self._run_page_discovery(
                request.target_url, request.requirements
            )
            
            if not discovery_result or "error" in discovery_result:
                await self._update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    0,
                    error=discovery_result.get("error", "Page discovery failed"),
                )
                return
            
            page_links = discovery_result.get("all_page_links", [])
            logger.info(f"Discovered {len(page_links)} pages for task {task_id}")
            
            # Phase 2: Content Extraction
            await self._update_task_status(
                task_id,
                TaskStatus.EXTRACTION,
                30,
                AgentType.CONTENT_EXTRACTION,
                f"Extracting content from {len(page_links)} pages...",
            )
            
            extraction_results = await self._run_parallel_extraction(
                page_links, request.requirements
            )
            
            if not extraction_results:
                await self._update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    0,
                    error="Content extraction failed",
                )
                return
            
            # Phase 3: Result Integration
            await self._update_task_status(
                task_id,
                TaskStatus.INTEGRATION,
                70,
                AgentType.RESULT_INTEGRATION,
                "Integrating and cleaning extracted data...",
            )
            
            integration_result = await self._run_result_integration(extraction_results)
            
            if not integration_result or "error" in integration_result:
                await self._update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    0,
                    error=integration_result.get("error", "Result integration failed"),
                )
                return
            
            # Task completed successfully
            final_result = StructuredData(
                integrated_data=integration_result.get("integrated_data", {}),
                metadata=integration_result.get("integration_metadata", {}),
                quality_score=integration_result.get("data_quality_report", {}).get(
                    "accuracy_score", 0.0
                ),
            )
            
            await self._update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                100,
                message="Task completed successfully",
                result=final_result,
            )
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed with exception: {str(e)}")
            await self._update_task_status(
                task_id,
                TaskStatus.FAILED,
                0,
                error=f"Task execution failed: {str(e)}",
            )
    
    async def _run_page_discovery(self, target_url: str, requirements: str) -> Dict:
        """Run page discovery agent."""
        try:
            # Simulate ADK agent execution
            # In real implementation, this would use ADK's agent execution
            logger.info(f"Running page discovery for {target_url}")
            
            # This is a placeholder - in real implementation, you would:
            # 1. Create agent context with target_url and requirements
            # 2. Execute page_discovery_agent
            # 3. Return the agent's output
            
            # For now, return a mock result
            return {
                "main_page_url": target_url,
                "all_page_links": [
                    {"url": target_url, "title": "Main Page", "relevance_score": 1.0}
                ],
                "analysis_summary": "Mock discovery result",
                "total_links_found": 1,
            }
            
        except Exception as e:
            logger.error(f"Page discovery failed: {str(e)}")
            return {"error": str(e)}
    
    async def _run_parallel_extraction(
        self, page_links: List[Dict], requirements: str
    ) -> List[Dict]:
        """Run parallel content extraction."""
        try:
            logger.info(f"Running parallel extraction for {len(page_links)} pages")
            
            # Create parallel agents based on number of pages
            num_agents = min(len(page_links), 5)  # Limit to 5 parallel agents
            
            # This is a placeholder - in real implementation, you would:
            # 1. Create parallel extraction agents
            # 2. Distribute page_links among agents
            # 3. Execute agents in parallel
            # 4. Collect and return results
            
            # For now, return mock results
            results = []
            for link in page_links:
                results.append({
                    "page_url": link["url"],
                    "page_title": link.get("title", ""),
                    "extracted_data": {"mock_data": "placeholder"},
                    "extraction_metadata": {
                        "processing_time": 1.0,
                        "data_volume": 1,
                        "content_length": 1000,
                        "extraction_confidence": 0.8,
                    },
                    "issues_encountered": [],
                    "data_quality_score": 0.8,
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Parallel extraction failed: {str(e)}")
            return []
    
    async def _run_result_integration(self, extraction_results: List[Dict]) -> Dict:
        """Run result integration agent."""
        try:
            logger.info(f"Running result integration for {len(extraction_results)} results")
            
            # This is a placeholder - in real implementation, you would:
            # 1. Create integration agent context with extraction_results
            # 2. Execute result_integration_agent
            # 3. Return the agent's output
            
            # For now, return a mock result
            return {
                "integrated_data": {
                    "total_records": len(extraction_results),
                    "data": [result["extracted_data"] for result in extraction_results],
                },
                "integration_metadata": {
                    "total_pages_processed": len(extraction_results),
                    "total_records": len(extraction_results),
                    "duplicates_removed": 0,
                    "data_conflicts_resolved": 0,
                    "integration_confidence": 0.9,
                },
                "data_quality_report": {
                    "completeness_score": 0.9,
                    "consistency_score": 0.8,
                    "accuracy_score": 0.85,
                },
                "processing_summary": "Mock integration completed",
            }
            
        except Exception as e:
            logger.error(f"Result integration failed: {str(e)}")
            return {"error": str(e)}


# Global task manager instance
task_manager = TaskManager() 