"""Browser click tool using Playwright for ADK agents."""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright
from loguru import logger


async def click_and_get_url(url: str, click_selector: str) -> str:
    """
    Navigate to a URL, simulate a click on an element, and return the new URL using Playwright.
    
    Args:
        url: The target URL to navigate to
        click_selector: CSS selector for the element to click
        
    Returns:
        The new URL after the click action is completed
    """
    logger.info(f"🖱️ Clicking element '{click_selector}' on URL: {url}")
    
    async with async_playwright() as p:
        try:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # Create new page
            page = await browser.new_page()
            
            # Set viewport and user agent
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            
            # Navigate to the page
            logger.debug(f"Navigating to: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for the clickable element to be present
            logger.debug(f"Waiting for element: {click_selector}")
            await page.wait_for_selector(click_selector, timeout=10000)
            
            # Get original URL
            original_url = page.url
            logger.debug(f"Original URL: {original_url}")
            
            # Scroll element into view
            await page.locator(click_selector).scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            
            # Click the element
            logger.debug(f"Clicking element: {click_selector}")
            await page.locator(click_selector).click()
            
            # Wait for navigation to complete or timeout
            await page.wait_for_url(lambda url: url != original_url, timeout=8000)

            new_url = page.url           
            logger.debug(f"Final URL: {new_url}")
            
            # Close browser
            await browser.close()
            
            # Validate and return URL
            if new_url and new_url.startswith(('http://', 'https://')):
                if new_url != original_url:
                    logger.info(f"🎯 Click successful. New URL: {new_url}")
                    return new_url
                else:
                    logger.info(f"📍 URL unchanged after click: {original_url}")
                    return original_url
            else:
                logger.warning(f"⚠️ Invalid URL returned: {new_url}, using original URL")
                return original_url
                
        except Exception as e:
            logger.error(f"❌ Click operation failed: {str(e)}")
            # Make sure browser is closed
            try:
                await browser.close()
            except:
                pass
            return url

if __name__ == "__main__":
    print("🧪 Playwright Click Functionality Test")
    print("=" * 50)
    
    # Run the comprehensive test
    asyncio.run(click_and_get_url("https://chat4data.ai/playground", ".mantine-Pagination-control:nth-child(3)"))