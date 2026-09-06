"""LLM 캐스케이드 로직 테스트 (네트워크 X — httpx 클라이언트를 가짜로 교체).

실행: cd backend && python -m pytest test_cascade.py -q
검증 범위: 키 없는 공급자 스킵 · 1순위 실패 시 폴백 · 순서 준수 · 마크다운 JSON 정리 · 전부 실패 시 503.
실제 공급자 응답 품질(한국어 일정 JSON)은 키가 있어야 검증 가능 → test_server.py / 수동.
"""
import json
import asyncio
import pytest
from fastapi import HTTPException

import main


class FakeResp:
    def __init__(self, status: int, payload=None, text: str = ""):
        self.status_code = status
        self._payload = payload
        self.text = text or (json.dumps(payload, ensure_ascii=False) if payload is not None else "")

    def json(self):
        return self._payload


class FakeClient:
    """URL 별로 미리 정한 응답을 돌려주고, 호출 순서를 기록."""

    def __init__(self, routes):
        self.routes = routes  # substring of url -> FakeResp
        self.calls = []
        self.is_closed = False

    async def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append(url)
        for key, resp in self.routes.items():
            if key in url:
                return resp
        raise AssertionError(f"unexpected url {url}")


def gemini_ok(text):
    return FakeResp(200, {"candidates": [{"content": {"parts": [{"text": text}]}}]})


def openai_ok(text):
    return FakeResp(200, {"choices": [{"message": {"content": text}}]})


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def keys(monkeypatch):
    def _set(**kw):
        for name in ["GEMINI_API_KEY", "CEREBRAS_API_KEY", "GROQ_API_KEY", "UPSTAGE_API_KEY", "OPENROUTER_API_KEY"]:
            monkeypatch.setattr(main, name, kw.get(name, ""))
    return _set


@pytest.fixture
def fake(monkeypatch):
    def _install(routes):
        client = FakeClient(routes)

        async def _get():
            return client

        monkeypatch.setattr(main, "get_client", _get)
        return client
    return _install


def test_no_keys_returns_503(keys, fake, monkeypatch):
    keys()
    client = fake({})
    monkeypatch.setattr(main, "LLM_CASCADE", ["gemini", "upstage", "groq", "openrouter", "cerebras"])
    with pytest.raises(HTTPException) as e:
        run(main.llm_generate("sys", "user", json_schema={}))
    assert e.value.status_code == 503
    assert client.calls == []  # 키 없으면 네트워크 호출 0


def test_gemini_first_success(keys, fake, monkeypatch):
    keys(GEMINI_API_KEY="g", CEREBRAS_API_KEY="c")
    client = fake({"generativelanguage": gemini_ok('{"schedule": []}')})
    monkeypatch.setattr(main, "LLM_CASCADE", ["gemini", "cerebras"])
    out = run(main.llm_generate("sys", "user", json_schema={}))
    assert json.loads(out) == {"schedule": []}
    assert len(client.calls) == 1 and "generativelanguage" in client.calls[0]
    assert "gemini-2.5-flash" in client.calls[0]  # 2.0-flash 하드코딩 제거 확인


def test_fallback_gemini_500_to_cerebras_with_markdown(keys, fake, monkeypatch):
    keys(GEMINI_API_KEY="g", CEREBRAS_API_KEY="c", GROQ_API_KEY="q")
    client = fake({
        "generativelanguage": FakeResp(500, text="boom"),
        "cerebras": openai_ok('```json\n{"schedule": [{"time": "08:00"}]}\n```'),
        "groq": openai_ok('{"never": true}'),
    })
    monkeypatch.setattr(main, "LLM_CASCADE", ["gemini", "cerebras", "groq"])
    out = run(main.llm_generate("sys", "user", json_schema={}))
    assert json.loads(out)["schedule"][0]["time"] == "08:00"  # 마크다운 펜스 정리됨
    assert [u for u in client.calls if "cerebras" in u] and not [u for u in client.calls if "groq" in u]


def test_skip_missing_keys_respects_order(keys, fake, monkeypatch):
    keys(GROQ_API_KEY="q", OPENROUTER_API_KEY="o")
    client = fake({
        "groq": FakeResp(429, text="rate limited"),
        "openrouter": openai_ok('{"schedule": [{"time": "09:00"}]}'),
    })
    monkeypatch.setattr(main, "LLM_CASCADE", ["gemini", "cerebras", "groq", "upstage", "openrouter"])
    out = run(main.llm_generate("sys", "user", json_schema={}))
    assert json.loads(out)["schedule"][0]["time"] == "09:00"
    assert [("groq" in u) or ("openrouter" in u) for u in client.calls] == [True, True]


def test_all_fail_503(keys, fake, monkeypatch):
    keys(GEMINI_API_KEY="g", GROQ_API_KEY="q")
    client = fake({"generativelanguage": FakeResp(503, text="x"), "groq": FakeResp(500, text="y")})
    monkeypatch.setattr(main, "LLM_CASCADE", ["gemini", "groq"])
    with pytest.raises(HTTPException) as e:
        run(main.llm_generate("sys", "user"))
    assert e.value.status_code == 503 and len(client.calls) == 2


def test_health_exposes_cascade():
    from fastapi.testclient import TestClient
    r = TestClient(main.app).get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and "llm_cascade" in body and "llm_providers" in body
    assert set(body["llm_providers"]) == {"gemini", "cerebras", "groq", "upstage", "openrouter"}
