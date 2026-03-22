# 하루메이트 (HaruMate) · 발달장애인 자립생활 지원 AI 앱

> [서울청년기획봉사단](https://www.donghaeng.seoul.kr/vproject/esg.do) 봉사활동에서 출발하여, TV 방송 보도 → 연세대학교 대학원 초청 → 앱 서비스 출시까지 이어진 프로젝트

---

## Project History

### Phase 1 — [서울청년기획봉사단](https://www.donghaeng.seoul.kr/vproject/esg.do) 2기 · 온쉐어 팀장 (2025.03 ~ 08)

서울시자원봉사센터 주관 [서울청년기획봉사단](https://www.donghaeng.seoul.kr/vproject/esg.do) 2기 **온쉐어** 팀 팀장으로 참가하여, 발달장애인을 위한 AI 요리 챗봇 **온쿡(OnCook)** 을 단독 기획·개발하고 복지관 현장에 투입했습니다.

- 서부장애인종합복지관 자립주거팀 발달장애인 5명 대상 쿠킹클래스 2회 운영
- LG Hello Vision 기업 연계 지원금 수령
- **헬로TV 뉴스 취재 · 방송 보도**
- 참여자 만족도 **4.83 / 5점** · SNS 조회수 **16,000+**

### Phase 2 — 연세대학교 사회복지대학원 초청 · 기술 납품 (2025.12)

봉사단 활동 성과가 알려지며, **연세대학교 사회복지대학원 HEART Lab**으로부터 기술 협력 초청을 받았습니다.
AI·공학 기술개발자로 유급 합류하여 Streamlit 기반 웹 프로토타입을 개발·납품하고, **대학원 연구팀 대상 LLM + AAC 기술 접목 방법론 강연 발표**를 진행했습니다.

### Phase 3 — 하루메이트 모바일 앱 개발 · 서비스 출시 (현재)

납품한 웹 버전을 기반으로 **Flutter iOS/Android 모바일 앱을 독자 개발**했습니다.
백엔드 서버 구축, LLM/TTS 무료 API 전환, 품질 평가 시스템 설계, 스토어 출시 준비까지 전 과정을 단독 수행했습니다.

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
| 서울청년기획봉사단 2기 온쉐어 팀장 | 2025.03 ~ 08 | AI 챗봇 단독 개발, 발달장애인 쿠킹클래스 현장 투입 |
| LG Hello Vision 기업 연계 | 2025.08 | 지원금 수령, 헬로TV 뉴스 취재 및 방송 출연 |
| 연세대 사회복지대학원 초청 | 2025.12 | 기술개발자 유급 합류, 웹 프로토타입 납품, 대학원 강연 발표 |

---

## 라이선스

MIT License

---

## 개발자

**JY** — 기획, 설계, 개발 전체 단독 수행
