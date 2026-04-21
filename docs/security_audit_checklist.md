# 하루메이트 보안 오딧 체크리스트

> **작성일:** 2026-04-20
> **대상 버전:** v2.1 (패키지 `com.harumate.app`, 백엔드 `hibuudy.onrender.com`)
> **용도:** 스토어 출시 전 반드시 확인/수정해야 할 보안 이슈 목록
> **범위:** 회원가입·인증·페어링·개인정보·API 키 관리

---

## 📊 요약

| 심각도 | 개수 | 출시 전 필수 |
|--------|------|-------------|
| 🔴 CRITICAL | 5 | ✅ 반드시 |
| 🟠 HIGH | 4 | ⚠️ 권장 |
| 🟡 MEDIUM | 3 | 출시 후 |
| ✅ OK | 6 | — |

**출시 전 최소 작업:** 약 10-12시간

---

## 🔴 CRITICAL (출시 전 필수)

### [ ] C-1. Claude API 키가 APK에 그대로 박혀 있음
**위치:** `hi_buddy_app/lib/services/haru_agent.dart:32-35`

```dart
static const String _apiKey = String.fromEnvironment(
  'CLAUDE_API_KEY',
  defaultValue: '',
);
```

**문제:**
- `--dart-define`은 컴파일 시점에 상수로 DEX에 박힘
- `jadx` 등 디컴파일 도구로 10분이면 추출
- Anthropic API 키 탈취 시 JY 결제 계정 무제한 호출 가능

**아이러니:** `backend/main.py:342-397`에 `/api/agent` 프록시가 이미 구현되어 있는데, Flutter가 직접 `api.anthropic.com` 호출 중. 프록시 의미 없음.

**조치:**
- [ ] `haru_agent.dart`의 `_handleWithClaude`를 `ApiService`의 `/api/agent` 호출로 교체
- [ ] `CLAUDE_API_KEY` dart-define 완전 제거
- [ ] 기존 노출된 키는 Anthropic 콘솔에서 폐기(revoke) 후 재발급

---

### [ ] C-2. "회원가입"이 사실상 존재하지 않음
**위치:** `backend/main.py:79-85`

```python
def verify_token(request: Request):
    if not APP_AUTH_TOKEN:
        return  # 토큰 미설정이면 인증 없이 통과
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {APP_AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="인증 실패")
```

**문제:**
- `APP_AUTH_TOKEN` 미설정 시 무조건 통과 (커밋 5bdc4cc)
- 설정되어도 **전역 공유 static 토큰** → 모든 앱 인스턴스가 같은 토큰 → 유저 구분 불가 → "회원가입" 개념 부재
- `api_service.dart:14-15`에서 `--dart-define API_TOKEN=xxx`로 빌드 시점 삽입 → APK 디컴파일로 추출 가능

**악용:** 누구든 토큰 추출 → Gemini/Claude 무제한 호출 → 과금 피해

**조치 (단기 — 출시 전 최소):**
- [ ] 앱 첫 실행 시 `Random.secure()`로 UUID 생성
- [ ] 서버에 `POST /api/device/register` 엔드포인트 추가 → device_token 발급
- [ ] `flutter_secure_storage`(Android Keystore 연동) 패키지로 토큰 저장
- [ ] `verify_token`이 DB에서 device_token 조회해 유효성 확인
- [ ] Rate limit을 IP가 아닌 device_token 단위로 변경

**조치 (중기):**
- [ ] Firebase Auth 익명 로그인 도입
- [ ] 향후 Google/Apple OAuth 연동

---

### [ ] C-3. 페어링 코드 예측 가능 + 서버 검증 없음
**위치:** `hi_buddy_app/lib/services/session_service.dart:110-114`

```dart
static String generatePairCode() {
  final now = DateTime.now().microsecondsSinceEpoch;
  final code = (now % 900000 + 100000).toString();
  return code;
}
```

**문제:**
- 시간 기반 → 같은 순간 생성한 기기끼리 근접값 → 브루트포스 난이도 낮음
- 서버에 등록/검증 없음 → UI만 있고 실제 페어링 로직 없음
- `database_service.dart:106` `pair_session` 테이블은 로컬 저장만

**스토어 심사 리스크:** 앱 설명에 "페어링 기능" 기재했는데 실제로 안 작동 → 기재 기능과 실동작 불일치로 반려 가능

**조치:**
- [ ] `session_service.dart`: `Random.secure()` 기반 생성으로 변경
- [ ] 백엔드에 `/api/pair/create` 추가 (서버가 `secrets.token_hex`로 생성, 10분 만료)
- [ ] 백엔드에 `/api/pair/claim` 추가 (1회용, 소비되면 무효화)
- [ ] DB에 `pair_codes` 테이블: `(code, creator_device_token, claimer_device_token, created_at, expires_at, used)`

---

### [ ] C-4. user_id 위조 (IDOR) — 일정 바꿔치기 가능
**위치:** `backend/main.py:577, 591` + `hi_buddy_app/lib/screens/coordinator_screen.dart:75`

```python
async def save_schedule(request, body: ScheduleSaveRequest, _=Depends(verify_token)):
    # body.user_id를 그대로 믿음 — 인증된 유저와 무관
```

```dart
'default_user', // TODO: 인증 구현 후 실제 user_id로 교체
```

**악용 시나리오:**
```http
POST /api/schedule/save
Authorization: Bearer <토큰>
{
  "user_id": "victim_user_id",
  "date": "2026-04-20",
  "schedule": [{"time":"08:00","task":"약 먹기","time":"15:00"...}]
}
```
→ **남의 약 복용 스케줄 변경 가능**. 발달장애인 대상 앱에서 실제 건강 피해로 직결.

**조치:**
- [ ] `verify_token`이 device_token → user_id 매핑으로 유저 결정
- [ ] `ScheduleSaveRequest`/`schedule_load` 파라미터에서 `user_id` **완전 제거**
- [ ] 서버가 인증된 device_token의 user_id만 사용

---

### [ ] C-5. CORS / TrustedHost 미설정
**위치:** `backend/main.py:55`

```python
app = FastAPI(title="Hi-Buddy API", docs_url=None, redoc_url=None)
# CORSMiddleware, TrustedHostMiddleware 없음
```

**문제:**
- 현재 인증이 사실상 오픈이므로 누구든 브라우저에서 API 직접 호출 가능
- Host 헤더 변조 공격 방어 없음

**조치:**
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["hibuudy.onrender.com", "localhost"]
)
```
- [ ] CORSMiddleware는 웹 프론트엔드 없으면 불필요. 추가 시 `allow_origins=[]`(앱은 브라우저가 아니므로 CORS 미적용)

---

## 🟠 HIGH (출시 직후 수정 권장)

### [ ] H-1. 긴급 연락처 / 약 스케줄 평문 저장
**위치:** `hi_buddy_app/lib/services/database_service.dart` 테이블 `emergency_contacts`, `medicine_schedule`

**문제:**
- sqflite 기본은 암호화 안 됨
- 루팅/탈옥 기기 + `adb pull /data/data/com.harumate.app/databases/harumate.db` → 평문 노출
- 발달장애인 **보호자 전화번호 + 약 정보**는 개인정보보호법상 **민감정보**

**조치:**
- [ ] `sqflite_sqlcipher` 패키지로 교체 (DB 전체 암호화)
- 또는 [ ] 전화번호/약명만 `flutter_secure_storage`로 분리 저장

---

### [ ] H-2. ProGuard minify OFF
**위치:** `hi_buddy_app/android/app/build.gradle.kts:53-54`

```kotlin
release {
    isMinifyEnabled = false
    isShrinkResources = false
}
```

**문제:**
- CLAUDE.md에 "ProGuard minify OFF 유지" 실패패턴 기록됨 — 과거 빌드 에러 회피용
- 미난독화 시 디컴파일 난이도 ↓ → C-1(Claude 키 탈취) 더 쉬움
- C-1 해결 후에는 반드시 minify ON 재시도 필요

**조치:**
- [ ] C-1 해결 후 `isMinifyEnabled = true` 재시도
- [ ] ProGuard rules 부족하면 `-keep class ...` 추가하며 디버깅
- [ ] 릴리즈 빌드 후 동작 확인 (특히 JSON 파싱, sqflite)

---

### [ ] H-3. Git history에 API 키 잔존 가능성
**위치:** 커밋 `af9ea2a` ("SECURITY: Remove exposed API keys")

**문제:**
- force push 또는 BFG Repo-Cleaner로 히스토리 정리하지 않았으면 이전 커밋에서 복원 가능
- 한 번이라도 노출된 키는 공격자가 이미 크롤링했을 가능성

**체크 명령:**
```bash
cd C:/Users/wnsdu/Hibuudy
git log --all --full-history -p -- CLAUDE.md | grep -iE "sk-ant|AIza|Bearer"
git log --all --full-history -p | grep -iE "sk-ant-|AIza[A-Za-z0-9_-]{35}"
```

**조치:**
- [ ] 위 명령으로 노출 이력 확인
- [ ] 노출 시: Anthropic / Google Cloud Console에서 **전량 폐기 후 재발급**
- [ ] 필요 시 `git filter-repo` 또는 BFG로 히스토리 정리 후 force push

---

### [ ] H-4. Rate Limit이 IP 기반 — Render 프록시 뒤에서 오작동
**위치:** `backend/main.py:56`

```python
limiter = Limiter(key_func=get_remote_address)
```

**문제:**
- Render 등 리버스 프록시 뒤에서는 프록시 IP가 반환될 수 있음
- → 전체 사용자가 하나의 IP로 묶여 빠르게 제한 도달 (DoS 유발)
- 또는 공격자가 `X-Forwarded-For` 조작으로 우회

**조치:**
- [ ] `X-Forwarded-For` 첫 번째 IP 파싱하는 `key_func` 구현
- [ ] 또는 device_token 인증 도입 후 토큰 기반 rate limit

---

## 🟡 MEDIUM (장기 개선)

### [ ] M-1. 로그에 request body 200자 노출
**위치:** `backend/main.py:67`

```python
return JSONResponse(
    status_code=422,
    content={"detail": exc.errors(), "body": str(exc.body)[:200] if exc.body else None},
)
```

**문제:** 연락처/약/이름 등 민감정보가 Render 로그로 수집됨
**조치:** `body` 필드 제거 또는 redaction

---

### [ ] M-2. 네트워크 cert pinning 없음
**문제:** 공공 WiFi(카페/복지관) MITM 가능. 발달장애인/노인 사용 환경에서 실재 리스크
**조치:** `http_certificate_pinning` 패키지 검토 (유지보수 부담 vs 보안 이득 고려)

---

### [ ] M-3. Render Free Tier SQLite 휘발
**위치:** `backend/main.py:539` `SCHEDULE_DB = Path(__file__).parent / "schedules.db"`
**문제:** Render 재시작 시 파일시스템 리셋 → 서버 저장 일정 주기적 손실
**조치:** Render Postgres Free 연동 또는 "로컬 우선" 설계 공식화(서버 저장 안 함)

---

## ✅ 잘 되어 있는 부분 (유지)

- [x] SQL injection 방어: `?` 파라미터 바인딩 일관 사용
- [x] `android:allowBackup="false"` (앱 데이터 백업 차단)
- [x] `android:usesCleartextTraffic="false"` (HTTP 차단)
- [x] `network_security_config.xml` 적절 (프로덕션 HTTPS only, 에뮬레이터만 HTTP 허용)
- [x] TTS 캐시 경로: SHA256 해싱 (path traversal 안전)
- [x] 입력 검증: `sanitize()` 제어문자 필터 + 길이 제한, Pydantic `Field(max_length=...)`
- [x] upstream API 에러 변환: `raise_for_upstream` → 원문 에러 노출 방지

---

## 🎯 권장 작업 순서 (출시 전)

| 순서 | 작업 | ID | 예상 시간 |
|------|------|-----|----------|
| 1 | `haru_agent.dart` → `/api/agent` 백엔드 프록시로 교체 | C-1 | 1h |
| 2 | 노출된 API 키 전량 로테이션 | H-3 | 30min |
| 3 | `/api/device/register` + device_token 시스템 | C-2 | 3h |
| 4 | `verify_token` DB 조회 방식 + user_id 위조 차단 | C-4 | 2h |
| 5 | 페어링 API 구현 (`/api/pair/create`, `/claim`) | C-3 | 3h |
| 6 | TrustedHostMiddleware 추가 | C-5 | 15min |
| 7 | ProGuard minify ON 재시도 | H-2 | 1h |

**총 10-12시간**

**출시 후 1주 내:** H-1(DB 암호화), H-4(rate limit)

**장기:** M-1~M-3, Firebase Auth 도입

---

## 📋 체크리스트만 보기 (복붙용)

```
CRITICAL
[ ] C-1: haru_agent.dart → 백엔드 프록시로 교체, CLAUDE_API_KEY 제거
[ ] C-2: device_token 기반 인증 시스템 구축
[ ] C-3: 페어링 코드 서버 생성/검증으로 전환
[ ] C-4: user_id 위조 차단 (토큰 기반)
[ ] C-5: TrustedHostMiddleware 추가

HIGH
[ ] H-1: 민감정보 DB 암호화 (sqflite_sqlcipher)
[ ] H-2: ProGuard minify ON 재시도
[ ] H-3: git history 키 노출 확인 + 로테이션
[ ] H-4: Rate limit을 X-Forwarded-For 또는 토큰 기반으로

MEDIUM
[ ] M-1: 로그 body redaction
[ ] M-2: cert pinning 검토
[ ] M-3: Postgres 이전 또는 로컬 우선 공식화
```

---

**다음 세션에서:** 위 순서대로 진행하거나, C-1/C-2만 먼저 긴급 패치 결정
