"""Web crawling tool using Crawl4AI."""

import asyncio
from typing import Dict, List, Optional
import sys

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
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

    def _create_crawler_config(self, content_filter: str = "pruning") -> CrawlerRunConfig:
        """Create optimized crawler configuration with content filtering."""

        # Configure content filter based on strategy
        if content_filter == "pruning":
            # Use pruning filter to remove boilerplate content
            filter_strategy = PruningContentFilter(
                user_query="products",
                threshold=0.45,  # Less aggressive pruning to keep more content
                min_word_threshold=15,  # Lower minimum words per block
            )
        elif content_filter == "bm25":
            # Use BM25 for query-based filtering (if we had a query)
            filter_strategy = BM25ContentFilter(
                user_query="div",  # Broader query
                bm25_threshold=0.6,  # Lower threshold for more content
                language="english"
            )
        else:
            filter_strategy = None
        
        # Configure markdown generator with optimized options
        md_generator = DefaultMarkdownGenerator(
            content_source="raw_html",  # Use cleaned HTML for better content
            content_filter=filter_strategy,
            options={
                "ignore_links": False,  # Keep links in markdown
                "ignore_images": False,  # Keep images in markdown
                "escape_html": False,
                "body_width": 0,  # No line wrapping
                "skip_internal_links": False,  # Keep internal links for deep crawling
                "include_sup_sub": False,  # Skip superscript/subscript for simplicity
                "mark_code": True,  # Preserve code blocks
                "include_links": True,  # Include link references
            }
        )
        
        return CrawlerRunConfig(
            markdown_generator=md_generator,
            word_count_threshold=30,  # Lower minimum word count
            only_text=False,  # We want structured content
            scan_full_page=True,
        )

    def _run_crawl(self, urls: List[str], return_format: str = "markdown", content_filter: str = "pruning") -> List[Dict[str, str]]:
        """The actual crawling logic that will be run in a new event loop."""
        async def crawl_logic():
            browser_config = BrowserConfig(
                headless=True,
                verbose=settings.DEBUG,
                extra_args=[
                    '--no-sandbox', 
                    '--disable-dev-shm-usage',
                    '--window-size=1920,1080',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            # Create optimized crawler configuration
            crawler_config = self._create_crawler_config(content_filter)
            
            # The crawler is now created and used entirely within this async function
            async with AsyncWebCrawler(config=browser_config) as crawler:
                tasks = []
                for url in urls:
                    # Use the optimized configuration
                    task = crawler.arun(
                        url=url, 
                        config=crawler_config,
                    )
                    tasks.append(task)
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
                    # Choose content based on format and availability
                    if return_format.lower() == "html":
                        content = result.html
                    else:
                        # Prefer fit_markdown (filtered) over raw markdown
                        content = result.markdown.raw_markdown
                        logger.info(f"Using raw markdown for {urls[i]}, length: {len(content)}")

                    # Check for robot verification or CAPTCHA
                    robot_indicators = [
                        "verify that you're not a robot",
                        "captcha",
                        "cloudflare",
                        "access denied",
                        "blocked",
                        "security check",
                        "unusual traffic"
                    ]
                    
                    content_lower = content.lower()
                    if any(indicator in content_lower for indicator in robot_indicators):
                        logger.warning(f"Robot verification detected for URL {urls[i]}")
                        processed_results.append({
                            "url": urls[i], 
                            "content": "", 
                            "error": "Robot verification required - content blocked by anti-bot protection"
                        })
                    else:
                        processed_results.append({
                            "url": urls[i], 
                            "content": content, 
                            "success": True,
                        })
            return processed_results

        # Run the async crawl_logic in a new event loop for this thread.
        return asyncio.run(crawl_logic())

    def crawl_pages(self, urls: List[str], return_format: str = "markdown", content_filter: str = "pruning") -> List[Dict[str, str]]:
        """Public synchronous method to be called from the main thread."""
        if not urls:
            return []
        
        logger.info(f"Starting crawl for {len(urls)} URLs with {content_filter} filter")
        results = self._run_crawl(urls, return_format, content_filter)
        logger.info(f"Completed crawling {len(urls)} URLs in a separate thread.")
        return results

# ADK Tool Function
async def web_crawl(
    url: str, 
    urls: Optional[List[str]] = None, 
    return_format: str = "markdown",
    content_filter: str = "none"
):
    """
    ADK tool function for web crawling that runs the crawler in a separate thread.
    
    Args:
        url: Single URL to crawl
        urls: List of URLs to crawl (optional)
        return_format: Format to return ("html" or "markdown")
        content_filter: Content filtering strategy ("pruning", "bm25", or "none")
        
    Returns:
        Crawling results with optimized content, including URLs and media in markdown format
    """
    if not url and not urls:
        return {"error": "Either 'url' or 'urls' parameter must be provided"}

    target_urls = urls if urls else [url]
    
    # Create an instance of the synchronous wrapper
    crawler = WebCrawlTool()

    try:
        # Run the blocking `crawl_pages` method in a separate thread
        # This avoids the NotImplementedError by not using the ProactorEventLoop for subprocesses.
        results = await asyncio.to_thread(
            crawler.crawl_pages, 
            target_urls, 
            return_format, 
            content_filter
        )
        
        if url:
            # If a single URL was passed, return a single result
            return {"single_result": results[0] if results else {"url": url, "error": "Crawl returned no result."}}
        else:
            # Otherwise, return all results
            return {"multiple_results": results}
            
    except Exception as e:
        logger.error(f"An unexpected error occurred in web_crawl tool: {e}")
        return {"error": f"Failed to execute crawl: {str(e)}"}