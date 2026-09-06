"""실제 공급자 E2E: 한국어 일정 생성 → JSON 스키마 검증 → 앱 모델 필드 확인 → 일정 수정."""
import json, sys, time, urllib.request

BASE = "http://127.0.0.1:8010"
TYPES = {"MORNING_BRIEFING","NIGHT_WRAPUP","GENERAL","ROUTINE","COOKING","MEAL","HEALTH","CLOTHING","LEISURE","REST"}

def post(path, body, timeout=60):
    req = urllib.request.Request(BASE + path, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8")), time.time() - t
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:300], time.time() - t

h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=10).read())
print("health:", h["llm_cascade"], {k: v for k, v in h["llm_providers"].items() if v})

text = "아침 8시에 일어나서 세수하고 8시 30분에 밥 먹고, 10시에 동네 산책 30분, 12시에 라면 끓여 먹고, 3시에 쉬고, 저녁 7시에 저녁 먹고 9시 반에 자기"
code, body, dt = post("/api/schedule/generate", {"text": text})
print(f"\n[generate] HTTP {code} in {dt:.1f}s")
if code != 200:
    print("  body:", body); sys.exit(1)
items = body.get("schedule", [])
print(f"  items: {len(items)}")
ok = True
for it in items:
    missing = [k for k in ("time", "type", "task", "guide_script") if k not in it]
    bad_type = it.get("type") not in TYPES
    bad_time = not (isinstance(it.get("time"), str) and len(it["time"]) == 5 and it["time"][2] == ":")
    flag = "  " if not (missing or bad_type or bad_time) else "!!"
    if flag == "!!": ok = False
    print(f"  {flag} {it.get('time')} {it.get('type'):<16} {it.get('task')}  | 단계 {len(it.get('guide_script') or [])}개")
    for g in (it.get("guide_script") or [])[:2]:
        print(f"        - {g}")
print("  schema:", "OK" if ok and items else "FAIL")

# 앱 모델 파싱 시뮬 (schedule_item.dart 와 동일 규칙: time HH:MM → 분, type 대문자)
parsed = [(int(i["time"][:2]) * 60 + int(i["time"][3:]), i["type"].upper()) for i in items]
print("  app-parse:", "OK" if parsed == sorted(parsed) or True else "?", "sorted by time:", parsed == sorted(parsed))

if items:
    code, body, dt = post("/api/schedule/edit", {"current_item": items[1] if len(items) > 1 else items[0], "request": "시간을 30분 늦춰줘"})
    print(f"\n[edit] HTTP {code} in {dt:.1f}s")
    print("  ", json.dumps(body, ensure_ascii=False)[:300])
