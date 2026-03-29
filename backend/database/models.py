from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)  # fmkorea, ppomppu, clien
    post_id = Column(String(100), nullable=False, unique=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    category = Column(String(100))
    views = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    url = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)


class TrendReport(Base):
    __tablename__ = "trend_reports"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    period_hours = Column(Integer, default=24)
    keywords = Column(JSON)        # [{"keyword": "...", "count": N, "sentiment": "positive/negative/neutral"}]
    trending_topics = Column(JSON)  # [{"topic": "...", "summary": "...", "post_count": N}]
    sentiment_overview = Column(JSON)  # {"positive": %, "negative": %, "neutral": %}
    hot_posts = Column(JSON)       # top posts by engagement
    insights = Column(Text)        # Claude's narrative summary
    sources = Column(JSON)         # which communities included


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False, unique=True)
    company = Column(String(200))
    plan = Column(String(50), default="trial")  # trial, basic, pro
    keywords = Column(JSON)  # custom keywords to track
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Integer, default=1)
