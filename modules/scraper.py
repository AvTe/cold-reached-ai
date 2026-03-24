import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from models import db, Business
from datetime import datetime

async def scrape_google_maps(search_query: str = None, url: str = None, max_results: int = 20):
    """
    Search and scrape business listings from Google Maps.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigation to target
        if url:
            target_url = url
        elif search_query:
            target_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        else:
            return []

        await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for the feed to appear
        try:
            await page.wait_for_selector('div[role="feed"]', timeout=20000)
        except:
            print("Feed container not found, attempting to scrape available articles.")

        listings_panel = page.locator('div[role="feed"]')
        
        # Scrolling logic to load more results
        results_count = 0
        scroll_attempts = 0
        while results_count < max_results and scroll_attempts < 15:
            # Check current number of items (Nv2PK is the standard card container)
            items = await page.locator('div.Nv2PK').all()
            results_count = len(items)
            
            # Scroll down the listings panel
            if await listings_panel.count() > 0:
                await listings_panel.hover()
                await page.mouse.wheel(0, 4000)
                await page.wait_for_timeout(2500) 
            else:
                # Fallback if role="feed" isn't found
                await page.mouse.wheel(0, 4000)
                await page.wait_for_timeout(2500)
            
            scroll_attempts += 1
            new_items = await page.locator('div.Nv2PK').all()
            if len(new_items) == results_count:
                # One more attempt for lazy loading
                await page.mouse.wheel(0, 5000)
                await page.wait_for_timeout(3000)
                if len(await page.locator('div.Nv2PK').all()) == results_count:
                    break
            results_count = len(new_items)

        # Final list of elements to extract from
        listing_elements = await page.locator('div.Nv2PK').all()
        scraped_data = []

        for element in listing_elements[:max_results]:
            try:
                # Get name from aria-label or specific text element
                # a.hfpxzc is the main clickable link for the listing
                link_element = element.locator('a.hfpxzc')
                name = await link_element.get_attribute('aria-label') if await link_element.count() > 0 else "Unknown Name"
                
                # Get Rating
                rating_element = element.locator('span.MW4etd')
                rating_text = await rating_element.inner_text() if await rating_element.count() > 0 else "0"
                try:
                    rating = float(rating_text.split(' ')[0].replace(',', '.'))
                except:
                    rating = 0.0

                # Click to get details
                await link_element.click()
                await page.wait_for_timeout(2000) # Wait for details panel
                
                # Extract details from the sidebar/details panel
                address_element = page.locator('button[data-item-id="address"]')
                address = await address_element.inner_text() if await address_element.count() > 0 else ""
                
                phone_element = page.locator('button[data-item-id*="phone:tel"]')
                phone = await phone_element.inner_text() if await phone_element.count() > 0 else ""
                
                website_element = page.locator('a[data-item-id="authority"]')
                website = await website_element.get_attribute('href') if await website_element.count() > 0 else ""

                scraped_data.append({
                    "name": name,
                    "address": address,
                    "phone": phone,
                    "website": website,
                    "rating": rating
                })
            except Exception as e:
                print(f"Error scraping individual listing: {e}")
                continue

        await browser.close()
        return scraped_data

def save_businesses(businesses_list, app):
    """
    Save list of business dictionaries to DB, skipping duplicates (name + address).
    """
    with app.app_context():
        new_entries = 0
        for data in businesses_list:
            # Define uniqueness by name + address combination
            existing = Business.query.filter_by(name=data['name'], address=data['address']).first()
            if not existing:
                new_business = Business(
                    name=data['name'],
                    address=data['address'],
                    phone=data['phone'],
                    website=data['website'],
                    rating=data['rating'],
                    scraped_at=datetime.utcnow()
                )
                db.session.add(new_business)
                new_entries += 1
        
        db.session.commit()
        return new_entries
