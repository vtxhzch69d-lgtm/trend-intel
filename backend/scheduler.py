import asyncio
from datetime import datetime
from scrapers import ALL_SCRAPERS
from analysis.claude_analyzer import TrendAnalyzer
from database.db import AsyncSessionLocal
from database.models import Post, TrendReport
from sqlalchemy import select
import json
import os


async def scrape_all() -> list:
    all_posts = []
    for ScraperClass in ALL_SCRAPERS:
        try:
            async with ScraperClass() as scraper:
                posts = await scraper.get_hot_posts(limit=50)
                for p in posts:
                    p["source"] = scraper.source_name
                all_posts.extend(posts)
                print(f"[{scraper.source_name}] {len(posts)}개 수집")
        except Exception as e:
            print(f"[scraper] {ScraperClass.source_name} 실패: {e}")
    return all_posts


async def save_posts(posts: list):
    async with AsyncSessionLocal() as db:
        new_count = 0
        for p in posts:
            existing = await db.execute(
                select(Post).where(Post.post_id == p["post_id"])
            )
            if existing.scalar_one_or_none():
                continue
            db.add(Post(
                source=p.get("source", ""),
                post_id=p["post_id"],
                title=p["title"],
                category=p.get("category", ""),
                views=p.get("views", 0),
                comments=p.get("comments", 0),
                likes=p.get("likes", 0),
                url=p.get("url", ""),
                published_at=p.get("published_at"),
            ))
            new_count += 1
        await db.commit()
        print(f"[db] {new_count}개 신규 저장")


async def run_analysis(posts: list):
    if not posts:
        return
    analyzer = TrendAnalyzer()
    try:
        result = await analyzer.analyze_trends(posts)
        async with AsyncSessionLocal() as db:
            report = TrendReport(
                period_hours=24,
                keywords=result.get("keywords", []),
                trending_topics=result.get("trending_topics", []),
                sentiment_overview=result.get("sentiment_overview", {}),
                hot_posts=sorted(posts, key=lambda x: x.get("views", 0) + x.get("comments", 0) * 5, reverse=True)[:10],
                insights=result.get("narrative", ""),
                sources=result.get("sources", []),
            )
            db.add(report)
            await db.commit()
            print(f"[analysis] 리포트 저장 완료 (토픽 {len(result.get('trending_topics', []))}개)")
    except Exception as e:
        print(f"[analysis] 분석 실패: {e}")


async def full_pipeline():
    print(f"\n[pipeline] 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    posts = await scrape_all()
    print(f"[pipeline] 총 {len(posts)}개 수집")
    await save_posts(posts)
    await run_analysis(posts)
    print(f"[pipeline] 완료")
