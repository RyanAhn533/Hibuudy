# 하루메이트 docs/ 인덱스

## 종합 문서 (방금 작성, 2026-05-09)
- **[ONE_PAGER.md](ONE_PAGER.md)** — 1장 요약. 발표/공모전 즉시 사용
- **[ARCHITECTURE_FULL.md](ARCHITECTURE_FULL.md)** — 현재 시스템 전체 구조 (15섹션 + 부록)
- **[EVOLUTION.md](EVOLUTION.md)** — 진화사 / changelog (7페이즈 + 기술 매트릭스)
- **[PERSONA_VALIDATION.md](PERSONA_VALIDATION.md)** — NVIDIA Nemotron-Personas-Korea 검증 시스템 디테일 + FAQ + 재현 방법
- **[DESIGN_v1.4_DELIBERATION.md](DESIGN_v1.4_DELIBERATION.md)** — Round 1 deliberation (컨셉「온」 placeholder + HaruTokens v2 spec + AI티 24금지 + 접근성 30체크)
- **[UX_100_ROADMAP.md](UX_100_ROADMAP.md)** — **Round 2** UX/UI 55→90점 5 마일스톤 (컨셉「메이트」 확정, M1 진행 중)
- **[INDEX.md](INDEX.md)** — 이 파일

## 기능별 / 기존 문서
- [privacy_policy.md](privacy_policy.md) / [privacy-policy.html](privacy-policy.html) — 개인정보처리방침 (Play 등록 필수)
- [welfare-center-manual.md](welfare-center-manual.md) — 복지관 매뉴얼 (B2B용)
- [security_audit_checklist.md](security_audit_checklist.md) — 보안 감사 체크리스트
- [tester_invitation.md](tester_invitation.md) — 테스터 초대장
- [b2b-dashboard.html](b2b-dashboard.html) — B2B 대시보드
- [index.html](index.html) — GitHub Pages 랜딩
- [v2_master_plan.md](v2_master_plan.md) — v2 마스터 플랜 (과거 기획)

## 시뮬레이션 / 검증 자료 (역사적 — 외부 사용 X)
> ⚠️ 이하는 Claude 페르소나로 만든 자료. 외부 자료에는 사용 금지.
> 실제 검증은 [v3/simulation/results/](../v3/simulation/results/) 의 NVIDIA Nemotron-Personas-Korea 기반으로 대체.
- expert_panel_review.md
- dd_user_simulation.md
- user_test_simulation.md
- coordinator_ux_walkthrough.md
- persona_*.txt (4개 페르소나 정의)

## 자매 문서 (다른 디렉토리)
- [../README.md](../README.md) — 프로젝트 README
- [../CLAUDE.md](../CLAUDE.md) — VLA 자율 개발 에이전트 설정
- [../STORE_RELEASE_CHECKLIST.md](../STORE_RELEASE_CHECKLIST.md) — 스토어 출시 체크리스트
- [../v3/ARCHITECTURE.md](../v3/ARCHITECTURE.md) — v3.0 멀티 에이전트 설계
- [../v3/personas/stats.json](../v3/personas/stats.json) — 페르소나 필터링 통계
- [../v3/simulation/results/](../v3/simulation/results/) — 시뮬레이션 결과 (run_*.jsonl + report_*.md)

## 빠른 시작 — 누가 어떤 문서부터 보면 되는지
| 역할 | 우선 문서 |
|---|---|
| 처음 보는 사람 | ONE_PAGER → ARCHITECTURE_FULL §1, §13 |
| 심사위원 / 발표 청중 | ONE_PAGER 단독 (1장) |
| 개발자 온보딩 | ARCHITECTURE_FULL §2~§4 + 부록 A 파일 트리 |
| 보안 검토자 | ARCHITECTURE_FULL §7 + security_audit_checklist.md |
| 비즈니스 검토 | ONE_PAGER + ARCHITECTURE_FULL §12 (비용), §13 (차별화) |
| AI/연구 관심 | ARCHITECTURE_FULL §4 (멀티 에이전트), §10 (페르소나) + **PERSONA_VALIDATION.md** + v3/ARCHITECTURE.md |
| 심사위원 (검증 디테일) | **PERSONA_VALIDATION.md** §3 (방법론), §5 (결과), §9 (FAQ) |
| 변천사 궁금 | EVOLUTION.md |
| 복지관 / 기관 | welfare-center-manual.md |
| 테스터 | tester_invitation.md |
