# .claude/skills — 하루메이트 리뷰 하네스

| 스킬 | 출처 | git 포함 | 용도 |
|---|---|---|---|
| `harumate-cognitive-a11y/` | 자체 (세션 7) | ✅ | 당사자 화면 **인지접근성 12원칙(R1~R12)** 감사. 판정 형식·grep 검사법 포함. 당사자 화면 변경 시 필수 |
| `apple-design/` | [dickwu/apple-design-skill](https://github.com/dickwu/apple-design-skill) vendored | ✅ | Apple HIG 53문서 기반 UI 리뷰어 (Flutter 지원). 구조·터치타겟·타이포 규칙만 차용, 스타일(Liquid Glass 등)은 「메이트」 톤 유지 |
| `_flutter_official/` | [flutter/skills](https://github.com/flutter/skills) | ❌ gitignore | Flutter 공식 스킬 25개 (테스트 추가, 레이아웃 수정, 라우팅 등). 참조용 |
| `_ecc/` | [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) sparse | ❌ gitignore | `flutter-dart-code-review`, `dart-flutter-patterns` 체크리스트 |

## 새 환경에서 gitignore 된 스킬 받기 (선택)

```bash
cd /c/Users/wnsdu/Hibuudy/.claude/skills
git clone --depth 1 https://github.com/flutter/skills.git _flutter_official
git clone --depth 1 --filter=blob:none --sparse https://github.com/affaan-m/everything-claude-code.git _ecc \
  && (cd _ecc && git sparse-checkout set skills/flutter-dart-code-review skills/dart-flutter-patterns)
```

## 리뷰 루틴 (세션 7에서 3라운드로 검증)

1. 구현 → `/ux-screenshot` (빌드·설치·캡처·예외 0)
2. `harumate-cognitive-a11y` 로 12원칙 판정 (Blocker R3/R4/R5/R6 = 0 이어야 commit)
3. `apple-design` 로 레이아웃·접근성·피드백 참조 (references/hig/accessibility.md, layout.md, feedback.md)
4. `/code-review medium <commit>` — 세션 7에서 실제 버그 5건 발견 (v3 인증 우회, Android 11+ tel/sms queries, stale 홈, FAB 겹침, 페이지 오버플로)
5. 수정 → 1 로 돌아가 재검증 → `/ux-commit-check` → commit

## 관련 명령 (`.claude/commands/`)

`/ux-status` (R-grep 포함) · `/ux-screenshot` · `/ux-commit-check` (git add -A 금지) · `/v3-deploy-check`

## hook

`.claude/hooks/require_human_gate.sh` — git push --force / reset --hard / rm -rf / 키스토어·.env 삭제 / Render 직접 배포 차단. 자가 테스트 4/4 통과(세션 7).
**활성화는 `.claude/settings.json` 등록 필요 — Claude Code 가 자기수정 못 하므로 JY 가 직접 (HANDOFF §1).**
