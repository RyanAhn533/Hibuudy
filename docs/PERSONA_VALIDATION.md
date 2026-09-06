# NVIDIA Nemotron-Personas-Korea 기반 페르소나 검증 시스템

> **하루메이트 v3.0의 핵심 차별화 포인트.**
> 클로드로 만든 가짜 "전문가 패널"을 폐기하고, NVIDIA가 한국 통계청 통계로 grounding한 700만 합성 페르소나로 정직한 검증으로 전환한 과정 + 방법론.
>
> **작성일:** 2026-05-09
> **자매 문서:** [ARCHITECTURE_FULL.md §10](ARCHITECTURE_FULL.md), [EVOLUTION.md §1.7](EVOLUTION.md)

---

## 1. 왜 페르소나 검증이 필요한가

### 1.1 사회취약계층 앱의 검증 딜레마

발달장애 당사자 / 보호자 / 복지사 대상 앱을 개발하면 다음 딜레마에 부딪힌다:

| 검증 방법 | 장점 | 한계 |
|---|---|---|
| 실제 사용자 테스트 | 정확함 | **연구윤리 IRB 필요**, 시간/비용/모집 어려움, 초기 검증 단계엔 부적합 |
| 전문가 인터뷰 | 깊이 있음 | 인원 한계, 일반화 어려움 |
| 사용자 평점 | 대규모 가능 | 출시 후에만 가능 |
| **AI 페르소나 시뮬레이션** | 빠르고 대규모 | **신뢰성 + 정직성 이슈** ← 우리가 풀어야 할 문제 |

### 1.2 우리가 처음 했던 실수 (~2026-04)

`docs/expert_panel_review.md`, `docs/dd_user_simulation.md`, `docs/user_test_simulation.md` — Claude API에 "발달장애 당사자 페르소나로 행동해라" 라는 프롬프트로 만든 시뮬레이션. **외부 자료에 "전문가 5인 패널 검증 완료" / "사용자 100명 시뮬레이션 4.24/5" 라고 표기하면 정직성 문제.**

JY가 직접 인지: *"전문가 5인 패널은 내가 클로드로 페르소나 만들어서 진행한거잖아"* (2026-05-08).

→ **외부 표현 가이드 정립**, 검증 인프라 갈아엎음.

---

## 2. NVIDIA Nemotron-Personas-Korea 란?

### 2.1 데이터셋 메타

| 항목 | 값 |
|---|---|
| 공식 명칭 | NVIDIA Nemotron-Personas-Korea |
| 공개 | 2026-04-20 |
| 출처 | NVIDIA AI (Dr. Hyunwoo Kim) |
| 라이선스 | **CC BY 4.0** (상업/비상업 모두 무료) |
| 형식 | Apache Parquet |
| 호스팅 | Hugging Face (`nvidia/Nemotron-Personas-Korea`) |
| 규모 | **1,000,000 records / 7,000,000 personas** (1 record = 7 페르소나 변형) |
| 토큰 | 1.7B 총 / 1B persona |
| 용량 | 다운로드 캐시 ~5.8 GB |

### 2.2 NVIDIA가 어떻게 만들었나

- **베이스 도구:** Gretel Data Designer (NVIDIA 인수 → NeMo 통합 예정)
- **Grounding 데이터:** 한국 통계청 (KOSTAT) 공식 통계
  - 인구 구조 (성별, 연령, 결혼 상태, 가구 형태)
  - 직업 분포 (한국표준직업분류 기반)
  - 지역 분포 (17개 시도 + 252개 시군구)
  - 학력 분포
- **이름 생성:** 118개 성씨 + 21,400개 이름 → 209,167 unique 풀네임 조합
- **연령 범위:** 19세 이상 성인 (한국 법적 성인)
- **분포 반영:** 2025 기준 한국 인구학 (저출생 + 고령화)

### 2.3 26개 필드 구조

**페르소나 본문 (7개)** — LLM이 통계 + 이름 + 직업 등에서 생성
- `persona` (간결 요약)
- `professional_persona`
- `family_persona`
- `sports_persona`
- `arts_persona`
- `travel_persona`
- `culinary_persona`

**페르소나 속성 (6개)**
- `cultural_background`
- `skills_and_expertise` / `skills_and_expertise_list`
- `hobbies_and_interests` / `hobbies_and_interests_list`
- `career_goals_and_ambitions`

**인구학 + 지역 (12개)**
- `uuid`, `sex`, `age`, `marital_status`, `military_status`
- `family_type`, `housing_type`, `education_level`, `bachelors_field`
- `occupation`, `district` (시군구), `province` (시도), `country`

### 2.4 NVIDIA 멀티국가 시리즈

Nemotron-Personas-Korea는 **Sovereign AI** 이니셔티브의 일부:
- USA · Japan · India · Singapore (with AI Singapore) · Brazil (with WideLabs) · France (with Pleias) · **Korea**
- 각 국가별 통계 grounding으로 "국가별 다양성" 보장

---

## 3. 우리가 어떻게 활용했나 (파이프라인)

### 3.1 전체 흐름

```
[Hugging Face]  nvidia/Nemotron-Personas-Korea (1M records, 5.8GB)
       │
       │ datasets.load_dataset() — 1회 다운로드 → v3/data/hf_cache/
       ▼
[Streaming 진단]  필드 구조 + 샘플 확인 (load 전)
       │
       │ ds.filter(_has_keyword) — 멀티프로세스 (num_proc=4)
       ▼
[Keyword Filter]  발달장애·돌봄·노인 키워드 매칭 (텍스트 8개 필드)
       │
       │ categorize() — 5종 라벨 부여
       ▼
[Categorize]  disability_related / caregiver / elderly / elderly_alone / elderly_keyword
       │
       │ + age >= 65 자동 추가 (키워드 없어도)
       ▼
[Combine + Dedup]  uuid 기준 중복 제거
       │
       │ to_parquet()
       ▼
[Output]  v3/personas/harumate_personas.parquet
          (281,992 rows × 27 cols, ~497 MB)
       │
       ├─→ stats.json (카테고리/연령/지역 분포)
       └─→ 시뮬레이션 입력
```

### 3.2 키워드 필터 (`v3/personas/01_download_and_filter.py`)

매칭 대상: 8개 텍스트 필드 (`persona`, `professional_persona`, `family_persona`, `skills_and_expertise`, `hobbies_and_interests`, `career_goals_and_ambitions`, `occupation`, `bachelors_field`)

**DISABILITY_KEYWORDS (18종)**
```
발달장애, 지적장애, 자폐, 자폐스펙트럼, ASD,
장애인, 장애아, 장애자녀, 다운증후군,
특수교육, 특수학교, 특수아동, 특수교사,
재활, 치료사, 언어치료, 행동치료, 감각통합
```
→ 발달장애 당사자 본인 + 가족 + 종사자 모두 포착

**CAREGIVER_KEYWORDS (9종)**
```
사회복지, 복지사, 돌봄, 요양, 활동지원,
보호자, 케어, 노인복지, 장애인복지
```
→ 사회복지/돌봄 관련 직업군

**ELDERLY_KEYWORDS (4종)** — 키워드 직접 매칭
```
노인, 독거, 치매, 경도인지장애
```

**+ 인구학 기반 자동 라벨**
- `age >= 65` AND `family_type` 에 "1인" 또는 "혼자" 또는 "독거" → `elderly_alone` (독거노인 프록시)
- `age >= 65` 그 외 → `elderly` (일반 노인)

→ 키워드 + 인구학 통계 둘 다 활용해 다층적 라벨링.

### 3.3 데이터셋 결과 (281,992 rows)

| 카테고리 | 단독 | 합산 (다중라벨 포함) |
|---|---|---|
| **disability_related** (발달장애/돌봄 종사자/가족) | 3,779 | **7,055** |
| **caregiver** (사회복지/돌봄) | 37,337 | **49,757** |
| **elderly_alone** (독거노인 프록시) | 47,898 | **49,748** |
| **elderly** (일반 노인) | 178,008 | **240,387** |
| **elderly_keyword** (키워드 노인, 65세 미만) | 1,803 | — |

**연령 분포:**
- 평균: 68.85세
- 중앙값: 70세
- 25/75 백분위: 66 / 78세
- 범위: 19~99세

**지역 분포 (Top 10):**
| 시도 | N | % |
|---|---|---|
| 경기 | 64,959 | 23.0% |
| 서울 | 50,340 | 17.9% |
| 부산 | 21,313 | 7.6% |
| 경상남 | 18,610 | 6.6% |
| 경상북 | 16,993 | 6.0% |
| 인천 | 15,183 | 5.4% |
| 대구 | 13,670 | 4.8% |
| 충청남 | 12,378 | 4.4% |
| 전라남 | 12,189 | 4.3% |
| 전북 | 11,635 | 4.1% |
| 합계 (Top 10) | 237,270 | 84.1% |

→ 한국 통계청 인구 분포와 일치 (수도권 ~40%, 영남 ~25%).

### 3.4 실제 추출된 페르소나 샘플

```
[1] 49세 여성, 경상남 진주
    직업: 언어재활사
    persona: "김원석 씨는 진주에서 단독주택에 거주하며
              환자들에게 신뢰받는 언어재활사로 살아가는,
              내실 있고 안정적인 성향의 중년 남성입니다."
    카테고리: disability_related (언어치료)

[2] 23세 여성, 인천 부평
    직업: 전직 보육교사, 현재 구직중
    persona: "한가은 씨는 부평의 활기찬 시장통 분위기 속에서
              자라난 사교적인 전직 보육교사로,
              이른 결혼 생활의 안정감과 소소한 취향을 쫓는
              20대 여성입니다."
    카테고리: caregiver

[3] 65세 여성, 부산
    직업: 노인 및 장애인 돌봄 서비스 종사원
    persona: "박말수 씨는 부산의 정겨운 인심을 닮아 주변 사람들을
              살뜰히 챙기는 돌봄 노동자로, 온천천 산책과 친구들과의
              반주 한 잔에서 삶의 행복을 찾는 60대 여성입니다."
    카테고리: caregiver, elderly
```

→ **이름 / 거주지 / 사투리 / 생활 디테일 모두 한국 현지화.** Claude로 만든 페르소나와 차원이 다른 정밀도.

---

## 4. 시뮬레이션 시스템 (`v3/simulation/`)

### 4.1 5개 표준 시나리오 (S1~S5)

각 시나리오는 (1) 자연어 입력 + (2) 사용자 컨텍스트 preset 으로 구성.

| ID | 시나리오 | 입력 | Preset |
|---|---|---|---|
| **S1** | 아침 일정 확인 | "오늘 뭐 해야 돼?" | 일정 3개 (09:00 약, 10:00 산책, 13:00 치료실) |
| **S2** | 점심 식사 도움 | "점심에 뭐 먹지?" | 냉장고 (김치, 계란, 밥, 참치) |
| **S3** | 약 복용 | "약 먹을 시간이야?" | 비타민D 현재 시간 ±30분 |
| **S4** | 외출 준비 | "이제 나갈 거야" | 보호자 연락처 |
| **S5** | **위급 상황** | "도와줘 다쳤어" | 비상 연락처 (`emergency: True`) |

### 4.2 Persona → Context 변환

각 페르소나에 대해:

```python
ctx = Context(
    user_id = persona.uuid,
    user_name = persona 이름 추출,
    disability_level = "moderate" if 카테고리에 disability/caregiver
                      else "mild",
    today_schedule = scenario.preset_schedule,
    ingredients = scenario.preset_ingredients,
    medications = scenario.preset_meds,
    contacts = scenario.preset_contacts,
    user_memory = {
        "persona_summary": persona.persona[:200],
        "occupation": persona.occupation,
        "age": persona.age,
        "province": persona.province,
        "family_type": persona.family_type,
        "category": persona.category_str,
    },
)
```

### 4.3 실행

- 페르소나 N명 (균형 샘플링: 4 카테고리에서 N//4 씩)
- × 5 시나리오 = N×5 시뮬레이션
- 각 실행: orchestrator.plan() → execute() → result 캡처
- 결과: `v3/simulation/results/run_{timestamp}.jsonl`

### 4.4 평가 지표 (`02_evaluate.py`)

| 지표 | 측정 방법 |
|---|---|
| **라우팅 정확도** | 시나리오별 expected_agent vs 실제 선택. S1=schedule, S2=meal, S3=health, S4=social, S5=health |
| **응답 적절성** | 응답 길이 + 결과 success 플래그 |
| **장애 친화도** | 어려운 한자어 카운트 (가능/수행/확인/처리/관련/사항/조치/권장) — 0이 우수 |
| **위급 처리** | S5 응답이 "도움/전화/보호자" 키워드 포함 여부 |
| **차분한 어조** | "괜찮/차분/잠시" 키워드 포함 여부 |
| **카테고리별 차이** | disability_related vs caregiver vs elderly_alone vs elderly 별 응답 길이 |

---

## 5. 결과 (2026-05-08, N=48 페르소나 × 5 시나리오 = 240건)

### 5.1 종합 지표

| 항목 | 값 |
|---|---|
| 총 시뮬레이션 | 240 |
| 전체 성공률 | **100%** (240/240) |
| 평균 응답 시간 | 0.1ms (휴리스틱 단계, LLM 없이) |
| 어려운 단어 평균 | **0** |

### 5.2 시나리오별

| 시나리오 | N | 성공률 | 라우팅 정확도 | 평균 응답 길이 | 신뢰도 |
|---|---|---|---|---|---|
| S1 (일정) | 48 | 100% | **100%** | 53.9자 | 0.85 |
| S2 (식사) | 48 | 100% | **100%** | 47자 | 0.85 |
| S3 (약) | 48 | 100% | **100%** | 31자 | 0.9 |
| S4 (외출) | 48 | 100% | **100%** | 12자 | 0.8 |
| S5 (위급) | 48 | 100% | **100%** | 30자 | **1.0** |

### 5.3 위급 처리 (가장 중요)

| 지표 | 값 |
|---|---|
| 도움 호출 언급률 | **100%** |
| 차분한 어조 사용률 | **100%** |
| HealthAgent 자동 라우팅 | **100%** (EMERGENCY priority 1.0 효과) |

→ **위급 키워드 ("도와줘 다쳤어") 가 들어오면 무조건 HealthAgent로 가서 차분한 도움 호출 응답.** 이게 사회취약계층 앱의 안전 보장 핵심.

### 5.4 카테고리별 응답

| 카테고리 | N | 평균 응답 길이 |
|---|---|---|
| disability_related | 60 | 34.4자 |
| caregiver | 65 | 34.4자 |
| elderly_alone | 70 | 35.2자 |
| elderly | 45 | 35.2자 |

→ 카테고리 무관 일관된 짧은 응답 (장애 친화도). 아직 카테고리별 응답 분기는 미구현 (다음 단계).

### 5.5 라우팅 분포 검증

| 에이전트 | 호출 수 | 기대 |
|---|---|---|
| schedule | 48 | 48 (S1) |
| meal | 48 | 48 (S2) |
| health | 96 | 96 (S3 + S5) |
| social | 48 | 48 (S4) |

→ 4 도메인 에이전트가 의도대로 분기 100%.

### 5.6 발견 + 수정 (라우팅 버그)

**1차 시뮬레이션 결과:**
- S3 "약 먹을 시간이야?" → meal로 잘못 라우팅 (`먹` 키워드 충돌)
- S4 "이제 나갈 거야" → schedule로 잘못 라우팅

**수정:** `BaseAgent` 에 `strong_keywords` (0.95 점수) + `weak_keywords` 분리. health에 `약 `, `약을`, `약먹` 추가. social에 `나갈` 강화.

**2차 시뮬레이션 결과:** 라우팅 100%.

→ **시뮬레이션이 실제 버그를 잡아냄.** 이게 페르소나 검증의 가치.

---

## 6. 코드 위치

```
v3/
├── personas/
│   ├── 01_download_and_filter.py    ← 다운로드 + 키워드 필터
│   ├── 02_inspect.py                ← 검수 + stats.json 생성
│   ├── harumate_personas.parquet    ← 결과 (497MB, 281,992 rows)
│   └── stats.json                   ← 카테고리/연령/지역 분포
├── simulation/
│   ├── 01_run_scenarios.py          ← 5 시나리오 × N 실행
│   ├── 02_evaluate.py               ← 보고서 생성
│   └── results/
│       ├── run_20260508_214122.jsonl     (240건 raw)
│       ├── summary_20260508_214123.json  (정량 지표)
│       └── report_20260508_214123.md     (마크다운 보고서)
└── data/hf_cache/                   ← Hugging Face 캐시 (5.8GB, gitignore)
```

---

## 7. 외부 표현 가이드 (정직성)

### ✅ 써도 됨
- "**LLM 기반 사용자 페르소나 시뮬레이션**을 통한 초기 사용성 점검"
- "**NVIDIA Nemotron-Personas-Korea** (한국 통계청 grounding, CC BY 4.0) 281,992 페르소나에서 **발달장애 가족·돌봄 종사자·독거노인** 카테고리 추출 후 5 시나리오 × N 페르소나 시뮬레이션"
- "라우팅 정확도 100%, 위급 시나리오 도움 호출률 100% 확인"
- "**연세대 사회복지대학원 HEART Lab + 서부장애인종합복지관** 협력 기반 현장 적용 가능성 검토 중"
- "**온쿡 (전신) 헬로TV 보도** + 발달장애인 클래스 만족도 4.83/5"

### ❌ 쓰면 안 됨 (정직성 이슈 / 의료 영역)
- ~~"전문가 5인 패널 검증 완료"~~ — 실제로는 Claude 페르소나
- ~~"발달장애인 사용자 100명 시뮬레이션 평균 4.24/5"~~ — 동일 이유
- ~~"치료 효과 입증"~~ — 의료 영역, 임상 시험 필요
- ~~"진단 가능"~~ — 의료기기법 위반 소지
- ~~"행동 개선 입증"~~ — 학술 검증 필요

### ⚠️ 조심해서 쓰기
- "초기 사용성 점검" / "설계 검증" — OK
- "효과 검증" → "사용성 점검"으로 표현
- "사용자 피드백" → "시뮬레이션 결과"로 명시

---

## 8. 한계 + 다음 단계

### 8.1 현재 한계
- **N이 작음** (48): 이번 검증은 빠른 검증용. 외부 발표/논문은 N=500+ 권장.
- **휴리스틱 평가만**: LLM judge (GPT-4 또는 Claude로 응답 품질 평가) 보강 안 됨.
- **카테고리별 응답 분기 미구현**: 발달장애 당사자 vs 보호자에게 다른 응답 톤 필요. 현재는 동일.
- **실제 사용자 비교 X**: 페르소나 시뮬레이션의 결과가 실제 사용자 행동과 얼마나 일치하는지 검증 필요.

### 8.2 다음 단계
1. **N=500+ 시뮬레이션** — 통계적 유의성 확보
2. **LLM judge 평가 보강** — 응답 품질, 어휘, 안전성 점수화
3. **카테고리별 응답 분기** — `disability_level` + `category` 기반 톤/난이도 조정
4. **실사용자 비교 연구** — 연세대 HEART Lab 협력 시 (IRB 승인 후)
5. **다른 도메인 적용 가능성** — 노인/치매/청소년 세그먼트로 확장

### 8.3 학술/공모전 어필 포인트
- **한국어 + 통계청 grounded 페르소나로 사회취약계층 앱 검증한 첫 사례** (검색 시 동일 사례 부재)
- **CC BY 4.0 데이터셋이라 재현 가능** (논문/오픈소스 친화)
- **위급 처리 100% + 라우팅 100% 정량 지표** (단순 정성 평가 아님)
- **시뮬레이션이 실제 라우팅 버그 잡아낸 사례 있음** (S3/S4 → 키워드 우선순위 보강)

---

## 9. FAQ (예상 심사위원 질문)

**Q1. 700만 페르소나 다 쓰는 건가?**
> 아니다. 281,992개로 필터링했고, 시뮬레이션은 그 중 N=48 샘플 사용 (균형 샘플링: 4 카테고리에서 N//4씩). 외부 발표는 N=500+ 로 늘릴 계획.

**Q2. NVIDIA가 만든 페르소나가 실제 한국 사람을 정확히 반영하나?**
> 한국 통계청 (KOSTAT) 통계로 grounding되어 있어서 인구학 분포는 정확. 다만 "한 명의 진짜 사람"이 아니라 "한국 통계 분포에서 합성된 다양성 표본"이다. 실제 사용자 검증은 별도 (IRB 후 가능).

**Q3. Claude 페르소나랑 뭐가 다른가?**
> Claude로 만든 페르소나는 **재현 불가** (시드 없음, 모델 버전 따라 다름) + **분포 검증 안됨**. NVIDIA 데이터셋은 **CC BY 4.0 공개 + 통계청 grounding + UUID로 재현 가능**.

**Q4. 시뮬레이션 100%는 너무 좋은데?**
> 라우팅 정확도가 100%인 거지, 응답 품질이 100%인 게 아니다. **현재 평가는 휴리스틱 (키워드 매칭)만**. LLM judge로 응답 품질을 점수화하는 보강 단계 필요. 한계 명시.

**Q5. 발달장애 카테고리 3,779명만 있는데 적지 않나?**
> Single 라벨 기준이며, 다중 라벨까지 포함하면 **7,055명**. 이는 한국 통계청 발달장애인구 비율 (~25만명 / 5천만명 = 0.5%) 의 약 5배에 해당. 충분한 다양성 확보.

---

## 10. 재현 방법 (오픈소스 친화)

```bash
cd /c/Users/wnsdu/Hibuudy

# 1. 의존성 (1회)
pip install datasets huggingface_hub pandas pyarrow

# 2. 데이터셋 다운로드 + 필터링 (~5분, 5.8GB 다운로드 1회)
python v3/personas/01_download_and_filter.py

# 3. 검수 + 통계
python v3/personas/02_inspect.py

# 4. 시뮬레이션 (N=48, ~수초 — 휴리스틱이라 빠름)
python v3/simulation/01_run_scenarios.py 48

# 5. 평가 보고서 생성
python v3/simulation/02_evaluate.py

# 결과
ls v3/simulation/results/
# run_*.jsonl + summary_*.json + report_*.md
```

---

**문서 끝.**
**자매 문서:**
- [ARCHITECTURE_FULL.md §10](ARCHITECTURE_FULL.md) — 시스템 전체 맥락
- [EVOLUTION.md §1.7, §3.4](EVOLUTION.md) — 검증 방법의 진화사
- [v3/ARCHITECTURE.md](../v3/ARCHITECTURE.md) — v3.0 멀티 에이전트 + 페르소나 검증 설계
