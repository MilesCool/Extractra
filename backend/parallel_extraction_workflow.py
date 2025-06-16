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
from typing import List, Dict, Any

from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from loguru import logger

from adk.agents import create_extraction_agent, create_page_discovery_agent
from core.config import settings

# Constants
APP_NAME = "extractra_parallel_workflow"
USER_ID = "user_1"
MODEL = settings.GEMINI_MODEL
        
# Page Discovery Agent
page_discovery_agent = create_page_discovery_agent("discovered_links")

# Create 2 parallel extraction agents
extraction_agents = [create_extraction_agent(i) for i in range(1, 3)]

parallel_extraction_agent = ParallelAgent(
    name="ParallelExtractionAgent",
    sub_agents=extraction_agents,
    description="Coordinates n parallel content extraction agents"
)

def convert_json(content: str) -> Dict[str, Any]:
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
            # Try to parse as JSON directly
            try:
                final_data = json.loads(content)
            except json.JSONDecodeError:
                final_data = content

            return final_data
    else:
        return content

def split_links_into_batches(links: List[str], batch_size: int = 2) -> List[List[str]]:
    """Split links into batches of specified size."""
    batches = []
    if len(links) < batch_size:
        return [links]
    for i in range(0, len(links), batch_size):
        batch = links[i:i + batch_size]
        batches.append(batch)
    
    logger.info(f"📦 Split {len(links)} links into {len(batches)} batches of up to {batch_size} links each")
    return batches


async def run_parallel_extraction_workflow(target_url: str, requirements: str) -> Dict[str, Any]:
    """
    Run the complete parallel extraction workflow using Runner agent switching.
    
    Args:
        target_url: Target website URL
        requirements: Data extraction requirements
        
    Returns:
        Complete extraction results
    """
    logger.info(f"🚀 Starting parallel extraction workflow")
    logger.info(f"Target URL: {target_url}")
    logger.info(f"Requirements: {requirements}")
    
    # Initialize services
    session_service = InMemorySessionService()
    
    # Create session
    session = await session_service.create_session(
        app_name=APP_NAME, 
        user_id=USER_ID, 
        session_id="parallel_extraction_session"
    )
    
    # Initialize runner with page discovery agent
    runner = Runner(
        agent=page_discovery_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    
    # Phase 1: Page Discovery
    logger.info("📋 Phase 1: Page Discovery")
    user_message = types.Content(
        role='user',
        parts=[types.Part(text=f"Target URL: {target_url}\nRequirements: {requirements}")]
    )
    
    # Run page discovery
    async for event in runner.run_async(
        user_id=USER_ID, 
        session_id=session.id, 
        new_message=user_message
    ):
        if event.is_final_response():
            break
    
    # Get discovered links from session state
    updated_session = await session_service.get_session(
        app_name=APP_NAME, 
        user_id=USER_ID, 
        session_id=session.id
    )
    
    discovery_result = updated_session.state.get("discovered_links", {})
    if not discovery_result:
        raise ValueError("Page discovery failed: No links found")
    
    import re
    
    # Extract URLs from discovery_result string using regex
    url_pattern = r'https?://[^\s\'"<>]+'
    discovered_links = re.findall(url_pattern, discovery_result)

    logger.info(f"✅ Discovered {len(discovered_links)} links")
    
    # Phase 2: Parallel Extraction in Batches
    logger.info("⚡ Phase 2: Parallel Extraction in Batches")
    
    # Split links into batches of 2
    link_batches = split_links_into_batches(discovered_links, 2)
    all_extraction_results = []

    # Parallel extraction coordinator
    runner.agent = parallel_extraction_agent
    
    # Process each batch
    for batch_idx, batch_urls in enumerate(link_batches):
        logger.info(f"🔄 Processing batch {batch_idx + 1}/{len(link_batches)} with {len(batch_urls)} URLs")
        
        # Create new session for this batch
        batch_session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=f"batch_session_{batch_idx}",
        )
        
        # Create batch message
        batch_message = types.Content(
            role='user',
            parts=[types.Part(text=f"URLs: {json.dumps(batch_urls)}\nRequirements: {requirements}")]
        )
        
        # Run parallel extraction for this batch with retry mechanism
        # max_retries = 3
        # retry_count = 0

        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=batch_session.id,
            new_message=batch_message,
        ):
            if event.is_final_response() and event.branch:
                pass
            elif event.is_final_response() and not event.branch:
                break

        # while retry_count < max_retries:
        #     try:
        #         break  # Success, exit retry loop
        #     except Exception as e:
        #         retry_count += 1
        #         await asyncio.sleep(3)
        #         if retry_count > max_retries:
        #             logger.error(f"❌ Batch {batch_idx + 1} failed after {max_retries} retries: {str(e)}")
        #             raise
        #         else:
        #             logger.warning(f"⚠️ Batch {batch_idx + 1} attempt {retry_count} failed, retrying: {str(e)}")
        
        # Collect results from this batch
        batch_result_session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=batch_session.id
        )
        
        # Extract results from all 2 agents
        batch_results = []
        for i in range(1, len(batch_urls) + 1):
            agent_result = batch_result_session.state.get(f"extraction_result_{i}", {})
            if agent_result:
                converted_result = convert_json(agent_result)
                batch_results.append(converted_result)
        
        all_extraction_results.extend(batch_results)
        logger.info(f"✅ Batch {batch_idx + 1} completed: {len(batch_results)} successful extractions")
    
    logger.info(f"🎯 Total extractions completed: {len(all_extraction_results)}")
    
    # Phase 3: Result Integration
    logger.info("🔄 Phase 3: Result Integration")

    final_data = {
        "integrated_data": [item['extracted_data'] for item in all_extraction_results]
    }
    
    # Compile workflow results
    workflow_result = {
        "status": "completed",
        "workflow_stages": {
            "page_discovery": {
                "links_discovered": len(discovered_links),
                "discovery_result": discovery_result
            },
            "parallel_extraction": {
                "total_batches": len(link_batches),
                "total_extractions": len(all_extraction_results),
                "extraction_results": all_extraction_results
            },
            "result_integration": final_data.get("integrated_data", {})
        },
        "final_data": final_data.get("integrated_data", {}),
        "metadata": {
            "total_links_processed": len(discovered_links),
            "total_batches": len(link_batches),
            "successful_extractions": len(all_extraction_results),
            "workflow_pattern": "discovery -> parallel_batches -> integration"
        }
    }
    
    logger.info(f"🎉 Workflow completed successfully")
    logger.info(f"Links processed: {len(discovered_links)}")
    logger.info(f"Successful extractions: {len(all_extraction_results)}")
    
    return workflow_result


# Test function
async def test_parallel_extraction():
    """Test the parallel extraction workflow."""
    logger.info("🧪 Testing Parallel Extraction Workflow")
    
    test_url = "https://chat4data.ai/playground"
    test_requirements = "Extract the following information from products on all pages: product name, current price, original price, image URL, visible comments, and hidden comments."
    
    try:
        result = await run_parallel_extraction_workflow(test_url, test_requirements)
        
        logger.info("✅ Test completed successfully")
        logger.info(f"Status: {result['status']}")
        
        print("\n📊 Test Results:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_parallel_extraction()) 