# Hi-Buddy 스토어 출시 체크리스트

돈만 내면 되는 상태까지 코드는 다 됨. 아래 순서대로 실행.

---

## Step 1: Windows 개발자 모드 켜기 (1분)
```
시작 > 설정 > 개발자용 > 개발자 모드 ON
또는: start ms-settings:developers
```

## Step 2: 백엔드 배포 (10분)

### 옵션 A: Render (추천, 무료)
1. https://render.com 가입
2. New > Web Service > GitHub 레포 연결
3. 설정:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. 환경변수 설정 (`.env.example` 참고):
   - `GEMINI_API_KEY` — https://aistudio.google.com/apikey 에서 발급
   - `GOOGLE_API_KEY`
   - `GOOGLE_CSE_ID`
   - `APP_AUTH_TOKEN` — 아무 랜덤 문자열
5. 배포 URL 메모 (예: `https://hibuddy-api.onrender.com`)

### 옵션 B: Railway
```bash
cd backend
npm i -g @railway/cli
railway login
railway init
railway up
railway variables set GEMINI_API_KEY=...
railway variables set GOOGLE_API_KEY=...
railway variables set GOOGLE_CSE_ID=...
railway variables set APP_AUTH_TOKEN=...
```

## Step 3: Gemini API 키 발급 (2분)
1. https://aistudio.google.com/apikey
2. "Create API Key" 클릭
3. 키 복사 → 백엔드 환경변수에 설정

## Step 4: 키스토어 생성 (2분)
```bash
cd hi_buddy_app
bash scripts/generate_keystore.sh
```
비밀번호 입력하면 자동으로:
- `hibuddy-release.jks` (키스토어 파일)
- `android/key.properties` (빌드 설정)

**⚠️ 키스토어 파일은 안전한 곳에 백업! 잃어버리면 앱 업데이트 불가!**

## Step 5: 릴리즈 빌드 (5분)
```bash
cd hi_buddy_app
bash scripts/build_release.sh https://your-server-url.com your-auth-token
```
결과:
- `build/app/outputs/bundle/release/app-release.aab` (Play Store용)
- `build/app/outputs/flutter-apk/app-release.apk` (테스트용)

## Step 6: Google Play Console 등록 ($25 1회)
1. https://play.google.com/console 가입 (25달러 결제)
2. "앱 만들기" 클릭
3. 앱 정보 입력 (`store_listing.md` 참고)
4. 개인정보 처리방침 URL 입력 (GitHub Pages에 `docs/privacy_policy.md` 호스팅)
5. 콘텐츠 등급 설문 작성 → "전체 이용가"
6. 앱 번들(AAB) 업로드
7. 심사 제출

## Step 7: 개인정보 처리방침 호스팅 (5분)
GitHub Pages로 무료 호스팅:
```bash
# 레포에 docs/privacy_policy.md 있으니까
# GitHub 레포 Settings > Pages > Source: Deploy from branch
# Branch: main, Folder: /docs
```
URL: `https://[username].github.io/Hibuudy/privacy_policy.html`

---

## 비용 요약

| 항목 | 비용 | 비고 |
|------|------|------|
| Gemini API | 무료 | 15 RPM 무료 tier |
| Edge TTS | 무료 | 완전 무료 |
| Render 서버 | 무료 | Free tier (750시간/월) |
| Google Play | $25 (1회) | 개발자 등록비 |
| Apple App Store | $99/년 | iOS는 선택사항 |
| **Android만 합계** | **$25** | |

---

## 파일 구조 최종

```
hi_buddy_app/
├── scripts/
│   ├── generate_keystore.sh    ← 키스토어 생성
│   ├── build_release.sh        ← 릴리즈 빌드
│   └── deploy_backend.sh       ← 백엔드 배포
├── store_listing.md            ← 스토어 등록 정보
├── android/
│   ├── key.properties          ← (생성 후) 서명 설정
│   └── app/proguard-rules.pro  ← ProGuard 규칙
└── pubspec.yaml                ← v1.0.0+1

backend/
├── Dockerfile                  ← Docker 배포
├── render.yaml                 ← Render 설정
├── railway.toml                ← Railway 설정
├── .env.example                ← 환경변수 템플릿
└── main.py                     ← API 서버

docs/
└── privacy_policy.md           ← 개인정보 처리방침
```
