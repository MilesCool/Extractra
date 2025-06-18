#!/usr/bin/env python3
"""
Parallel Extraction Workflow - Handle large-scale link processing with parallel agents

This module implements a workflow based on Google ADK Runner agent switching pattern:
1. PageDiscoveryAgent discovers all relevant links
2. ParallelAgent processes links in batches of 2
3. ResultIntegrationAgent consolidates final results
"""

import asyncio
import json
import math
import re
from typing import List, Dict, Any

from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from loguru import logger

from adk.agents import create_extraction_agent, create_page_discovery_agent
from core.config import settings
from adk.tools.web_crawl import web_crawl

from dotenv import load_dotenv
load_dotenv(dotenv_path="backend/.env")

# Constants
APP_NAME = "extractra_parallel_workflow"
USER_ID = "user_1"

class ParallelExtractionWorkflow:
    """Parallel extraction workflow manager with three distinct phases."""
    
    def __init__(self, user_id: str, progress_callback=None):
        """Initialize the workflow with agents and session service.
        
        Args:
            user_id: User identifier for session management
            progress_callback: Optional callback function for progress updates
        """
        self.user_id = user_id
        self.progress_callback = progress_callback
        self.session_service = InMemorySessionService()
        self.batch_size = 2
        
        # Page Discovery Agent
        self.page_discovery_agent = create_page_discovery_agent("discovered_links")

        # Create 2 parallel extraction agents
        self.extraction_agent = create_extraction_agent()
        # self.parallel_extraction_agent = ParallelAgent(
        #     name="ParallelExtractionAgent",
        #     sub_agents=extraction_agents,
        #     description="Coordinates n parallel content extraction agents"
        # )

        # Initialize runner
        self.runner = None
        self.main_session = None
        
        # Store workflow results
        self.discovered_links = []
        self.extraction_results = []
        self.final_data = {}
    
    def convert_json(self, content: str) -> Dict[str, Any]:
        """Convert JSON content from string format."""
        if isinstance(content, str):
            if content.strip().startswith("```json") and content.strip().endswith("```"):
                json_content = content.strip()[7:-3].strip()
                try:
                    final_data = json.loads(json_content)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON content, using raw data")
                    final_data = content
                return final_data
            else:
                try:
                    final_data = json.loads(content)
                except json.JSONDecodeError:
                    final_data = content
                return final_data
        else:
            return content

    def split_links_into_batches(self, links: List[str], batch_size: int = 5) -> List[List[str]]:
        """Split links into batches of specified size."""
        batches = []
        if len(links) < batch_size:
            return [links]
        for i in range(0, len(links), batch_size):
            batch = links[i:i + batch_size]
            batches.append(batch)
        
        logger.info(f"📦 Split {len(links)} links into {len(batches)} batches of up to {batch_size} links each")
        return batches

    async def page_discovery(self, target_url: str, requirements: str) -> List[str]:
        """
            Phase 1: Page Discovery
            Discover all relevant links from the target website.
        
        Args:
            target_url: Target website URL
            requirements: Data extraction requirements
            
        Returns:
                List of discovered URLs
        """
        logger.info("📋 Phase 1: Page Discovery")
    
        # Create session
        self.main_session = await self.session_service.create_session(
            app_name=APP_NAME, 
            user_id=self.user_id, 
            session_id="parallel_extraction_session"
        )
    
        # Initialize runner with page discovery agent
        self.runner = Runner(
            agent=self.page_discovery_agent,
            app_name=APP_NAME,
            session_service=self.session_service
        )
    
        # Create user message
        user_message = types.Content(
            role='user',
            parts=[types.Part(text=f"Target URL: {target_url}\nRequirements: {requirements}")]
        )
    
        # Run page discovery
        async for event in self.runner.run_async(
            user_id=self.user_id, 
            session_id=self.main_session.id, 
            new_message=user_message
        ):
            if event.is_final_response():
                break
    
        # Get discovered links from session state
        updated_session = await self.session_service.get_session(
        app_name=APP_NAME, 
        user_id=self.user_id, 
            session_id=self.main_session.id
        )
    
        discovery_result = updated_session.state.get("discovered_links", {})
        if not discovery_result:
            raise ValueError("Page discovery failed: No links found")
    
        # Extract URLs from discovery_result string using regex
        url_pattern = r'https?://[^\s\'"<>]+'
        self.discovered_links = re.findall(url_pattern, discovery_result)

        logger.info(f"✅ Discovered {len(self.discovered_links)} links")
        return self.discovered_links

    async def parallel_extraction(self, requirements: str) -> List[Dict[str, Any]]:
        """
        Phase 2: Parallel Extraction in Batches
        Process discovered links in parallel batches.
        
        Args:
            requirements: Data extraction requirements
            
        Returns:
            List of extraction results
        """
        logger.info("⚡ Phase 2: Parallel Extraction in Batches")
    
        if not self.discovered_links:
            raise ValueError("No links available for extraction. Run page discovery first.")
        
        # Split links into batches of 5
        # link_batches = self.split_links_into_batches(self.discovered_links, self.batch_size)
        self.extraction_results = []

        # Switch runner to parallel extraction agent
        # self.runner.agent = self.parallel_extraction_agent
    
        # Process each batch
        for batch_idx, url in enumerate(self.discovered_links):
            batch_runner = Runner(
                agent=self.extraction_agent,
                app_name=APP_NAME,
                session_service=self.session_service
            )
            
            # Update progress at start of batch
            batch_progress = int((len(self.extraction_results) / len(self.discovered_links)) * 100)
            if self.progress_callback:
                await self.progress_callback(
                    self.user_id,
                    stage_index=1,
                    progress=batch_progress,
                    details=f"Extracted data from {len(self.extraction_results)} sources"
                )
            
            # Create new session for this batch
            batch_session = await self.session_service.create_session(
                app_name=APP_NAME,
                user_id=self.user_id,
                session_id=f"batch_session_{batch_idx}",
            )

            content = await web_crawl(url, return_format="markdown")
            
            # Create batch message
            message_text = f"Content: {content}\nRequirements: {requirements}"
            
            batch_message = types.Content(
                role='user',
                parts=[types.Part(text=message_text)]
            )
            
            # Run parallel extraction for this batch
            async for event in batch_runner.run_async(
                user_id=self.user_id,
                session_id=batch_session.id,
                new_message=batch_message,
            ):
                if event.is_final_response() and event.branch:
                    pass
                elif event.is_final_response() and not event.branch:
                    break

            # Collect results from this batch
            batch_result_session = await self.session_service.get_session(
                app_name=APP_NAME,
                user_id=self.user_id,
                session_id=batch_session.id
            )
            
            # Extract results from all agents
            batch_results = []
            agent_result = batch_result_session.state.get(f"extraction_result", {})
            if agent_result:
                converted_result = self.convert_json(agent_result)
                batch_results.append(converted_result)
            else:
                batch_results.append({"extracted_data": []})
            
            # logger.info("Waiting api rpm limit !!!")
            self.extraction_results.extend(batch_results)
            logger.info(f"✅ Batch {batch_idx + 1} completed: {len(batch_results)} successful extractions")

            # await asyncio.sleep(60)
    
        logger.info(f"🎯 Total extractions completed: {len(self.extraction_results)}")
        return self.extraction_results

    async def result_integration(self) -> Dict[str, Any]:
        """
        Phase 3: Result Integration
        Consolidate and format all extraction results.
        
        Returns:
            Integrated final data
        """
        logger.info("🔄 Phase 3: Result Integration")

        if not self.extraction_results:
            raise ValueError("No extraction results available for integration.")
        
        # Integrate all results
        self.final_data = {
            "integrated_data": [data_item for item in self.extraction_results if 'extracted_data' in item for data_item in item['extracted_data']]
        }
        
        logger.info(f"✅ Integration completed: {len(self.final_data.get('integrated_data', []))} items integrated")
        return self.final_data

    async def run_complete_workflow(self, target_url: str, requirements: str) -> Dict[str, Any]:
        """
        Run the complete parallel extraction workflow.
        
        Args:
            target_url: Target website URL
            requirements: Data extraction requirements
            
        Returns:
            Complete workflow results
        """
        logger.info(f"🚀 Starting parallel extraction workflow")
        logger.info(f"Target URL: {target_url}")
        logger.info(f"Requirements: {requirements}")
        
        try:
            # Phase 1: Page Discovery
            discovered_links = await self.page_discovery(target_url, requirements)
            
            # Phase 2: Parallel Extraction
            extraction_results = await self.parallel_extraction(requirements)
            
            # Phase 3: Result Integration
            final_data = await self.result_integration()
    
            # Compile workflow results
            workflow_result = {
                "status": "completed",
                "workflow_stages": {
                    "page_discovery": {
                        "links_discovered": len(discovered_links),
                        "discovered_links": discovered_links
                    },
                    "parallel_extraction": {
                        "total_batches": len(self.split_links_into_batches(discovered_links, self.batch_size)),
                        "total_extractions": len(extraction_results),
                        "extraction_results": extraction_results
                    },
                    "result_integration": final_data.get("integrated_data", {})
                },
                "final_data": final_data.get("integrated_data", {}),
                "metadata": {
                    "total_links_processed": len(discovered_links),
                    "total_batches": len(self.split_links_into_batches(discovered_links, self.batch_size)),
                    "successful_extractions": len(extraction_results),
                    "workflow_pattern": "discovery -> parallel_batches -> integration"
                }
            }
            
            logger.info(f"🎉 Workflow completed successfully")
            logger.info(f"Links processed: {len(discovered_links)}")
            logger.info(f"Successful extractions: {len(extraction_results)}")
            
            return workflow_result

        except Exception as e:
            logger.error(f"❌ Workflow failed: {str(e)}")
            raise


# Legacy function for backward compatibility
async def run_parallel_extraction_workflow(target_url: str, requirements: str, user_id: str = USER_ID, progress_callback=None) -> Dict[str, Any]:
    """
    Legacy function - use ParallelExtractionWorkflow class instead.
    
    Args:
        target_url: Target website URL
        requirements: Data extraction requirements
        user_id: User identifier (defaults to USER_ID constant)
        progress_callback: Optional callback function for progress updates
    """
    workflow = ParallelExtractionWorkflow(user_id, progress_callback)
    return await workflow.run_complete_workflow(target_url, requirements)


# Test function
async def test_parallel_extraction():
    """Test the parallel extraction workflow."""
    logger.info("🧪 Testing Parallel Extraction Workflow")
    
    test_url = "https://www.amazon.sg/s?k=rtx+4090"
    test_requirements = "Extract the following information from products on all pages: product name, current price, original price, image URL."
    
    try:
        workflow = ParallelExtractionWorkflow(USER_ID)
        result = await workflow.run_complete_workflow(test_url, test_requirements)
        
        logger.info("✅ Test completed successfully")
        logger.info(f"Status: {result['status']}")
        
        print("\n📊 Test Results:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_parallel_extraction()) 