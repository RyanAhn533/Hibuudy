"""
백엔드 서버 테스트 스크립트.

실행 방법:
  1. cd backend
  2. pip install -r requirements.txt
  3. cp .env.example .env  (API 키 입력)
  4. uvicorn main:app --reload &
  5. python test_server.py
"""

import httpx
import sys

BASE_URL = "http://localhost:8000"
# .env에서 APP_AUTH_TOKEN과 동일한 값을 넣어야 합니다
TOKEN = "your-secure-random-token-here"

headers = {"Authorization": f"Bearer {TOKEN}"}


def test_health():
    r = httpx.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    print("[PASS] health check")


def test_auth_required():
    r = httpx.post(f"{BASE_URL}/api/schedule/generate", json={"text": "test"})
    assert r.status_code == 401
    print("[PASS] auth required (401 without token)")


def test_schedule_generate():
    r = httpx.post(
        f"{BASE_URL}/api/schedule/generate",
        headers=headers,
        json={"text": "08:00 아침 인사\n12:00 라면 먹기\n18:00 운동하기"},
        timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert "schedule" in data
    assert len(data["schedule"]) >= 3
    print(f"[PASS] schedule generate ({len(data['schedule'])} items)")


def test_schedule_edit():
    r = httpx.post(
        f"{BASE_URL}/api/schedule/edit",
        headers=headers,
        json={
            "current_item": {
                "time": "12:00",
                "type": "COOKING",
                "task": "라면 먹기",
                "guide_script": ["물 끓이기", "면 넣기"],
            },
            "request": "시간을 13:00으로 변경",
        },
        timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert "time" in data or "task" in data
    print(f"[PASS] schedule edit")


def test_tts():
    r = httpx.post(
        f"{BASE_URL}/api/tts",
        headers=headers,
        json={"text": "안녕하세요, 하이버디입니다."},
        timeout=30,
    )
    assert r.status_code == 200
    assert len(r.content) > 1000  # at least 1KB of audio
    print(f"[PASS] TTS ({len(r.content)} bytes)")

    # Test caching - second request should be faster
    r2 = httpx.post(
        f"{BASE_URL}/api/tts",
        headers=headers,
        json={"text": "안녕하세요, 하이버디입니다."},
        timeout=10,
    )
    assert r2.status_code == 200
    assert len(r2.content) == len(r.content)
    print(f"[PASS] TTS cache hit (same size: {len(r2.content)} bytes)")


def test_youtube():
    r = httpx.get(
        f"{BASE_URL}/api/youtube/search",
        headers=headers,
        params={"q": "라면 만들기", "maxResults": 2},
        timeout=15,
    )
    assert r.status_code == 200
    results = r.json()
    assert len(results) > 0
    assert "videoId" in results[0]
    print(f"[PASS] YouTube search ({len(results)} results)")


def test_image():
    r = httpx.get(
        f"{BASE_URL}/api/image/search",
        headers=headers,
        params={"q": "라면", "maxResults": 2},
        timeout=15,
    )
    assert r.status_code == 200
    results = r.json()
    assert len(results) > 0
    assert "link" in results[0]
    print(f"[PASS] Image search ({len(results)} results)")


if __name__ == "__main__":
    print(f"Testing server at {BASE_URL}...\n")

    tests = [
        test_health,
        test_auth_required,
        test_schedule_generate,
        test_schedule_edit,
        test_tts,
        test_youtube,
        test_image,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1

    print(f"\n{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
