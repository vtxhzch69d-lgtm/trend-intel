from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from .base import BaseScraper
import re


class FMKoreaScraper(BaseScraper):
    source_name = "fmkorea"
    BASE_URL = "https://www.fmkorea.com"

    # 인기글 게시판 목록
    HOT_BOARDS = [
        "/index.php?mid=best",          # 베스트 게시물
        "/index.php?mid=humor_best",    # 유머 베스트
        "/index.php?mid=news",          # 뉴스
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
                print(f"[fmkorea] Error scraping {board_path}: {e}")
                continue
        return posts[:limit]

    def _parse_posts(self, html: str, board_path: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        posts = []

        for li in soup.select("ul.bd_lst li"):
            try:
                title_el = li.select_one("h3.title a, .title a")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                if not href:
                    continue

                post_id = re.search(r"srl=(\d+)", href)
                post_id = post_id.group(1) if post_id else href.split("/")[-1]

                views = self._parse_int(li.select_one(".m_no, .count"))
                comments = self._parse_int(li.select_one(".rCommentCount, .replyCount"))
                likes = self._parse_int(li.select_one(".voted_count"))
                category = li.select_one(".category")
                category = category.get_text(strip=True) if category else board_path.split("mid=")[-1]

                posts.append({
                    "post_id": f"fmkorea_{post_id}",
                    "title": title,
                    "category": category,
                    "views": views,
                    "comments": comments,
                    "likes": likes,
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
