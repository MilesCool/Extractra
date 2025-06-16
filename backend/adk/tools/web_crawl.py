"""Web crawling tool using Crawl4AI."""

import asyncio
from typing import Dict, List, Optional
import sys

from crawl4ai import AsyncWebCrawler, BrowserConfig
from loguru import logger

from core.config import settings

# This check is still useful but won't solve the core issue on its own.
if sys.platform.startswith('win'):
    # Using ProactorEventLoopPolicy here is not needed as the conflict is with the main app's loop.
    pass

class WebCrawlTool:
    """Synchronous wrapper for Crawl4AI to be run in a separate thread."""
    
    def __init__(self):
        # We will run the async crawler within a new event loop in a separate thread.
        pass

    def _run_crawl(self, urls: List[str], return_format: str = "markdown") -> List[Dict[str, str]]:
        """The actual crawling logic that will be run in a new event loop."""
        async def crawl_logic():
            browser_config = BrowserConfig(
                headless=True,
                verbose=settings.DEBUG,
                extra_args=[
                    '--no-sandbox', 
                    '--disable-dev-shm-usage',
                ]
            )
            # The crawler is now created and used entirely within this async function
            async with AsyncWebCrawler(config=browser_config) as crawler:
                tasks = [crawler.arun(url=url, word_count_threshold=10) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)

            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Exception for URL {urls[i]}: {str(result)}")
                    processed_results.append({"url": urls[i], "content": "", "error": str(result)})
                elif not result.success:
                    logger.error(f"Failed to crawl {urls[i]}: {result.error_message}")
                    processed_results.append({"url": urls[i], "content": "", "error": result.error_message})
                else:
                    content = result.html if return_format.lower() == "html" else result.markdown
                    processed_results.append({"url": urls[i], "content": content, "success": True})
            return processed_results

        # Run the async crawl_logic in a new event loop for this thread.
        return asyncio.run(crawl_logic())

    def crawl_pages(self, urls: List[str], return_format: str = "markdown") -> List[Dict[str, str]]:
        """Public synchronous method to be called from the main thread."""
        if not urls:
            return []
        
        logger.info(f"Starting crawl for {len(urls)} URLs in a separate thread.")
        results = self._run_crawl(urls, return_format)
        logger.info(f"Completed crawling {len(urls)} URLs in a separate thread.")
        return results

# ADK Tool Function
async def web_crawl(url: str, urls: Optional[List[str]] = None, return_format: str = "markdown") -> Dict:
    """
    ADK tool function for web crawling that runs the crawler in a separate thread.
    
    Args:
        url: Single URL to crawl
        urls: List of URLs to crawl (optional)
        return_format: Format to return ("html" or "markdown")
        
    Returns:
        Crawling results
    """
    if not url and not urls:
        return {"error": "Either 'url' or 'urls' parameter must be provided"}

    target_urls = urls if urls else [url]
    
    # Create an instance of the synchronous wrapper
    crawler = WebCrawlTool()

    try:
        # Run the blocking `crawl_pages` method in a separate thread
        # This avoids the NotImplementedError by not using the ProactorEventLoop for subprocesses.
        results = await asyncio.to_thread(crawler.crawl_pages, target_urls, return_format)
        
        if url:
            # If a single URL was passed, return a single result
            return {"single_result": results[0] if results else {"url": url, "error": "Crawl returned no result."}}
        else:
            # Otherwise, return all results
            return {"multiple_results": results}
            
    except Exception as e:
        logger.error(f"An unexpected error occurred in web_crawl tool: {e}")
        return {"error": f"Failed to execute crawl: {str(e)}"}