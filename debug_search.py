import asyncio
from playwright.async_api import async_playwright

async def debug_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.google.com/maps/search/cafes+in+bangalore", wait_until="networkidle")
        
        title = await page.title()
        content = await page.content()
        
        if "Before you continue" in content or "Accept all" in content:
            print("CONSENT SCREEN DETECTED!")
        else:
            print(f"Page loaded properly. Title: {title}")
        
        # Check if feed exists
        feed = await page.locator('div[role="feed"]').count()
        print(f"Feed found: {feed}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_search())
