"""Web crawling tool using Crawl4AI."""

import asyncio
from typing import Dict, List, Optional

from crawl4ai import AsyncWebCrawler
from loguru import logger

from core.config import settings


class WebCrawlTool:
    """Web crawling tool using Crawl4AI."""
    
    def __init__(self):
        self.crawler: Optional[AsyncWebCrawler] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.crawler = AsyncWebCrawler(
            verbose=settings.DEBUG,
            headless=True,
        )
        await self.crawler.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)
    
    async def crawl_single_page(self, url: str, return_format: str = "markdown") -> Dict[str, str]:
        """
        Crawl a single web page and return content in specified format.
        
        Args:
            url: Target URL to crawl
            return_format: Format to return ("html" or "markdown")
            
        Returns:
            Dictionary containing url and content in specified format
        """
        try:
            if not self.crawler:
                raise RuntimeError("Crawler not initialized. Use async context manager.")
            
            logger.info(f"Crawling URL: {url}")
            
            result = await self.crawler.arun(
                url=url,
                word_count_threshold=10,
                extraction_strategy="NoExtractionStrategy",
                chunking_strategy="NlpSentenceChunking",
                bypass_cache=True,
            )
            
            if not result.success:
                logger.error(f"Failed to crawl {url}: {result.error_message}")
                return {
                    "url": url,
                    "content": "",
                    "format": return_format,
                    "error": result.error_message or "Unknown error"
                }
            
            # Choose content based on return_format
            if return_format.lower() == "html":
                content = result.html
                content_type = "raw_html"
            else:  # default to markdown
                content = result.markdown
                content_type = "markdown"
            
            logger.info(f"Successfully crawled {url}, {content_type} length: {len(content)}")
            
            return {
                "url": url,
                "content": content,
                "format": return_format,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Exception while crawling {url}: {str(e)}")
            return {
                "url": url,
                "content": "",
                "format": return_format,
                "error": str(e)
            }
    
    async def crawl_multiple_pages(self, urls: List[str], return_format: str = "markdown") -> List[Dict[str, str]]:
        """
        Crawl multiple web pages concurrently.
        
        Args:
            urls: List of URLs to crawl
            return_format: Format to return ("html" or "markdown")
            
        Returns:
            List of dictionaries containing url and content in specified format
        """
        if not urls:
            return []
        
        logger.info(f"Crawling {len(urls)} URLs concurrently")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
        
        async def crawl_with_semaphore(url: str) -> Dict[str, str]:
            async with semaphore:
                return await self.crawl_single_page(url, return_format)
        
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Exception for URL {urls[i]}: {str(result)}")
                processed_results.append({
                    "url": urls[i],
                    "content": "",
                    "format": return_format,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        logger.info(f"Completed crawling {len(urls)} URLs")
        return processed_results


# ADK Tool Function
async def web_crawl(url: str, urls: Optional[List[str]] = None, return_format: str = "markdown") -> Dict:
    """
    ADK tool function for web crawling.
    
    Args:
        url: Single URL to crawl
        urls: List of URLs to crawl (optional)
        return_format: Format to return ("html" or "markdown")
        
    Returns:
        Crawling results
    """
    if not url and not urls:
        return {"error": "Either 'url' or 'urls' parameter must be provided"}
    
    async with WebCrawlTool() as crawler:
        if url:
            # Single URL crawling
            result = await crawler.crawl_single_page(url, return_format)
            return {"single_result": result}
        else:
            # Multiple URLs crawling
            results = await crawler.crawl_multiple_pages(urls, return_format)
            return {"multiple_results": results}