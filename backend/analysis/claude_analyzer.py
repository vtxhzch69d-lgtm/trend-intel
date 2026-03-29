import httpx
import json
from typing import List, Dict
from datetime import datetime
import os

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


class TrendAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")

    async def analyze_trends(self, posts: List[Dict], custom_keywords: List[str] = None) -> Dict:
        if not posts:
            return self._empty_report()

        posts_text = self._format_posts(posts)
        keyword_instruction = ""
        if custom_keywords:
            kw_list = ", ".join(custom_keywords)
            keyword_instruction = f"\n특히 다음 키워드에 대한 언급/감성을 집중 분석해주세요: {kw_list}"

        prompt = f"""당신은 한국 온라인 커뮤니티 트렌드 분석 전문가입니다.
아래는 최근 뽐뿌, 클리앙 커뮤니티의 인기 게시글 목록입니다.
{keyword_instruction}

게시글 데이터:
{posts_text}

다음을 JSON 형식으로 분석해주세요:

{{
  "trending_topics": [
    {{
      "topic": "주제명",
      "summary": "2-3줄 요약",
      "post_count": 숫자,
      "sentiment": "positive/negative/neutral/mixed",
      "urgency": "high/medium/low"
    }}
  ],
  "keywords": [
    {{
      "keyword": "키워드",
      "count": 숫자,
      "sentiment": "positive/negative/neutral",
      "context": "어떤 맥락에서 언급되는지 한 줄 설명"
    }}
  ],
  "sentiment_overview": {{
    "positive": 숫자,
    "negative": 숫자,
    "neutral": 숫자,
    "overall_mood": "전반적인 커뮤니티 분위기 한 줄"
  }},
  "business_insights": [
    {{
      "insight": "비즈니스/마케터에게 유용한 인사이트",
      "action": "취할 수 있는 액션",
      "priority": "high/medium/low"
    }}
  ],
  "narrative": "전체 트렌드에 대한 3-5문단 분석 (마케터가 읽을 보고서 형식으로)"
}}

반드시 유효한 JSON만 출력하고 다른 텍스트는 포함하지 마세요."""

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        raw = data["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        result = json.loads(raw)
        result["analyzed_at"] = datetime.utcnow().isoformat()
        result["post_count"] = len(posts)
        result["sources"] = list({p.get("source", "unknown") for p in posts})
        return result

    def _format_posts(self, posts: List[Dict]) -> str:
        lines = []
        for i, post in enumerate(posts[:100], 1):
            lines.append(
                f"{i}. [{post.get('source','?')}][{post.get('category','?')}] "
                f"{post.get('title','제목없음')} "
                f"(조회:{post.get('views',0)} 댓글:{post.get('comments',0)} 좋아요:{post.get('likes',0)})"
            )
        return "\n".join(lines)

    def _empty_report(self) -> Dict:
        return {
            "trending_topics": [],
            "keywords": [],
            "sentiment_overview": {"positive": 33, "negative": 33, "neutral": 34, "overall_mood": "데이터 없음"},
            "business_insights": [],
            "narrative": "분석할 데이터가 없습니다.",
            "analyzed_at": datetime.utcnow().isoformat(),
            "post_count": 0,
            "sources": [],
        }
