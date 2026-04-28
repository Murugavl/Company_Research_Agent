import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="backend/.env")

async def test_tavily_images():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("TAVILY_API_KEY not found")
        return

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": "Google company logo and headquarters images",
        "include_answer": True,
        "include_images": True,
        "max_results": 5
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, timeout=20.0)
            res.raise_for_status()
            data = res.json()
            print(f"Images found: {len(data.get('images', []))}")
            for img in data.get('images', []):
                print(f" - {img}")
        except Exception as e:
            print(f"Tavily search failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_tavily_images())
