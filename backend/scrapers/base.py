import httpx
from abc import ABC, abstractmethod
from typing import List, Dict
import asyncio
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}


class BaseScraper(ABC):
    source_name: str = ""

    def __init__(self):
        self.client = httpx.AsyncClient(
            headers=HEADERS,
            timeout=15.0,
            follow_redirects=True,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def fetch(self, url: str) -> str:
        await asyncio.sleep(random.uniform(0.5, 1.5))  # polite delay
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.text

    @abstractmethod
    async def get_hot_posts(self, limit: int = 50) -> List[Dict]:
        """
        Returns list of dicts:
        {
            "post_id": str,
            "title": str,
            "category": str,
            "views": int,
            "comments": int,
            "likes": int,
            "url": str,
            "published_at": datetime | None,
        }
        """
        pass
