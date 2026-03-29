from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from .base import BaseScraper
import re


class PpomppuScraper(BaseScraper):
    source_name = "ppomppu"
    BASE_URL = "https://www.ppomppu.co.kr"

    HOT_BOARDS = [
        "/zboard/zboard.php?id=freeboard",   # 자유게시판
        "/zboard/zboard.php?id=issue",        # 이슈
        "/zboard/zboard.php?id=economy",      # 경제
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
                print(f"[ppomppu] Error scraping {board_path}: {e}")
                continue
        return posts[:limit]

    def _parse_posts(self, html: str, board_path: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        posts = []
        board_id = re.search(r"id=(\w+)", board_path)
        board_id = board_id.group(1) if board_id else "unknown"

        rows = soup.select("tr.baseList, tr.cLine0, tr.cLine1")
        for row in rows:
            try:
                title_el = row.select_one("a.baseList-title, .title a, td.baseList-title a")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                if not title or len(title) < 2:
                    continue

                href = title_el.get("href", "")
                post_no = re.search(r"no=(\d+)", href)
                post_id = post_no.group(1) if post_no else href

                cells = row.find_all("td")
                views = 0
                comments = 0
                for cell in cells:
                    text = cell.get_text(strip=True)
                    if text.isdigit():
                        val = int(text)
                        if val > views:
                            views = val

                comment_el = title_el.find_next("span", class_="replyCount")
                if comment_el:
                    comments = self._parse_int(comment_el)

                full_url = self.BASE_URL + "/" + href.lstrip("/") if not href.startswith("http") else href

                posts.append({
                    "post_id": f"ppomppu_{post_id}",
                    "title": title,
                    "category": board_id,
                    "views": views,
                    "comments": comments,
                    "likes": 0,
                    "url": full_url,
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
