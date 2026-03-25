# 하루메이트 v2 — 발달장애인 종합 생활 에이전트

> 스케줄러가 아니라, 발달장애인의 하루 전체를 책임지는 AI 생활 도우미.
> "시리가 발달장애인을 위해 태어났다면"

---

## 핵심 철학

**1. 모든 건 에이전트 하나가 처리한다**
- 일정, 요리, 날씨, 교통, 유튜브, 대화, 감정 지원 — 전부 하나의 에이전트
- 사용자는 앱 안에서 헤매지 않음. 에이전트가 때맞춰 알아서 안내

**2. 오프라인이 기본, 온라인은 보너스**
- 일정, TTS, 레시피, 체크리스트 → 로컬 (인터넷 불필요)
- 날씨, 교통, 유튜브, Claude 대화 → 온라인 (있으면 더 좋음)

**3. 장애 강도별로 다르게 동작**
- 경증: 전체 기능, 자율 조작
- 중등도: 큰 버튼, 자동 TTS, 이미지 중심
- 중증: 키오스크 모드, 터치 불필요, 알아서 진행

---

## 에이전트 기능 전체 맵

### A. 시간 기반 자동 기능 (에이전트가 알아서)

| 기능 | 동작 | 데이터 소스 | LLM? |
|------|------|:---:|:---:|
| 기상 알림 | 설정 시간에 TTS "일어날 시간이에요" | 로컬 | X |
| 아침 브리핑 | 오늘 날씨 + 오늘 일정 요약 + 입을 옷 추천 | 날씨 API | X |
| 활동 시간 알림 | "지금은 OO 시간이에요" + 가이드 표시 | 로컬 | X |
| 식사 추천 | 냉장고 식재료 기반 메뉴 추천 | 로컬 DB | X |
| 약 먹기 알림 | 설정 시간에 TTS + 푸시 알림 | 로컬 | X |
| 외출 알림 | 날씨 + 대중교통 경로 + 소요 시간 안내 | API | X |
| 하루 마무리 | 오늘 한 것 요약 + "잘했어요" 격려 | 로컬 | X |

### B. 사용자 요청 기능 (사용자가 물어보면)

| 기능 | 예시 입력 | 동작 | LLM? |
|------|----------|------|:---:|
| 요리 가이드 | "라면 만들기" | 레시피 + 단계 TTS + 유튜브 | X |
| 유튜브 재생 | "요리 영상 보여줘" | 검색 + 인앱 재생 | X |
| 날씨 확인 | "오늘 날씨" | 현재 날씨 + 옷차림 추천 | X |
| 대중교통 | "복지관 가는 법" | 경로 + 소요시간 + 출발 알림 | X |
| 전화 걸기 | "엄마한테 전화" | 긴급 연락처 원터치 발신 | X |
| 타이머 | "4분 타이머" | 타이머 + 알림 (요리 중 필수) | X |
| 자유 대화 | "심심해", "기분이 안 좋아" | Claude 감정 대화 | O |
| 복잡한 질문 | "내일 뭐 하면 좋을까" | Claude 맥락 기반 추천 | O |

### C. 코디네이터/보호자 기능

| 기능 | 설명 |
|------|------|
| 일정 만들기 | 텍스트 입력 → 로컬 파싱 (즉시) |
| 식재료 관리 | 냉장고에 뭐 있는지 등록/수정 |
| 사용자 프로필 | 장애 강도, 선호도, 알레르기, 약 시간 설정 |
| 수행 기록 열람 | 날짜별 체크리스트 완료율, 도움 필요 횟수 |
| 긴급 연락처 | 보호자, 복지관, 119 등록 |
| 원격 일정 전송 | (v2.5) Firebase로 다른 기기에 일정 보내기 |

---

## 기술 설계

### 에이전트 코어

```dart
class HaruAgent {
  final UserProfile profile;
  final ScheduleManager schedule;
  final RecipeDB recipes;
  final WeatherService weather;
  final TransitService transit;
  final YouTubeService youtube;
  final ClaudeService? claude; // 프리미엄

  /// 메인 입력 처리 — 키워드 매칭 우선, Claude 폴백
  Response handle(String input) {
    // 1차: 인텐트 분류 (로컬, 즉시)
    final intent = classifyIntent(input);

    switch (intent) {
      case Intent.hungry:    return suggestMeal();
      case Intent.weather:   return showWeather();
      case Intent.transit:   return showTransit(input);
      case Intent.youtube:   return searchYouTube(input);
      case Intent.timer:     return startTimer(input);
      case Intent.call:      return makeCall(input);
      case Intent.bored:     return suggestActivity();
      case Intent.medicine:  return medicineReminder();
      case Intent.unknown:
        if (claude != null) return claude!.chat(input, context: profile);
        return Response("잘 이해하지 못했어요. 다시 말해주세요.");
    }
  }

  /// 인텐트 분류 (키워드 기반, LLM 불필요)
  Intent classifyIntent(String input) {
    final t = input.toLowerCase();
    if (matchAny(t, ['배고', '먹', '밥', '요리', '간식', '점심', '저녁'])) return Intent.hungry;
    if (matchAny(t, ['날씨', '비', '우산', '온도', '추워', '더워'])) return Intent.weather;
    if (matchAny(t, ['버스', '지하철', '가는', '교통', '몇 분', '출발'])) return Intent.transit;
    if (matchAny(t, ['유튜브', '영상', '보여', '틀어'])) return Intent.youtube;
    if (matchAny(t, ['타이머', '분', '초', '알려'])) return Intent.timer;
    if (matchAny(t, ['전화', '엄마', '아빠', '선생님'])) return Intent.call;
    if (matchAny(t, ['심심', '놀', '뭐 하', '지루'])) return Intent.bored;
    if (matchAny(t, ['약', '먹어야'])) return Intent.medicine;
    return Intent.unknown;
  }
}
```

### 데이터 구조 (sqflite)

```sql
-- 사용자 프로필
CREATE TABLE user_profile (
  id INTEGER PRIMARY KEY,
  name TEXT,
  disability_level TEXT,  -- mild/moderate/severe
  ui_mode TEXT,           -- normal/simple/kiosk
  tts_speed REAL,
  wake_time TEXT,         -- 기상 시간
  sleep_time TEXT         -- 취침 시간
);

-- 식재료 (냉장고)
CREATE TABLE ingredients (
  id INTEGER PRIMARY KEY,
  name TEXT,
  category TEXT,          -- 채소/고기/양념/면류/...
  added_date TEXT,
  expiry_date TEXT        -- 유통기한 (선택)
);

-- 일정 템플릿 (매일 반복)
CREATE TABLE daily_template (
  id INTEGER PRIMARY KEY,
  day_of_week INTEGER,    -- 0=매일, 1=월, ..., 7=일
  time TEXT,
  type TEXT,
  task TEXT,
  guide_script TEXT       -- JSON array
);

-- 수행 기록
CREATE TABLE completion_log (
  id INTEGER PRIMARY KEY,
  date TEXT,
  time TEXT,
  activity_type TEXT,
  task TEXT,
  completed INTEGER,      -- 0/1
  steps_total INTEGER,
  steps_completed INTEGER,
  needed_help INTEGER,    -- 0/1
  duration_seconds INTEGER
);

-- 긴급 연락처
CREATE TABLE emergency_contacts (
  id INTEGER PRIMARY KEY,
  name TEXT,              -- "엄마", "선생님"
  phone TEXT,
  relationship TEXT
);

-- 약 알림
CREATE TABLE medicine_schedule (
  id INTEGER PRIMARY KEY,
  name TEXT,              -- 약 이름
  time TEXT,              -- HH:MM
  days TEXT               -- "매일" or "월,수,금"
);

-- 자주 가는 장소
CREATE TABLE places (
  id INTEGER PRIMARY KEY,
  name TEXT,              -- "복지관", "집"
  address TEXT,
  latitude REAL,
  longitude REAL
);
```

### 외부 서비스 (전부 무료 or 기존 키)

| 서비스 | API | 비용 | 용도 |
|--------|-----|:---:|------|
| 날씨 | OpenWeatherMap Free | 무료 (1000회/일) | 현재 날씨 + 예보 |
| 대중교통 | 카카오맵 API or ODsay | 무료 tier | 경로 검색 + 소요시간 |
| 유튜브 | YouTube Data API | 무료 (기존 키) | 영상 검색 + 재생 |
| TTS | flutter_tts | 무료 (디바이스) | 모든 음성 안내 |
| AI 대화 | Claude API | 종량제 | 프리미엄 대화만 |
| 동기화 | Firebase | 무료 tier | 코디-사용자 연결 (선택) |

### 화면 구성

```
[탭 1: 오늘 하루]        ← 메인. 시간 기반 자동 안내
  - 현재 활동 카드 (큰 글씨)
  - 단계별 가이드 + 체크박스
  - 유튜브 영상 (관련 시)
  - 다음 일정 미리보기

[탭 2: 도우미]           ← 에이전트 대화
  - 음성/텍스트 입력
  - "배고파" → 식사 추천
  - "날씨" → 날씨 + 옷 추천
  - "복지관 가는 법" → 교통 안내
  - "심심해" → 유튜브 추천 / Claude 대화

[탭 3: 나의 정보]        ← 코디네이터가 관리
  - 일정 만들기/수정
  - 식재료 관리
  - 약 알림 설정
  - 긴급 연락처
  - 수행 기록 (그래프)

[설정]
  - 장애 강도 (UI 모드 자동 전환)
  - TTS 속도
  - 알림 설정
```

---

## 장애 강도별 동작 차이

### 경증 (일반 모드)
```
전체 기능 사용 가능
텍스트 + 음성 + 이미지
자율적 네비게이션
에이전트 대화 가능
```

### 중등도 (간단 모드)
```
큰 아이콘 3개: 🍚 밥 | 💪 운동 | 😊 놀기
자동 TTS (모든 화면 자동 읽기)
이미지 중심 (텍스트 최소화)
체크박스 대신 큰 ✅ 버튼
유튜브는 자동 재생 (검색 없이)
```

### 중증 (키오스크 모드)
```
터치 불필요
시간에 맞춰 자동으로 화면 전환
자동 TTS 연속 재생
음악/영상 자동 재생
보호자 원격 제어 (Firebase)
SOS 버튼 하나만 (큰 빨간 버튼)
```

---

## 아침 브리핑 시나리오 예시

### 경증 사용자 (22세 준서)

```
[08:00 알람]
에이전트: "좋은 아침이에요, 준서님!"

[날씨 카드]
"오늘 날씨는 맑고 따뜻해요. 15도예요."
"가벼운 겉옷 하나 입으면 좋겠어요."

[오늘 일정 카드]
"오늘 할 일을 알려드릴게요."
• 09:00 세수하기
• 10:00 옷 입기
• 12:00 라면 만들기 🍜
• 15:00 복지관 가기 🚌
• 18:00 운동하기 💪
• 22:00 하루 마무리

[대중교통 카드] (15:00 복지관 일정 감지)
"오늘 3시에 복지관 가야 해요."
"버스 145번 타면 25분 걸려요."
"2시 30분에 출발하면 돼요."
[출발 알림 설정하기]

[식사 카드] (냉장고: 라면, 달걀, 김치)
"점심은 라면 어때요? 집에 라면이 있어요."
[레시피 보기] [유튜브로 보기]
```

---

## 수익 모델

| 티어 | 가격 | 기능 |
|------|:---:|------|
| **무료** | 0원 | 일정, TTS, 레시피, 체크리스트, 타이머 |
| **베이직** | 월 2,900원 | + 날씨, 대중교통, 유튜브 검색 |
| **프리미엄** | 월 4,900원 | + Claude 대화, 감정 지원, 맞춤 추천 |
| **기관용** | 월 15만원 | + 다중 사용자, 수행 리포트, 원격 관리 |

---

## 개발 로드맵

| 단계 | 기간 | 핵심 기능 |
|------|------|----------|
| **v2.0** | 1주 | sqflite + 사용자 프로필 + 로컬 일정 생성 |
| **v2.1** | 1주 | 에이전트 코어 (인텐트 분류 + 시간 기반 자동) |
| **v2.2** | 1주 | 날씨 API + 아침 브리핑 + 옷 추천 |
| **v2.3** | 1주 | 유튜브 인앱 검색/재생 + DD 필터링 |
| **v2.4** | 1주 | 대중교통 API + 외출 알림 + 경로 안내 |
| **v2.5** | 1주 | Claude 대화 연동 + 감정 지원 |
| **v2.6** | 1주 | 장애 강도별 UI 모드 (간단/키오스크) |
| **v2.7** | 1주 | 수행 기록 + 리포트 + 기관용 대시보드 |
| **v2.8** | 1주 | Firebase 동기화 + 원격 일정 전송 |

**총 9주. v1 스토어 출시하면서 병렬 개발.**

---

## v1 vs v2 한눈에

| | v1 (스케줄러) | v2 (생활 에이전트) |
|---|---|---|
| 정체성 | 일정 관리 앱 | **발달장애인 종합 생활 도우미** |
| 일정 | 서버 API (느림) | 로컬 (즉시) |
| 날씨 | 없음 | **아침 브리핑 + 옷 추천** |
| 교통 | 없음 | **대중교통 경로 + 출발 알림** |
| 유튜브 | 제한적 | **인앱 검색/재생 + 자동 추천** |
| 대화 | 없음 | **Claude 에이전트** |
| 식재료 | 없음 | **냉장고 관리 + 메뉴 추천** |
| 약 | 없음 | **복약 알림** |
| 전화 | 없음 | **긴급 연락처 원터치** |
| 타이머 | 없음 | **요리 중 타이머** |
| 수행 기록 | 없음 | **체크리스트 + 리포트** |
| UI 모드 | 1종 | **3종 (일반/간단/키오스크)** |
| 오프라인 | 부분 | **핵심 기능 100%** |
| 서버 의존 | 필수 | **없음 (선택)** |
