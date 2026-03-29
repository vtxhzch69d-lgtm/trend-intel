from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
import os

from dotenv import load_dotenv
load_dotenv()

from database.db import init_db, get_db
from database.models import TrendReport, Post, Subscription
from scheduler import full_pipeline

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    interval = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "30"))
    scheduler.add_job(full_pipeline, "interval", minutes=interval, id="scrape_job")
    scheduler.start()
    print(f"[startup] 스케줄러 시작 (매 {interval}분)")
    # 시작 시 즉시 1회 실행
    import asyncio
    asyncio.create_task(full_pipeline())
    yield
    scheduler.shutdown()


app = FastAPI(
    title="트렌드인텔 API",
    description="한국 커뮤니티 트렌드 분석 플랫폼",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_key(x_api_key: str = Header(None)):
    secret = os.getenv("API_SECRET_KEY", "dev-secret")
    if x_api_key != secret:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ─── Public endpoints ────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/subscribe")
async def subscribe(email: str, company: str = "", db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Subscription).where(Subscription.email == email))
    if existing.scalar_one_or_none():
        return {"message": "이미 등록된 이메일입니다.", "status": "exists"}
    sub = Subscription(email=email, company=company, plan="trial")
    db.add(sub)
    await db.commit()
    return {"message": "등록 완료! 무료 트라이얼을 시작합니다.", "status": "created"}


# ─── Protected endpoints (API key required) ──────────────────────

@app.get("/reports/latest")
async def get_latest_report(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        select(TrendReport).order_by(desc(TrendReport.created_at)).limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="아직 분석 데이터가 없습니다.")
    return {
        "id": report.id,
        "created_at": report.created_at,
        "trending_topics": report.trending_topics,
        "keywords": report.keywords,
        "sentiment_overview": report.sentiment_overview,
        "hot_posts": report.hot_posts,
        "insights": report.insights,
        "sources": report.sources,
    }


@app.get("/reports")
async def list_reports(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        select(TrendReport).order_by(desc(TrendReport.created_at)).limit(limit)
    )
    reports = result.scalars().all()
    return [
        {
            "id": r.id,
            "created_at": r.created_at,
            "sources": r.sources,
            "topic_count": len(r.trending_topics or []),
            "sentiment_overview": r.sentiment_overview,
        }
        for r in reports
    ]


@app.get("/reports/{report_id}")
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(select(TrendReport).where(TrendReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
    return {
        "id": report.id,
        "created_at": report.created_at,
        "trending_topics": report.trending_topics,
        "keywords": report.keywords,
        "sentiment_overview": report.sentiment_overview,
        "hot_posts": report.hot_posts,
        "insights": report.insights,
        "sources": report.sources,
    }


@app.post("/trigger-analysis")
async def trigger_analysis(_: str = Depends(verify_api_key)):
    import asyncio
    asyncio.create_task(full_pipeline())
    return {"message": "분석 시작됨 (백그라운드 실행)"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
