"""GitHub Actions에서 실행되는 스크래핑+분석 스크립트"""
import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import re

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


# ── 스크래퍼 ────────────────────────────────────────────

async def scrape_ppomppu(client):
    posts = []
    for board in ["freeboard", "issue", "economy"]:
        try:
            r = await client.get(f"https://www.ppomppu.co.kr/zboard/zboard.php?id={board}")
            soup = BeautifulSoup(r.text, "lxml")
            for row in soup.select("tr.baseList, tr.cLine0, tr.cLine1"):
                title_el = row.select_one("a.baseList-title, .title a, td.baseList-title a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 2:
                    continue
                href = title_el.get("href", "")
                cells = row.find_all("td")
                views = max((int(re.sub(r"[^\d]","",c.get_text())) for c in cells if re.sub(r"[^\d]","",c.get_text()).isdigit() and int(re.sub(r"[^\d]","",c.get_text())) > 10), default=0)
                posts.append({"source":"ppomppu","category":board,"title":title,"views":views,"comments":0,"likes":0,"url":"https://www.ppomppu.co.kr/"+href.lstrip("/")})
        except Exception as e:
            print(f"ppomppu/{board} 오류: {e}")
        await asyncio.sleep(1)
    return posts


async def scrape_clien(client):
    posts = []
    for board in ["park", "cm_humor", "news"]:
        try:
            r = await client.get(f"https://www.clien.net/service/board/{board}")
            soup = BeautifulSoup(r.text, "lxml")
            for row in soup.select("div.list_item, .symph-row"):
                title_el = row.select_one("span.subject_fixed, .list_subject .subject_fixed")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue
                link_el = row.select_one("a.list_subject, a[href*='/service/board/']")
                href = link_el.get("href", "") if link_el else ""
                views_el = row.select_one(".hit, .list_hit")
                views = int(re.sub(r"[^\d]","",views_el.get_text())) if views_el and re.sub(r"[^\d]","",views_el.get_text()) else 0
                posts.append({"source":"clien","category":board,"title":title,"views":views,"comments":0,"likes":0,"url":"https://www.clien.net"+href if href.startswith("/") else href})
        except Exception as e:
            print(f"clien/{board} 오류: {e}")
        await asyncio.sleep(1)
    return posts


async def scrape_all():
    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0, follow_redirects=True) as client:
        ppomppu = await scrape_ppomppu(client)
        clien = await scrape_clien(client)
    posts = ppomppu + clien
    print(f"수집 완료: {len(posts)}개 (ppomppu:{len(ppomppu)} clien:{len(clien)})")
    return posts


# ── AI 분석 ────────────────────────────────────────────

async def analyze(posts):
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("GROQ_API_KEY 없음 - 분석 스킵")
        return None

    lines = []
    for i, p in enumerate(posts[:80], 1):
        lines.append(f"{i}. [{p['source']}][{p['category']}] {p['title']} (조회:{p['views']})")
    posts_text = "\n".join(lines)

    prompt = f"""당신은 한국 온라인 커뮤니티 트렌드 분석 전문가입니다.
아래는 뽐뿌, 클리앙 커뮤니티의 인기 게시글입니다.

{posts_text}

JSON 형식으로 분석해주세요:
{{
  "trending_topics": [{{"topic":"주제","summary":"2줄 요약","post_count":숫자,"sentiment":"positive/negative/neutral/mixed","urgency":"high/medium/low"}}],
  "keywords": [{{"keyword":"키워드","count":숫자,"sentiment":"positive/negative/neutral","context":"한줄설명"}}],
  "sentiment_overview": {{"positive":숫자,"negative":숫자,"neutral":숫자,"overall_mood":"한줄"}},
  "business_insights": [{{"insight":"인사이트","action":"액션","priority":"high/medium/low"}}],
  "narrative": "3-5문단 마케터용 분석 보고서"
}}
JSON만 출력하세요."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": GROQ_MODEL, "messages": [{"role":"user","content":prompt}], "temperature":0.3, "max_tokens":4096}
        )
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"].strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()
    return json.loads(raw)


# ── 저장 ────────────────────────────────────────────────

async def main():
    posts = await scrape_all()
    if not posts:
        print("수집된 게시글 없음")
        sys.exit(1)

    result = await analyze(posts)
    if not result:
        sys.exit(1)

    result["analyzed_at"] = datetime.utcnow().isoformat()
    result["post_count"] = len(posts)
    result["sources"] = list({p["source"] for p in posts})

    # 최신 리포트 저장
    (DATA_DIR / "latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))

    # 히스토리 저장 (최근 48개 = 24시간)
    history_file = DATA_DIR / "history.json"
    history = json.loads(history_file.read_text()) if history_file.exists() else []
    history.insert(0, {
        "analyzed_at": result["analyzed_at"],
        "sentiment_overview": result["sentiment_overview"],
        "topic_count": len(result.get("trending_topics", [])),
        "sources": result["sources"],
    })
    history = history[:48]
    history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2))

    print(f"저장 완료: data/latest.json")
    print(f"토픽: {len(result.get('trending_topics',[]))}개")
    for t in result.get("trending_topics", [])[:3]:
        print(f"  [{t['urgency']}] {t['topic']}")


if __name__ == "__main__":
    asyncio.run(main())
