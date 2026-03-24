import asyncio
from modules.scraper import scrape_google_maps

async def test():
    print("Testing Keyword Search...")
    data = await scrape_google_maps(search_query="cafes in bangalore", max_results=5)
    print(f"Keyword search returned {len(data)} results.")
    for d in data:
        print(d["name"])

if __name__ == "__main__":
    asyncio.run(test())
