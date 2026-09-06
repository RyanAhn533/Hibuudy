# 하루메이트 (HaruMate) — 1-Pager

> 발달장애 당사자가 **보호자의 지속 지시 없이도** 하루 일과를 따라갈 수 있게 돕는, **AI 기반 접근성 우선 생활 루틴 보조 앱**

---

## 핵심 한 줄
**Flutter + FastAPI + 멀티 LLM(Claude+Gemini+Groq) + Edge TTS + 멀티 에이전트 + 3-tier 메모리** 로 **WCAG AAA 접근성**과 **100% 오프라인 폴백**을 동시에 제공하는, 사회취약계층용 AI 보조 시스템.

## 임팩트 / 검증
- **연세대 사회복지대학원 HEART Lab + 서부장애인종합복지관** 협력
- **온쿡 (전신) 헬로TV 보도** + 발달장애인 클래스 만족도 **4.83/5**
- **NVIDIA Nemotron-Personas-Korea** (한국 통계청 grounding) 기반 **281,992 페르소나** 시뮬레이션
- 240건 시나리오 시뮬레이션 **라우팅 정확도 100%**, **위급 처리율 100%**

## 차별화 (일반 AI 챗봇과의 차이)
| | 일반 AI 챗봇 | 하루메이트 |
|---|---|---|
| 주체 | 챗봇 | **일과 수행 보조** (챗봇은 보조) |
| 사용자군 | 일반인 | **당사자 + 보호자 + 기관** 3 역할 분리 |
| 접근성 | 옵션 | **WCAG AAA 기본**, UI 모드 3단계 |
| 오프라인 | 미지원 | **핵심 기능 100% 동작** |
| LLM | 단일 | **3-tier (로컬 → 온디바이스 → 클라우드)** |
| 검증 | 사용자 평점 | **NVIDIA 통계청 grounded 페르소나** |
| 위급 | 없음 | **SOS 상시 + EMERGENCY 키워드 priority 1.0** |
| 보호자 연동 | — | **페어링 코드 → 30초 자동 싱크** |
| B2B | — | **엑셀 내보내기 (3시트)** 복지관 제출용 |
| AI 투명성 | 블랙박스 | **plan 시각화 + 사용자 승인** |

## 기술 구성 (한눈에)
```
[디바이스]  Flutter (com.harumate.care, v1.3.3+6)
            ├ UI 모드 3단계 (normal/simple/kiosk)
            ├ HaruTokens 디자인 시스템 + Pretendard
            ├ sqflite 7테이블 + flutter_local_notifications
            └ Tier 0 (오프라인) / Tier 1 (Gemini Nano)
                          ↓ HTTPS Bearer
[백엔드]    FastAPI on Render Free
            ├ /api/* 16 엔드포인트 + slowapi rate limit
            ├ LLM 캐스케이드: Claude → Gemini → Groq
            ├ Edge TTS (ko-KR) + SHA256 캐시
            └ /api/v3/* 멀티 에이전트 옵트인
                ├ Schedule / Meal / Health / Social
                ├ Mem0 3-tier (Zep temporal validity)
                └ EMERGENCY priority 1.0
[검증]      NVIDIA Nemotron-Personas-Korea 281,992
            └ 5 시나리오 × N → 100% 라우팅
```

## 비용
- **연간 운영비: $0~$50** (Android Play 등록비 $25 1회 제외)
- 무료: Render / Edge TTS / Gemini 15 RPM / Groq / wttr.in / Hugging Face
- 유료(선택): Claude Haiku 4.5 (~$5~50/월)

## 코드 규모
| 영역 | 파일 | 줄 수 |
|---|---|---|
| Flutter (lib/) | 32 | ~9,577 |
| FastAPI (backend/) | 3 | ~1,200 |
| v3 Python (v3/) | 14 | ~2,500 |
| Streamlit (Hi-Buddy.py + pages/) | 3 | ~1,650 |
| **합계** | ~52 | **~14,927** |

테스트 54/54 통과 · 시뮬레이션 240/240 통과

## 상태
- v1.3.3 Google Play **비공개 테스트 검토 중** (Google Group `harumate-testers@googlegroups.com`)
- v3.0-dev 멀티 에이전트 백엔드 **구현 + 시뮬레이션 100%** (배포 대기)
- D1-D3 디자인 시스템 일관 적용 중 (HaruText utility, 키오스크 단일 포커스)
- **마감 기준 작업** (현대오토에버 D-9, 연세대 발표 시점)

## 5개월 진화 (Streamlit → 멀티 에이전트)
```
2025-12  Streamlit 프로토타입 (OpenAI 기반)
2026-03  Flutter 앱화 + Gemini/Edge TTS 무료 운영 + 백엔드 분리
2026-03  AI 에이전트화 v2.0 (Claude 컨텍스트 기반)
2026-03  접근성 v2.1 (UI 3모드, SOS, 날씨, 타이머)
2026-04  품질 정상화 v1.x (캐스케이드, 세그먼트, B2B, CI, 디자인 토큰)
2026-05  v3.0-dev (멀티 에이전트 + Mem0 + 페르소나 + 디자인 일관 적용) ← 현재
```

## 자료
- 종합 아키텍처: [docs/ARCHITECTURE_FULL.md](ARCHITECTURE_FULL.md) (722줄)
- 진화사: [docs/EVOLUTION.md](EVOLUTION.md) (562줄)
- **페르소나 검증 디테일: [docs/PERSONA_VALIDATION.md](PERSONA_VALIDATION.md)** (NVIDIA 데이터셋 방법론 + FAQ + 재현 방법)
- v3 설계: [v3/ARCHITECTURE.md](../v3/ARCHITECTURE.md)
- 개인정보처리방침: [docs/privacy_policy.md](privacy_policy.md)
- 복지관 매뉴얼: [docs/welfare-center-manual.md](welfare-center-manual.md)
- 보안 감사: [docs/security_audit_checklist.md](security_audit_checklist.md)
- 백엔드: https://hibuudy.onrender.com
- 저장소: https://github.com/RyanAhn533/Hibuudy

---

## 외부 표현 가이드 (중요)
✅ **써도 됨**
- "LLM 기반 사용자 페르소나 시뮬레이션 (NVIDIA Nemotron-Personas-Korea, 한국 통계청 grounding)"
- "연세대 사회복지대학원 HEART Lab + 서부장애인종합복지관 협력"
- "온쿡 헬로TV 보도 + 발달장애인 클래스 만족도 4.83/5"
- "WCAG AAA 접근성 기준 충족 (UI 모드 3단계)"

❌ **쓰면 안 됨** (정직성 이슈)
- "전문가 5인 패널 검증 완료" (실제로는 Claude 페르소나)
- "발달장애인 100명 사용자 시뮬레이션 4.24/5" (동일 이유)
- "치료 효과 / 진단 가능 / 행동 개선 입증" (의료 영역 아님)
