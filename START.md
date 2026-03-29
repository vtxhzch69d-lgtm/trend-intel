# 트렌드인텔 - 빠른 시작 가이드

## 로컬 실행

### 1. 백엔드
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 입력
uvicorn main:app --reload --port 8000
```

### 2. 프론트엔드
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
# http://localhost:3000 접속
```

---

## 배포

### 백엔드 (Railway - 무료 시작)
1. railway.app 가입
2. 새 프로젝트 → GitHub 연결 → backend 폴더 선택
3. 환경변수 설정:
   - ANTHROPIC_API_KEY=sk-ant-...
   - API_SECRET_KEY=랜덤문자열
4. 배포 완료 → URL 복사 (예: https://trend-intel-backend.railway.app)

### 프론트엔드 (Vercel - 무료)
1. vercel.com 가입
2. 새 프로젝트 → GitHub 연결 → frontend 폴더 선택
3. 환경변수 설정:
   - NEXT_PUBLIC_API_URL=https://trend-intel-backend.railway.app
   - NEXT_PUBLIC_API_KEY=위에서 설정한 API_SECRET_KEY
4. 배포 완료

---

## 수익화 로드맵

### 1주차: MVP 완성
- [ ] 로컬 실행 확인
- [ ] 배포 완료
- [ ] 실제 분석 리포트 생성 확인

### 2주차: 첫 고객 확보
- [ ] 마케터 커뮤니티 (아이보스, 디지털마케팅 오픈카톡) 에 무료 리포트 공유
- [ ] "이런 서비스 써보실 분" 스레드 올리기
- [ ] 5명 무료 베타 모집

### 3주차: 피드백 반영 + 유료 전환
- [ ] 베타 사용자 피드백 수집
- [ ] 토스페이먼츠 또는 Stripe 결제 연동
- [ ] 유료 플랜 런칭

### 목표
- 1개월: 5명 유료 고객 (월 50만원)
- 3개월: 20명 (월 200만원)
- 6개월: 50명 (월 500만원+)
