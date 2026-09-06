#!/usr/bin/env bash
# require_human_gate.sh
# PreToolUse hook for Bash tool. 자동 모드에서 위험 명령 차단.
#
# 출처: claude-research-engine v2 (JY).
# 하루메이트 적응: Windows Python 경로 호환, jsonl 검사 제거, Flutter 도메인 패턴 추가.
#
# Exit 0 = 허용. Exit 2 = 차단.
# JY 동의: (a) 직접 터미널 실행 또는 (b) "confirmed, proceed with <cmd>" 명시.

set -euo pipefail

input=$(cat)

# ── Python 경로 자동 탐색 (Windows + Linux + Mac) ─────────────
PYTHON_CMD=""
for cmd in python3 /c/Users/wnsdu/anaconda3/python.exe python py; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON_CMD="$cmd"
    break
  fi
done

# JSON 파싱 (Python 있으면), 없으면 raw input 사용
if [ -n "$PYTHON_CMD" ]; then
  cmd=$(echo "$input" | "$PYTHON_CMD" -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "$input")
else
  cmd="$input"
fi

# ── 무조건 차단 패턴 ────────────────────────────────────
deny_patterns=(
  'git push --force'
  'git push -f '
  'git push.*-f$'
  'git reset --hard'
  'git branch -D'
  'git checkout -- \.'
  'git restore \.'
  'git clean -f'
  'rm -rf'
  'rm -r '
  'rm -fr'
  # Flutter / 앱 — 키스토어/빌드 자산 보호
  'rm.*\.jks'
  'rm.*key\.properties'
  'rm.*harumate-release'
  'rm.*\.keystore'
  # v3 데이터 보호 (281K 페르소나, 5.8GB)
  'rm.*hf_cache'
  'rm.*harumate_personas\.parquet'
  # ENV / secrets 보호
  'rm.*\.env'
  # 운영 직접 변경 차단
  'render-cli deploy'
  'gradle.*publishRelease'
  'fastlane.*release'
)

for p in "${deny_patterns[@]}"; do
  if echo "$cmd" | grep -qE "$p"; then
    cat >&2 <<EOF
🚫 BLOCKED: "$cmd"

이 명령은 default_policy=human_gate_required 입니다.

진행하려면:
  (a) JY가 다른 터미널에서 직접 실행, 또는
  (b) JY 메시지에 "confirmed, proceed with <command>" 명시 동의

안전 대안:
  rm -rf X          →  mv X X.deleted-\$(date +%s)/
  git reset --hard  →  git stash + git reset --mixed
  git push --force  →  git push --force-with-lease
EOF
    exit 2
  fi
done

# ── "다 적용했다" 사고 방지 경고 (메모리 룰) ─────────────
if echo "$cmd" | grep -qE 'git commit.*(feat|fix|refactor|style)\(.*(ui|theme|widget|screen)'; then
  cat >&2 <<EOF
⚠️ HINT: UI 코드 commit. 'flutter analyze' + 'flutter build apk' 직전 통과 확인했는지?
  메모리 룰 (feedback_apply_means_running.md): 빌드/실행/검증까지 = "적용 완료"
EOF
fi

exit 0
