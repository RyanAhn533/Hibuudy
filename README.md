# Hi-Buddy · 발달장애인 자립생활 지원 AI 앱

> AI 기반 하루 일정 관리 앱 — 발달장애인 당사자가 혼자서도 하루를 보낼 수 있도록 돕는 코디네이터-사용자 분리형 스케줄러

---

## 스토리

### 1단계 — 서울청년기획봉사단 온쉐어 (2025.03 ~ 08)

서울청년기획봉사단 온쉐어 팀장으로 팀원들을 이끌며, 발달장애인을 위한 AI 요리 챗봇 **온쿡(OnCook)** 을 단독 개발했습니다.

- 서부장애인종합복지관 자립주거팀 발달장애인 5명 대상 쿠킹클래스 2회 진행
- LG Hello Vision 기업 연계 지원금 수령, **헬로TV 뉴스 취재 및 방송 출연**
- 참여자 만족도 **4.83 / 5점** · SNS 조회수 **16,000회 이상**

### 2단계 — 연세대학교에서 연락이 옴 (2025.12)

봉사단 활동 결과를 본 **연세대학교 사회복지대학원 HEART Lab**에서 직접 연락이 왔습니다.
"이런 서비스를 만들고 싶다"는 요청을 받고, AI·공학 기술개발자로 유급 합류하여 Streamlit 기반 웹 프로토타입을 개발해 납품했습니다.

### 3단계 — Hi-Buddy 앱 개발 (현재)

납품한 웹 버전을 기반으로, 직접 **Flutter 모바일 앱**으로 확장 개발했습니다.
온쿡(요리 챗봇)에서 출발해 **발달장애인의 하루 전체를 지원하는 일정 관리 앱**으로 발전시켰습니다.

---

## 주요 기능

- **AI 일정 자동 생성** — 코디네이터가 자연어로 입력하면 Gemini가 구조화된 일정표 생성
- **사용자 맞춤 화면** — 지금 할 일 1개만 크게 표시, 단계별 음성 안내
- **요리/운동/옷입기** — 활동별 특화 UI (레시피 단계, 운동 루틴, AAC 픽토그램)
- **무료 TTS 음성 안내** — Edge TTS 한국어 음성, 각 단계별 재생 버튼
- **오프라인 폴백** — 네트워크 끊겨도 마지막 저장 일정 자동 표시

---

## 시스템 아키텍처

```
코디네이터 (Streamlit / Flutter)
  ↓ 자연어 입력
Gemini 2.0 Flash → JSON 일정표
  ↓ 저장
Backend (FastAPI) → SQLite / 로컬 저장
  ↓ 불러오기
사용자 화면 (Flutter / Streamlit)
  → 현재 활동 표시 + TTS 음성 안내
```

**Two-sided 구조**: 코디네이터(보호자/교사)와 사용자(발달장애인)가 완전히 분리된 화면 사용.

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Mobile App | Flutter (iOS / Android) |
| Web App | Streamlit |
| Backend | FastAPI + SQLite |
| LLM | Gemini 2.0 Flash (무료) |
| TTS | Edge TTS (무료) |
| Image Search | Google Custom Search API |
| Video Search | YouTube Data API v3 |
| 품질 관리 | 규칙 기반 응답 평가 + 자동 재생성 |
| 배포 | Render (무료 tier) |

---

## 접근성 설계 (AAC 기반)

| 영역 | 적용 원칙 |
|------|---------|
| UI | 폰트 40px 이상, 버튼 전체 너비, 화면당 활동 1개 |
| 언어 | 존댓말, 문장 20~45자, 숫자는 한글로 |
| 레시피 | 칼 최소화(가위/손 대체), 약불/중불만, 단계당 1동작 |
| 음성 | 정시 자동 TTS + 각 단계 개별 재생 버튼 |

---

## 프로젝트 구조

```
Hi-Buddy.py                  # Streamlit 메인 진입점
pages/
  1_코디네이터_일정입력.py    # 일정 설계 (코디네이터)
  2_사용자_오늘_따라하기.py   # 따라하기 (사용자)
utils/
  config.py                  # Gemini API 설정
  schedule_ai.py             # 자연어 → JSON 변환 + 품질 평가
  tts.py                     # Edge TTS 합성
  image_ai.py                # 이미지 검색
  youtube_ai.py              # 유튜브 검색 + DD 친화도 점수
  response_evaluator.py      # Gemini 응답 품질 평가기
  recipes.py                 # 레시피 DB
  runtime.py                 # 활성 슬롯 계산
hi_buddy_app/                # Flutter 모바일 앱
backend/                     # FastAPI 백엔드
docs/                        # 개인정보 처리방침
```

---

## 실행 방법

### Streamlit (웹)
```bash
pip install -r requirements.txt
# .env에 GEMINI_API_KEY, GOOGLE_API_KEY, GOOGLE_CSE_ID 설정
streamlit run Hi-Buddy.py
```

### Flutter (모바일)
```bash
cd hi_buddy_app
flutter pub get
flutter run
```

### Backend
```bash
cd backend
pip install -r requirements.txt
# .env에 환경변수 설정 (.env.example 참고)
uvicorn main:app --reload
```

---

## 관련 보도

| 활동 | 기간 | 내용 |
|------|------|------|
| 서울청년기획봉사단 온쉐어 팀장 | 2025.03 ~ 08 | AI 챗봇 단독 개발, 발달장애인 쿠킹클래스 현장 투입 |
| LG Hello Vision 기업 연계 | 2025.08 | 지원금 수령, 헬로TV 뉴스 취재 및 방송 출연 |
| 연세대 HEART Lab 기술 납품 | 2025.12 | Streamlit 웹 프로토타입 개발 및 유급 납품 |

---

## 라이선스

MIT License

---

## 개발자

**JY** — 기획, 설계, 개발 전체 단독 수행
