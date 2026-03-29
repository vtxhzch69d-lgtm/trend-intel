from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from .base import BaseScraper
import re


class ClienScraper(BaseScraper):
    source_name = "clien"
    BASE_URL = "https://www.clien.net"

    HOT_BOARDS = [
        "/service/board/park",       # 공원 (핫딜/자유)
        "/service/board/cm_humor",   # 유머
        "/service/board/news",       # 뉴스
    ]

    async def get_hot_posts(self, limit: int = 50) -> List[Dict]:
        posts = []
        for board_path in self.HOT_BOARDS:
            try:
                url = self.BASE_URL + board_path
                html = await self.fetch(url)
                board_posts = self._parse_posts(html, board_path)
                posts.extend(board_posts)
                if len(posts) >= limit:
                    break
            except Exception as e:
                print(f"[clien] Error scraping {board_path}: {e}")
                continue
        return posts[:limit]

    def _parse_posts(self, html: str, board_path: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        posts = []
        board_name = board_path.split("/")[-1]

        for row in soup.select("div.list_item, .symph-row"):
            try:
                title_el = row.select_one("span.subject_fixed, .list-subject .subject_fixed, a.subject_fixed")
                if not title_el:
                    title_el = row.select_one(".list_subject a, .subject a")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                if not title:
                    continue

                link_el = row.select_one("a.list_subject, a[href*='/service/board/']")
                href = link_el.get("href", "") if link_el else ""
                post_id = href.split("/")[-1].split("?")[0]

                views_el = row.select_one(".hit, .list_hit")
                likes_el = row.select_one(".symph_cnt, .list_symph")
                comments_el = row.select_one(".reply_symph, .list_reply")

                posts.append({
                    "post_id": f"clien_{post_id}",
                    "title": title,
                    "category": board_name,
                    "views": self._parse_int(views_el),
                    "comments": self._parse_int(comments_el),
                    "likes": self._parse_int(likes_el),
                    "url": self.BASE_URL + href if href.startswith("/") else href,
                    "published_at": None,
                })
            except Exception:
                continue
        return posts

    def _parse_int(self, el) -> int:
        if not el:
            return 0
        text = re.sub(r"[^\d]", "", el.get_text())
        return int(text) if text else 0
