---
description: v3 백엔드 Render 헬스 + /api/v3 엔드포인트 동작 확인
allowed-tools: Bash(curl:*), Read
argument-hint: (없음)
---

v3 백엔드 배포 상태 진단. JY가 D7 (Render 재배포) 결정할 때 사용.

```bash
URL=https://hibuudy.onrender.com

echo "=== 1. Render 헬스 ==="
curl -s -o /dev/null -w "Status: %{http_code} | Time: %{time_total}s\n" $URL/health || echo "❌ 서버 응답 없음"

echo ""
echo "=== 2. v2 /api/agent (기존 동작) ==="
curl -s -o /dev/null -w "v2 /api/agent: %{http_code}\n" -X POST $URL/api/agent \
  -H "Content-Type: application/json" \
  -d '{"input":"테스트","context":{}}' \
  --max-time 10

echo ""
echo "=== 3. v3 /api/v3/agent (멀티 에이전트 배포 여부) ==="
RESP=$(curl -s -X POST $URL/api/v3/agent \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","session_id":"s1","input":"오늘 뭐 해야 돼?","context":{}}' \
  --max-time 10)
echo "$RESP" | head -c 200
echo ""

if echo "$RESP" | grep -q "selected_agent"; then
  echo "✅ v3 라이브 (선택 에이전트: $(echo $RESP | grep -oE '"agent_name":"[^"]*' | head -1))"
elif echo "$RESP" | grep -q "404"; then
  echo "⚠️ v3 라우터 미배포. USE_V3_ORCHESTRATOR=true 환경변수 설정 필요"
else
  echo "❌ v3 실패: $RESP"
fi

echo ""
echo "=== 4. v3 /api/v3/agent/explain (투명성) ==="
curl -s -X POST $URL/api/v3/agent/explain \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","session_id":"s1","input":"점심에 뭐 먹지?","context":{}}' \
  --max-time 10 | head -c 200
```

읽은 후:
- v2 200 + v3 404 → D7 Render 재배포 필요 (`USE_V3_ORCHESTRATOR=true` 환경변수)
- v2 504/타임아웃 → Render 콜드스타트 (다시 호출 시 살아남)
- v3 200 + selected_agent 있음 → 라이브 동작. 시연/논문에 사용 가능
- v2도 죽었으면 Render 대시보드 가서 상태 확인 필요
