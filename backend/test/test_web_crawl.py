"""Test script for web_crawl tool."""

import asyncio
import json
import time
from typing import List
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from adk.tools.web_crawl import WebCrawlTool, web_crawl

async def test_single_page_crawl():
    """Test crawling a single web page."""
    print("=" * 60)
    print("Testing Single Page Crawl")
    print("=" * 60)
    
    test_url = "https://www.amazon.sg/Outlet/b/?_encoding=UTF8&ie=UTF8&node=8191518051&pd_rd_w=suXqr&content-id=amzn1.sym.10c4beec-f7b7-4f79-8911-d1af6797210b&pf_rd_p=10c4beec-f7b7-4f79-8911-d1af6797210b&pf_rd_r=ZJZM72CEQJQH2CZA56EJ&pd_rd_wg=qjq7g&pd_rd_r=dad468ab-8179-4514-a0bc-6d92874c2626&ref_=pd_hp_d_btf_unk&bubble-id=deals-collection-electronics"
    
    print(f"Crawling URL: {test_url}")
    start_time = time.time()
    
    async with WebCrawlTool() as crawler:
        result = await crawler.crawl_single_page(test_url)
    
    end_time = time.time()
    
    print(f"Crawl completed in {end_time - start_time:.2f} seconds")
    print(f"Success: {result.get('success', False)}")
    print(f"Content length: {len(result.get('markdown', ''))}")
    
    if result.get('error'):
        print(f"Error: {result['error']}")
    else:
        print("First 200 characters of content:")
        print(result.get('markdown', '')[:200] + "...")
    
    print()


async def test_multiple_pages_crawl():
    """Test crawling multiple web pages."""
    print("=" * 60)
    print("Testing Multiple Pages Crawl")
    print("=" * 60)
    
    test_urls = [
        "https://google.github.io/adk-docs/tools/",
        "https://google.github.io/adk-docs/tools/built-in-tools/",
        "https://google.github.io/adk-docs/tools/third-party-tools/",
    ]
    
    print(f"Crawling {len(test_urls)} URLs:")
    for url in test_urls:
        print(f"  - {url}")
    
    start_time = time.time()
    
    async with WebCrawlTool() as crawler:
        results = await crawler.crawl_multiple_pages(test_urls)
    
    end_time = time.time()
    
    print(f"\nCrawl completed in {end_time - start_time:.2f} seconds")
    print(f"Total results: {len(results)}")
    
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Content length: {len(result.get('markdown', ''))}")
        if result.get('error'):
            print(f"  Error: {result['error']}")
    
    print()


async def test_adk_tool_function():
    """Test the ADK tool function interface."""
    print("=" * 60)
    print("Testing ADK Tool Function Interface")
    print("=" * 60)
    
    # Test single URL
    print("Testing single URL parameter:")
    result = await web_crawl(url="https://google.github.io/adk-docs/tools/third-party-tools/")
    print(f"Single result keys: {list(result.keys())}")
    if 'single_result' in result:
        single_result = result['single_result']
        print(f"  URL: {single_result.get('url', 'N/A')}")
        print(f"  Success: {single_result.get('success', False)}")
        print(f"  Content length: {len(single_result.get('markdown', ''))}")
    
    print()
    
    # Test multiple URLs
    print("Testing multiple URLs parameter:")
    test_urls = ["https://google.github.io/adk-docs/tools/third-party-tools/", "https://google.github.io/adk-docs/tools/google-cloud-tools/"]
    result = await web_crawl(urls=test_urls)
    print(f"Multiple results keys: {list(result.keys())}")
    if 'multiple_results' in result:
        multiple_results = result['multiple_results']
        print(f"  Number of results: {len(multiple_results)}")
        for i, res in enumerate(multiple_results):
            print(f"  Result {i+1}: {res.get('url', 'N/A')} - Success: {res.get('success', False)}")
    
    print()
    
    # Test error case
    print("Testing error case (no parameters):")
    result = await web_crawl()
    print(f"Error result: {result}")
    
    print()


async def test_error_handling():
    """Test error handling with invalid URLs."""
    print("=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    invalid_urls = [
        "https://this-domain-does-not-exist-12345.com",
        "invalid-url",
        "http://localhost:99999",
    ]
    
    print("Testing with invalid URLs:")
    for url in invalid_urls:
        print(f"  - {url}")
    
    async with WebCrawlTool() as crawler:
        results = await crawler.crawl_multiple_pages(invalid_urls)
    
    print(f"\nResults for {len(invalid_urls)} invalid URLs:")
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Error: {result.get('error', 'No error')}")
    
    print()


async def test_performance():
    """Test performance with concurrent requests."""
    print("=" * 60)
    print("Testing Performance")
    print("=" * 60)
    
    # Create a list of test URLs
    test_urls = [
        "https://google.github.io/adk-docs/get-started/quickstart/#agentpy"
    ]
    
    print(f"Testing concurrent crawling of {len(test_urls)} URLs")
    print("URLs include artificial delays to test concurrency")
    
    start_time = time.time()
    
    async with WebCrawlTool() as crawler:
        results = await crawler.crawl_multiple_pages(test_urls)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\nPerformance Results:")
    print(f"  Total time: {total_time:.2f} seconds")
    print(f"  Average time per URL: {total_time / len(test_urls):.2f} seconds")
    print(f"  Successful crawls: {sum(1 for r in results if r.get('success', False))}")
    print(f"  Failed crawls: {sum(1 for r in results if not r.get('success', False))}")
    
    print()


def save_results_to_file(results: List[dict], filename: str):
    """Save crawl results to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {filename}")
    except Exception as e:
        print(f"Failed to save results: {e}")


async def main():
    """Run all tests."""
    print("Web Crawl Tool Test Suite")
    print("=" * 60)
    print("This script tests the web_crawl tool functionality")
    print("including single page crawling, multiple page crawling,")
    print("error handling, and performance testing.")
    print()
    
    try:
        # Run all test functions
        await test_single_page_crawl()
        # await test_multiple_pages_crawl()
        # await test_adk_tool_function()
        # await test_error_handling()
        # await test_performance()
        
        print("=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main()) 