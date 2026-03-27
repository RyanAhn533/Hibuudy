# 하루메이트 Autonomous Development Agent

> 이 파일을 읽은 Claude는 하루메이트 프로젝트의 자율 개발 에이전트로 동작한다.
> CLAUDE.md = weight, prompt = action signal, memory = shared state.
> 프로젝트 디렉토리: C:/Users/wnsdu/Hibuudy/

---

## 1. 프로젝트 상태 (V: Vision)

### 현재 버전: v2.1
- 패키지: com.harumate.app
- 앱 이름: 하루메이트 (구 Hi-Buddy, 이름 변경 완료)
- 서버: https://hibuudy.onrender.com (Render Free)
- LLM: Claude Haiku 4.5 (에이전트 대화) + Gemini 2.0 Flash (백엔드)
- TTS: flutter_tts (디바이스, 오프라인)
- DB: sqflite 로컬 (7 테이블) + SharedPreferences
- 오프라인: 핵심 기능 100% 동작

### 디렉토리 구조
```
C:/Users/wnsdu/Hibuudy/
├── CLAUDE.md                    ← 이 파일
├── README.md                    ← 포트폴리오
├── Hi-Buddy.py                  ← Streamlit 웹앱
├── pages/ utils/                ← Streamlit
├── backend/                     ← FastAPI (Render)
├── hi_buddy_app/                ← Flutter 앱 (메인)
│   ├── lib/
│   │   ├── screens/             ← home, coordinator, user, agent, profile, youtube, timer
│   │   ├── services/            ← haru_agent, api, database, schedule_generator, tts, weather, timer, ui_mode
│   │   ├── widgets/             ← activity_card, step_card, morning_briefing, sos_button
│   │   └── models/ theme/
│   ├── assets/data/recipes.json
│   └── android/ ios/
└── docs/                        ← 개인정보처리방침, 시뮬레이션, 리뷰
```

### 완료된 기능
- [x] 일정 만들기 (로컬 파싱 + API 폴백)
- [x] 오늘 하루 (시간 기반 활동 + 30초 갱신)
- [x] 도우미 에이전트 (Claude 맥락 기반 + 오프라인 폴백)
- [x] 나의 정보 (프로필, 식재료, 연락처, 약, 수행 기록)
- [x] 단계 체크박스 + 격려 + 일정 복사 + 수동 추가
- [x] 날씨 (wttr.in) + 아침 브리핑 + 옷 추천
- [x] 유튜브 인앱 재생 + 타이머 (레시피 연동)
- [x] 장애 강도별 UI (일반/간단/키오스크) + SOS 버튼
- [x] 활동 전환 알림 + 오프라인 폴백

### TODO (우선순위순)
- [ ] 대중교통 API + 외출 알림
- [ ] 앱 아이콘 커스텀
- [ ] Play Store 등록
- [ ] Firebase 동기화
- [ ] 노인 모드
- [ ] 수행 기록 리포트

---

## 2. 판단 기준

### 우선순위: 크래시 > UX > 차별화 > 비즈니스 > 최적화
### 규칙: YAGNI, 오프라인 우선, 접근성 (16px+/48px+), 기술 용어 금지
### 테스트: dart analyze → APK 빌드 → 바탕화면 복사 → git push

### 실패 패턴 (반복 금지)
- 패키지 리네이밍 시 Kotlin 디렉토리도 이동
- ProGuard minify OFF 유지
- Gemini 1회만 호출 (429 방지)
- API 키 절대 git에 올리지 마 (.env로만 관리)
- "할 수 있습니다" 금지, 바로 실행
- JY 자는 동안 백그라운드 에이전트 돌려

### JY 워크플로우
- "ㄱ" = 실행, "다 해라" = 병렬 실행, "봐바라" = 읽고 요약
- 중요 결정 = 3명 토론 + Opus 리뷰
- 대기 = 리뷰/테스트/개선안 자동 도출

---

## 3. 실행 로그

### 세션 1 (2026-03-22): OpenAI→Gemini 전환, Render 배포, 앱 이름 변경, README 포트폴리오화
### 세션 2 (2026-03-23~24): 크래시 수정, 전문가 패널 68/100, 100명 시뮬레이션, UX 5개 수정, 기능 5개 추가
### 세션 3 (2026-03-25~27): v2.0 에이전트 전환, sqflite DB, Claude 에이전트, 날씨/유튜브/타이머/UI모드/SOS, +6000줄

---

## 4. VLA 루프

```
1. CLAUDE.md 읽기 (V)
2. TODO 중 임팩트 최고 판단 (L)
3. 실행 + 빌드 + 테스트 (A)
4. 로그 기록 + 다음 액션 제안
```

---

## 5. 기술 환경

```
Flutter: C:/flutter/bin/flutter.bat
Android SDK: C:/Users/wnsdu/AppData/Local/Android/Sdk
Java: C:/Program Files/Android/Android Studio/jbr
Python: C:/Users/wnsdu/anaconda3/python.exe
GitHub: RyanAhn533/Hibuudy

빌드:
  export JAVA_HOME="/c/Program Files/Android/Android Studio/jbr"
  export ANDROID_HOME="$LOCALAPPDATA/Android/Sdk"
  flutter build apk --release
  → C:/Users/wnsdu/Desktop/하루메이트.apk

API 키: .env 또는 Render 환경변수에서 관리 (절대 git에 올리지 말 것)
```

---

## 6. 비즈니스

- 스토리: 서울청년기획봉사단 2기 → TV → 연세대 초청 → 앱 독자 개발
- 소유권: Flutter 앱 = JY 100% 소유
- 외주 견적: 3,000~4,000만원
- 타겟: 발달장애인 25만 + 독거 노인 180만
- 수익: 무료(0원) / 베이직(2,900원) / 프리미엄(4,900원) / 기관(15만원)
