"""
Hi-Buddy Backend Proxy Server
─────────────────────────────
API 키를 서버에서만 관리하고, Flutter 앱은 이 서버만 호출합니다.

LLM: environment-configured provider cascade; account limits require verification.
TTS: Edge TTS; deployment and provider policy require separate verification.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Annotated, Literal
from datetime import date as CalendarDate
from contextlib import closing, contextmanager

import edge_tts
import httpx
from response_evaluator import evaluate_schedule, generate_retry_feedback
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, ConfigDict, ValidationError
from contracts import DraftItem, DraftResponse, PlanEnvelope
from device_store import DeviceStore
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

if os.getenv('HIBUDDY_SKIP_DOTENV', 'false').lower() != 'true':
    load_dotenv()

DATA_DIR = Path(os.getenv('HIBUDDY_DATA_DIR', str(Path(__file__).parent / '.data'))).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
if os.getenv('HIBUDDY_REQUIRE_PERSISTENT_STORAGE', 'false').lower() == 'true' and not os.getenv('HIBUDDY_DATA_DIR'):
    raise RuntimeError('HIBUDDY_DATA_DIR must point to the mounted persistent disk')
LOCAL_DRAFT_MODE = os.getenv('HIBUDDY_LOCAL_DRAFT', 'false').lower() == 'true'
if LOCAL_DRAFT_MODE and os.getenv('ENVIRONMENT', '').lower() == 'production':
    raise RuntimeError('Local draft mode is forbidden in production')
device_store = DeviceStore(DATA_DIR / 'devices.db')

# ── Config ──────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "") or GOOGLE_API_KEY
APP_AUTH_TOKEN = os.getenv("APP_AUTH_TOKEN", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
# Official deprecations table read 2026-10-29 (page updated 2026-10-22 UTC):
# 2.5-flash has no shutdown date, but "we are limiting access to the 2.5 models
# to users who have actively used them in the past"; new projects are pointed
# to 3.5 Flash-Lite or 3.8 Flash. gemini-3.8-flash: stable, no shutdown date.
# https://ai.google.dev/gemini-api/docs/deprecations
# https://ai.google.dev/gemini-api/docs/models
# 모델 교체는 코드 수정 없이 Render ENV GEMINI_MODEL 로.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# llama-3.3-70b-versatile ended 2026-08-16 for free/developer tiers;
# committed-spend enterprise has an exception. Check account-specific availability.
# https://console.groq.com/docs/deprecations (checked 2026-10-11)
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# ── OpenAI 호환 공급자 (과거 조사는 docs/COMPETITIVE_TECH_ROADMAP 참고) ──
# 순서는 ENV LLM_CASCADE 로 조정. 키 없는 공급자는 자동 스킵.
# Pricing, credits, quotas and account access have not been live-tested in this
# review. Historical smoke tests do not establish current availability or quality.
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL", "gpt-oss-120b")
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")
# solar-pro3 ends 2026-10-30 KST; solar-pro4 synthetic chat/draft checked 2026-10-14.
# Re-read 2026-10-29: solar-pro4 current; solar-pro3/pro2/mini deprecated 2026-10-30 KST.
# https://console.upstage.ai/docs/capabilities/generate/reasoning
UPSTAGE_MODEL = os.getenv("UPSTAGE_MODEL", "solar-pro4")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")
LLM_CASCADE = [
    x.strip() for x in os.getenv("LLM_CASCADE", "gemini,upstage,groq,openrouter,cerebras").split(",") if x.strip()
]

# Edge TTS 한국어 음성 (여성: ko-KR-SunHiNeural, 남성: ko-KR-InJoonNeural)
EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "ko-KR-SunHiNeural")

# TTS cache directory
TTS_CACHE_DIR = DATA_DIR / 'tts_cache'
TTS_CACHE_DIR.mkdir(exist_ok=True)

# ── FastAPI + Rate Limiter ──────────────────────────────────────────

app = FastAPI(title="Hi-Buddy API", docs_url=None, redoc_url=None, openapi_url=None)
# Public compatibility metadata only; this is not a model-readiness claim.
API_CONTRACT = 'hibuddy-device-v1'
PLAN_SCHEMA_VERSION = 1


def rate_limit_key(request: Request) -> str:
    """Use only a DB-authenticated identity; public endpoints retain IP limits.

    FastAPI resolves verify_token before the endpoint's SlowAPI decorator runs.
    Never key a bucket from caller-supplied headers, tokens, or device IDs.
    A missing verified identity safely falls back to the shared IP bucket.
    """
    device_id = getattr(request.state, 'verified_device_id', None)
    if device_id is not None:
        return 'device:' + device_id
    return 'ip:' + get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return detailed validation errors instead of generic 'error parsing body'."""
    return JSONResponse(
        status_code=422,
        content={"detail": [{"loc": e['loc'], "msg": e['msg'], "type": e['type']} for e in exc.errors()]},
    )


@app.on_event("startup")
async def startup():
    logger.info("Hi-Buddy API started successfully")
    logger.info('Device authentication required; storage directory configured: %s', bool(os.getenv('HIBUDDY_DATA_DIR')))


# ── Auth Dependency ─────────────────────────────────────────────────


def verify_token(request: Request):
    """Opaque, revocable device credential. Missing configuration never bypasses auth."""
    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    if scheme != 'Bearer':
        raise HTTPException(401, '기기 인증이 필요해요.')
    device = device_store.authenticate(token)
    request.state.verified_device_id = device['id']
    return device


def verify_admin_token(request: Request):
    if not APP_AUTH_TOKEN or request.headers.get('Authorization') != f'Bearer {APP_AUTH_TOKEN}':
        raise HTTPException(status_code=401, detail="인증 실패")


class EnrollmentRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: Literal['coordinator', 'self']


class PairAcceptRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    code: str = Field(pattern=r'^\d{6}$')


@app.post('/api/devices/enroll')
@limiter.limit('10/minute')
async def enroll_device(request: Request, body: EnrollmentRequest):
    return device_store.enroll(body.role)


@app.delete('/api/devices/current')
async def revoke_device(device=Depends(verify_token)):
    device_store.revoke_device(device)
    return {'revoked': True}


@app.post('/api/pairing/code')
@limiter.limit('5/minute')
async def create_pair_code(request: Request, device=Depends(verify_token)):
    return device_store.offer(device)


@app.post('/api/pairing/accept')
@limiter.limit('5/minute')
async def accept_pair_code(request: Request, body: PairAcceptRequest, device=Depends(verify_token)):
    return device_store.accept(device, body.code)


@app.get('/api/pairing/status')
async def pairing_status(device=Depends(verify_token)):
    return {'device_id': device['id'], 'role': device['role'], 'links': device_store.links(device)}


@app.delete('/api/pairing/{link_id}')
async def revoke_pair(link_id: str, device=Depends(verify_token)):
    device_store.revoke(device, link_id)
    return {'revoked': True}


# ── v3 멀티 에이전트 라우터 (옵트인, 기본 OFF) ───────────────────────
# HANDOFF §2: USE_V3_ORCHESTRATOR=true 일 때만 마운트. v3/ 는 backend/ Docker 컨텍스트 밖이라
# Render 에서는 명시적으로 켰을 때만 시도하고, 실패하면 조용히 넘기지 않고 부팅을 막는다.
# 모든 v3 엔드포인트는 v2 와 동일한 bearer 인증(verify_token)을 라우터 레벨로 강제.
if os.getenv("USE_V3_ORCHESTRATOR", "false").lower() == "true":
    raise RuntimeError('The legacy v3 memory demo is unsupported; keep USE_V3_ORCHESTRATOR=false')


# ── Input Sanitization ──────────────────────────────────────────────

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def sanitize(text: str, max_length: int = 2000) -> str:
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    return _CONTROL_CHARS.sub("", text)


# ── Shared HTTP Client ──────────────────────────────────────────────

_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


@app.on_event("shutdown")
async def shutdown():
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()


# ── Safe Error Handling ─────────────────────────────────────────────


def raise_for_upstream(resp: httpx.Response, service: str):
    """upstream API 에러를 안전하게 변환 (키 노출 방지)."""
    if resp.status_code == 200:
        return
    code = resp.status_code
    # Provider bodies and exception strings can echo private input or credentials.
    # Log only a fixed provider label and status, never a body or request URL.
    logger.warning("Upstream %s status=%s", service, code)
    messages = {
        401: f"{service}: 인증 실패",
        403: f"{service}: 접근 거부",
        429: f"{service}: 요청 한도 초과 - 잠시 후 다시 시도하세요.",
    }
    if code in messages:
        raise HTTPException(status_code=code, detail=messages[code])
    if code >= 500:
        raise HTTPException(status_code=502, detail=f"{service}: 외부 서버 오류")
    raise HTTPException(status_code=502, detail=f"{service}: 외부 요청 처리 실패")


# ── Gemini API Helper ───────────────────────────────────────────────


def completed_provider_text(resp, provider: str) -> str:
    """Only a normally finished text answer can become a successful reply.

    Provider HTTP200 also includes truncation, filtering and tool requests.
    Thinking blocks are never used as the user-facing answer.
    """
    try:
        data = resp.json()
        if provider == 'gemini':
            candidate = data['candidates'][0]
            if candidate.get('finishReason') != 'STOP':
                raise ValueError('incomplete Gemini response')
            parts = candidate['content']['parts']
            if not isinstance(parts, list):
                raise ValueError('invalid Gemini parts')
            pieces = []
            for part in parts:
                if part.get('thought') is True:
                    continue
                valid_response_text(part['text'])
                pieces.append(part['text'])
            text = ''.join(pieces)
        elif provider == 'claude':
            if data.get('stop_reason') != 'end_turn':
                raise ValueError('incomplete Claude response')
            if not isinstance(data['content'], list):
                raise ValueError('invalid Claude content')
            pieces = []
            for block in data['content']:
                if block.get('type') in {'thinking', 'redacted_thinking'}:
                    continue
                if block.get('type') != 'text':
                    raise ValueError('nontext Claude block')
                valid_response_text(block['text'])
                pieces.append(block['text'])
            text = ''.join(pieces)
        else:
            choice = data['choices'][0]
            if choice.get('finish_reason') != 'stop':
                raise ValueError('incomplete OpenAI-compatible response')
            message = choice['message']
            if message.get('tool_calls') or message.get('refusal') is not None:
                raise ValueError('nontext completion')
            text = message['content']
        return valid_response_text(text)
    except (ValueError, KeyError, IndexError, TypeError, AttributeError, HTTPException):
        # Fixed error only; provider body/reasoning/credentials must not escape.
        raise HTTPException(502, f'{provider}: 완성된 텍스트 응답을 확인하지 못했어요.') from None


async def gemini_generate(
    system_prompt: str,
    user_text: str,
    response_schema: dict = None,
    json_mode: bool = True,
    max_tokens: int = 800,
) -> str:
    """Configured Gemini model call. json_mode=False returns natural text."""
    generation_config = {
        "temperature": 0.7 if not json_mode else 0.15,
        "maxOutputTokens": max_tokens,
    }
    if json_mode:
        generation_config["responseMimeType"] = "application/json"
        if response_schema:
            generation_config["responseSchema"] = response_schema

    client = await get_client()
    resp = await client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_text}]}],
            "generationConfig": generation_config,
        },
    )
    raise_for_upstream(resp, "Gemini")
    raw_text = completed_provider_text(resp, 'gemini')
    return valid_response_text(_clean_json_response(raw_text)) if json_mode else raw_text


# ── OpenAI 호환 공급자 헬퍼 (Groq / Cerebras / Upstage / OpenRouter) ──────────

OPENAI_COMPAT_PROVIDERS: dict[str, dict] = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": lambda: GROQ_API_KEY,
        "model": lambda: GROQ_MODEL,
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "key": lambda: CEREBRAS_API_KEY,
        "model": lambda: CEREBRAS_MODEL,
    },
    "upstage": {
        "url": "https://api.upstage.ai/v1/chat/completions",
        "key": lambda: UPSTAGE_API_KEY,
        "model": lambda: UPSTAGE_MODEL,
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key": lambda: OPENROUTER_API_KEY,
        "model": lambda: OPENROUTER_MODEL,
    },
}


async def openai_compat_generate(
    provider: str,
    system_prompt: str,
    user_text: str,
    json_mode: bool = False,
    max_tokens: int = 800,
) -> str:
    """OpenAI 호환 chat/completions 호출 → 응답 텍스트. provider 는 OPENAI_COMPAT_PROVIDERS 키."""
    cfg = OPENAI_COMPAT_PROVIDERS[provider]
    key = cfg["key"]()
    if not key:
        raise HTTPException(status_code=503, detail=f"{provider} 키 미설정")

    client = await get_client()
    payload = {
        "model": cfg["model"](),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://hibuudy.onrender.com"
        headers["X-Title"] = "HaruMate"

    resp = await client.post(cfg["url"], headers=headers, json=payload, timeout=30.0)
    raise_for_upstream(resp, provider)

    text = completed_provider_text(resp, provider)
    return valid_response_text(_clean_json_response(text)) if json_mode else text


async def groq_generate(system_prompt: str, user_text: str, json_mode: bool = False, max_tokens: int = 800) -> str:
    """하위 호환 래퍼 (기존 호출부용)."""
    return await openai_compat_generate("groq", system_prompt, user_text, json_mode=json_mode, max_tokens=max_tokens)


async def llm_generate(
    system_prompt: str,
    user_text: str,
    json_schema: dict | None = None,
    json_mode: bool = False,
    max_tokens: int = 800,
) -> str:
    """LLM 캐스케이드: ENV LLM_CASCADE 순서대로 (기본 gemini → upstage → groq → openrouter → cerebras).
    키 없는 공급자는 스킵. 전부 실패하면 503. json_schema 제공 시 자동 json_mode=True."""
    if json_schema is not None:
        json_mode = True

    tried: list[str] = []
    for provider in LLM_CASCADE:
        try:
            if provider == "gemini":
                if not GEMINI_API_KEY:
                    continue
                tried.append(provider)
                return await gemini_generate(
                    system_prompt, user_text, json_schema, json_mode=json_mode, max_tokens=max_tokens
                )
            if provider in OPENAI_COMPAT_PROVIDERS:
                if not OPENAI_COMPAT_PROVIDERS[provider]["key"]():
                    continue
                tried.append(provider)
                return await openai_compat_generate(
                    provider, system_prompt, user_text, json_mode=json_mode, max_tokens=max_tokens
                )
            logger.warning("LLM_CASCADE 에 모르는 공급자: %s", provider)
        except HTTPException as e:
            logger.warning("%s 실패 → 다음 공급자: HTTP %s", provider, e.status_code)
        except Exception as e:
            logger.warning("%s 예외 → 다음 공급자: %s", provider, type(e).__name__)

    logger.error("LLM 캐스케이드 전부 실패 (시도: %s). 키 설정 확인: GEMINI/CEREBRAS/GROQ/UPSTAGE/OPENROUTER", tried)
    raise HTTPException(status_code=503, detail="AI 서비스가 잠시 쉬고 있어요.")


def _clean_json_response(text: str) -> str:
    """Gemini JSON 응답에서 CoT/마크다운 잔재 제거."""
    text = text.strip()
    # ```json ... ``` 블록 추출
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if md_match:
        text = md_match.group(1).strip()
    # 첫 { 또는 [ 앞의 텍스트 제거
    for i, ch in enumerate(text):
        if ch in ('{', '['):
            text = text[i:]
            break
    # 마지막 } 또는 ] 뒤의 텍스트 제거
    for i in range(len(text) - 1, -1, -1):
        if text[i] in ('}', ']'):
            text = text[:i + 1]
            break
    return text


# ══════════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

# ── Health Check ────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "api_contract": API_CONTRACT,
        "plan_schema_version": PLAN_SCHEMA_VERSION,
        "auth": "device",
        "capabilities": {
            "device_enrollment": True,
            "pairing": True,
            "approved_plan_sync": True,
        },
        # A configured path does not prove that the deployment mounted a disk.
        "storage": "configured_directory" if os.getenv('HIBUDDY_DATA_DIR') else "local_development",
        "local_draft": LOCAL_DRAFT_MODE,
        "llm_cascade": LLM_CASCADE,
        "llm_providers": {
            "gemini": bool(GEMINI_API_KEY), "cerebras": bool(CEREBRAS_API_KEY),
            "groq": bool(GROQ_API_KEY), "upstage": bool(UPSTAGE_API_KEY),
            "openrouter": bool(OPENROUTER_API_KEY),
        },
    }


# ── Waitlist (준비 중 세그먼트 이메일 수집) ─────────────────────────

WAITLIST_DB = DATA_DIR / 'waitlist.db'


@contextmanager
def open_database(path):
    # sqlite3.Connection.__exit__ commits/rolls back, but does not close it.
    with closing(sqlite3.connect(str(path))) as conn:
        with conn:
            yield conn


def _init_waitlist_db():
    try:
        with open_database(WAITLIST_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS waitlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    segment TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(email, segment)
                )
            """)
    except Exception as e:
        logger.warning("waitlist db init: %s", e)


_init_waitlist_db()


class WaitlistRequest(BaseModel):
    email: str = Field(..., max_length=200)
    segment: str = Field(..., max_length=50)


@app.post("/api/waitlist")
@limiter.limit("10/minute")
async def add_waitlist(request: Request, body: WaitlistRequest):
    """준비 중인 세그먼트(senior/dementia/youth) 이메일 수집."""
    email = sanitize(body.email, max_length=200)
    seg = sanitize(body.segment, max_length=50)
    if "@" not in email or len(email) < 5:
        raise HTTPException(status_code=400, detail="이메일 형식이 잘못됐어요.")
    try:
        with open_database(WAITLIST_DB) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO waitlist (email, segment) VALUES (?, ?)",
                (email, seg),
            )
            conn.commit()
    except Exception as e:
        logger.warning("waitlist insert: %s", e)
        raise HTTPException(status_code=500, detail="등록 실패")
    return {"status": "ok"}


# ── Error Reporting (경량 Crashlytics 대체) ────────────────────

ERROR_DB = DATA_DIR / 'errors.db'


def _init_error_db():
    try:
        with open_database(ERROR_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    tag TEXT,
                    msg TEXT,
                    stack TEXT,
                    platform TEXT,
                    received_at TEXT DEFAULT (datetime('now'))
                )
            """)
    except Exception as e:
        logger.warning("errors db init: %s", e)


_init_error_db()


@app.post("/api/errors")
@limiter.limit("30/minute")
async def collect_errors(request: Request, _=Depends(verify_token)):
    """Flutter 클라이언트 크래시 로그 수집 (JSONL 형식)."""
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > 65536:
            raise HTTPException(413, '오류 보고 크기가 너무 커요.')
        body.extend(chunk)
    lines = body.decode("utf-8", errors="ignore").strip().split("\n")
    saved = 0
    try:
        with open_database(ERROR_DB) as conn:
            for line in lines:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    conn.execute(
                        "INSERT INTO errors (ts, tag, msg, stack, platform) VALUES (?, ?, ?, ?, ?)",
                        (
                            entry.get("ts", ""),
                            entry.get("tag", "unknown"),
                            entry.get("msg", "")[:500],
                            entry.get("stack", "")[:2000],
                            entry.get("platform", ""),
                        ),
                    )
                    saved += 1
                except Exception:
                    continue
            conn.commit()
    except Exception as e:
        logger.warning("error collect: %s", e)
        return Response(status_code=500)
    return {"saved": saved}


@app.get("/api/metrics")
@limiter.limit("30/minute")
async def metrics(request: Request, _=Depends(verify_admin_token)):
    # slowapi 는 `request` 인자가 없으면 import 시점에 예외 (로컬 최신 slowapi 에서 부팅 실패하던 버그)
    """관리자용 통합 메트릭 (토큰 필요)."""
    result: dict = {
        "ts": __import__("datetime").datetime.utcnow().isoformat(),
        "env": {
            "gemini": bool(GEMINI_API_KEY),
            "groq": bool(GROQ_API_KEY),
            "claude": bool(CLAUDE_API_KEY),
            "auth": bool(APP_AUTH_TOKEN),
        },
    }
    # 에러 수집
    try:
        with open_database(ERROR_DB) as conn:
            result["errors_total"] = conn.execute(
                "SELECT COUNT(*) FROM errors"
            ).fetchone()[0]
            result["errors_24h"] = conn.execute(
                "SELECT COUNT(*) FROM errors WHERE datetime(received_at) > datetime('now', '-1 day')"
            ).fetchone()[0]
    except Exception:
        result["errors_total"] = 0
        result["errors_24h"] = 0

    # waitlist
    try:
        with open_database(WAITLIST_DB) as conn:
            result["waitlist_total"] = conn.execute(
                "SELECT COUNT(*) FROM waitlist"
            ).fetchone()[0]
            rows = conn.execute(
                "SELECT segment, COUNT(*) FROM waitlist GROUP BY segment"
            ).fetchall()
            result["waitlist_by_segment"] = {r[0]: r[1] for r in rows}
    except Exception:
        result["waitlist_total"] = 0
        result["waitlist_by_segment"] = {}

    # schedule DB
    try:
        with device_store.conn() as conn:
            result["schedules_stored"] = conn.execute(
                "SELECT COUNT(*) FROM approved_plans"
            ).fetchone()[0]
            result["unique_users"] = conn.execute(
                "SELECT COUNT(DISTINCT owner_id) FROM approved_plans"
            ).fetchone()[0]
    except Exception:
        result["schedules_stored"] = 0
        result["unique_users"] = 0

    return result


@app.get("/api/errors/recent")
async def recent_errors(_=Depends(verify_admin_token), limit: int = 50):
    """관리자용: 최근 에러 조회 (토큰 필요)."""
    try:
        with open_database(ERROR_DB) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM errors ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return {"errors": [dict(r) for r in rows]}
    except Exception:
        return {"errors": []}


@app.get("/api/waitlist/count")
async def waitlist_count(_=Depends(verify_admin_token)):
    """관리자용 집계 (토큰 있을 때만)."""
    try:
        with open_database(WAITLIST_DB) as conn:
            rows = conn.execute(
                "SELECT segment, COUNT(*) FROM waitlist GROUP BY segment"
            ).fetchall()
            return {"counts": {r[0]: r[1] for r in rows}}
    except Exception:
        return {"counts": {}}


# ── 1. Schedule Generation (configured provider cascade) ──────────


class ScheduleRequest(BaseModel):
    text: str = Field(..., max_length=2000)


# 2026-10-11: 활동이 여러 개면 안내가 "10시에 옷 입기 연습을 시작합니다" 같은 한두 문장의
# 되풀이로 나와 따라 할 단계가 없었다. 몸으로 하는 활동은 행동 단계로 나누게 했다.
# 결과는 초안이며 돕는 사람이 확인하고 게시해야 당사자 화면에 나온다.
SCHEDULE_SYSTEM_PROMPT = """너는 성인 발달장애인을 돕는 생활지원 담당자의 보조다.
담당자가 적은 하루 일정을 읽고, 당사자가 보고 따라 할 안내 초안을 JSON 으로 만든다.
출력 스키마: { "schedule": [ { "time": "HH:MM", "type": "TYPE", "task": "할 일", "guide_script": ["1단계","2단계"] } ] }
type은: MORNING_BRIEFING, NIGHT_WRAPUP, GENERAL, ROUTINE, COOKING, MEAL, HEALTH, CLOTHING, LEISURE, REST 중 하나.
task 는 입력한 말을 그대로 쓴다. 옷 입기·갈아입기는 CLOTHING, 씻기·정리는 ROUTINE.

guide_script 규칙:
1. 옷 입기, 씻기, 요리, 식사, 운동, 청소처럼 몸으로 하는 활동(CLOTHING, ROUTINE, COOKING, MEAL, HEALTH, GENERAL)은
   실제로 하는 순서대로 3~5단계로 나눈다. 활동이 여러 개여도 단계를 줄이지 않는다.
2. 한 단계에는 행동 하나만 적는다. 눈에 보이는 물건과 동작으로 쓴다. 예: "윗옷을 머리에 넣어요."
3. 한 단계는 25자 이내, 쉬운 낱말, "~해요"로 끝낸다.
4. 어떤 활동이든 시각이나 활동 이름을 되풀이하지 않는다. "10시에 옷 입기를 시작합니다", "아침 8시에 일정을 알려드려요" 같은 문장은 쓰지 않는다.
5. 입력에 없는 물건·음식·장소, 조리 시간·분량 같은 숫자를 지어내지 않는다. 모르면 "준비된 옷을 꺼내요"처럼 넓게 쓴다.
6. 고를 것이 있으면(예: 라면 또는 카레) 첫 단계를 "먹고 싶은 것을 골라요"처럼 고르는 단계로 쓰고,
   그다음 단계는 어느 쪽을 골라도 맞는 말로 쓴다. 예: "고른 음식을 준비해요." 두 가지를 섞어 쓰지 않는다.
7. 인사와 쉬는 시간(MORNING_BRIEFING, NIGHT_WRAPUP, REST, LEISURE)은 1~2문장으로 짧게 쓴다.
8. 평가, 훈계, 건강·의료 조언을 쓰지 않는다. 앱이 직접 도와준다는 말도 쓰지 않는다.
한국어만. JSON만 출력. 설명이나 주석 절대 추가하지 마라."""

SCHEDULE_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "schedule": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "time": {"type": "STRING"},
                    "type": {"type": "STRING"},
                    "task": {"type": "STRING"},
                    "guide_script": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                    },
                },
                "required": ["time", "type", "task", "guide_script"],
            },
        }
    },
    "required": ["schedule"],
}


@app.post("/api/schedule/generate")
@limiter.limit("10/minute")
async def generate_schedule(request: Request, body: ScheduleRequest, _=Depends(verify_token)):
    text = sanitize(body.text)
    if not text:
        raise HTTPException(status_code=400, detail="일정 내용을 입력해 주세요.")

    # 캐스케이드: Gemini → Groq → 503
    # 활동마다 3~5단계가 나오므로 기본 800 토큰으로는 하루 일정이 잘릴 수 있다
    if LOCAL_DRAFT_MODE:
        items = []
        for line in text.splitlines():
            match = re.match(r'\s*([0-2]\d:[0-5]\d)\s+(.+)', line)
            if match:
                task = match.group(2).strip()
                items.append({'time': match.group(1), 'type': 'GENERAL', 'task': task, 'guide_script': ['필요한 것을 준비해요.', '안내를 보며 천천히 해요.', '사용한 것을 정리해요.']})
        if not items:
            raise HTTPException(400, '로컬 시험에서는 08:00 할 일 형식으로 입력해 주세요.')
        return DraftResponse.model_validate({'schedule': items}).model_dump()
    content = await llm_generate(
        SCHEDULE_SYSTEM_PROMPT, text, json_schema=SCHEDULE_RESPONSE_SCHEMA, max_tokens=2000
    )

    try:
        validated = DraftResponse.model_validate_json(content)
    except (ValueError, ValidationError):
        raise HTTPException(status_code=502, detail="일정 생성: 안내 형식이 올바르지 않아요.")
    return validated.model_dump()


# ── 2. Schedule Edit (configured provider cascade) ────────────────


class EditRequest(BaseModel):
    current_item: dict
    request: str = Field(..., max_length=500)


EDIT_SYSTEM_PROMPT = """너는 일정표를 수정하는 코디네이터 도우미다.
사용자 요청에 따라 time(HH:MM), task, type, guide_script를 수정한다.
반드시 JSON만 출력. 한국어만. 기존 의미를 최대한 유지.
활동이나 type이 바뀌면 guide_script도 새 활동에 맞게 전부 다시 작성한다. 이전 활동의 단계를 그대로 두지 않는다.
type: MORNING_BRIEFING, NIGHT_WRAPUP, GENERAL, ROUTINE, COOKING, MEAL, HEALTH, CLOTHING, LEISURE, REST"""


@app.post("/api/schedule/edit")
@limiter.limit("10/minute")
async def edit_schedule(request: Request, body: EditRequest, _=Depends(verify_token)):
    edit_text = sanitize(body.request, max_length=500)
    if not edit_text:
        raise HTTPException(status_code=400, detail="수정 요청을 입력해 주세요.")

    try:
        current = DraftItem.model_validate(body.current_item).model_dump()
    except ValidationError:
        raise HTTPException(422, '수정할 안내 형식이 올바르지 않아요.')
    user_msg = f"현재 항목 JSON:\n{json.dumps(current, ensure_ascii=False)}\n\n수정 요청: {edit_text}"

    if LOCAL_DRAFT_MODE:
        updated = DraftItem.model_validate(body.current_item).model_dump()
        match = re.search(r'([0-2]\d:[0-5]\d)', edit_text)
        if not match:
            raise HTTPException(503, '로컬 시험의 AI 수정은 시각 변경만 지원해요. 안내는 직접 고쳐 주세요.')
        updated['time'] = match.group(1)
        return DraftItem.model_validate(updated).model_dump()
    content = await llm_generate(EDIT_SYSTEM_PROMPT, user_msg, json_schema={})
    try:
        validated = DraftItem.model_validate_json(content)
    except (ValueError, ValidationError):
        raise HTTPException(status_code=502, detail="일정 수정: 안내 형식이 올바르지 않아요.")
    if (validated.task != body.current_item.get('task') or validated.type != body.current_item.get('type')) and validated.guide_script == body.current_item.get('guide_script'):
        raise HTTPException(502, '활동이 바뀌었지만 안내는 그대로예요. 다시 요청해 주세요.')
    return validated.model_dump()


# ── 3. Claude Agent Proxy (발달장애인 생활 에이전트) ─────────────


class AgentContext(BaseModel):
    """Public app catalog only. Personal records are handled on the device."""
    model_config = ConfigDict(extra='forbid', strict=True)
    available_recipes: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(default_factory=list, max_length=100)


class AgentRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    input: str = Field(..., max_length=500)
    context: AgentContext | None = None


AGENT_SYSTEM_TEMPLATE = """너는 쉬운 말로 안내하는 하루 도우미다.
따뜻하게, 짧게, 존댓말로 대답해라.

규칙:
1. 한 문장은 20~45자 이내.
2. 전체 답은 3문장 이내.
3. 어려운 단어 금지. "추가" 대신 "넣기", "삭제" 대신 "지우기".
4. 격려는 담백하게. 이모지 🎉 금지.
5. 아래 목록은 앱에서 볼 수 있는 레시피 제목이며 집에 재료가 있다는 뜻은 아니다. 재료가 있다고 추측하지 않는다.
6. 감정 대화는 공감 먼저, 조언은 묻기 전까지 하지 않는다.
7. 전화·저장·도움 요청을 실행할 수 없다. 실행했거나 실행 중이라고 말하지 않는다.
8. 필요한 도움과 선택은 물어서 확인한다. 진단명이나 장애 정도를 추측하지 않는다.

앱 레시피 목록: {recipes}

JSON으로 응답하지 말고, 자연스러운 한국어 문장만 출력해라."""


@app.post("/api/agent")
@limiter.limit("20/minute")
async def agent_chat(request: Request, body: AgentRequest, _t=Depends(verify_token)):
    """맥락 기반 대화 에이전트.
    CLAUDE_API_KEY가 있으면 Claude를 먼저 시도하고 설정된 캐스케이드로 대체한다.
    """
    user_input = sanitize(body.input, max_length=500)
    if not user_input:
        raise HTTPException(status_code=400, detail="무엇을 물어볼지 적어주세요.")

    ctx = body.context or AgentContext()
    system_prompt = AGENT_SYSTEM_TEMPLATE.format(
        recipes=", ".join(ctx.available_recipes) or "(목록 없음)",
    )

    # Claude (키가 있으면) 이후에는 LLM_CASCADE의 실제 설정 순서를 따른다.
    if CLAUDE_API_KEY:
        client = await get_client()
        try:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 400,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_input}],
                },
                timeout=20.0,
            )
            if resp.status_code == 200:
                return {"text": completed_provider_text(resp, 'claude')}
            logger.warning("Claude %s → configured cascade fallback", resp.status_code)
        except Exception as e:
            logger.warning("Claude exception → configured cascade: %s", type(e).__name__)

    # 설정된 공급자 순서로 자연 한국어 응답을 요청한다.
    text = await llm_generate(
        system_prompt, user_input,
        json_schema=None, json_mode=False, max_tokens=400,
    )
    return {"text": valid_response_text(text)}


def valid_response_text(text):
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(502, 'AI 응답이 비어 있거나 올바르지 않아요.')
    return text.strip()


# ── 3.5 옷 추천 (AI) ────────────────────────────────────────────


class ClothingRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    temp: float = Field(ge=-70, le=70, allow_inf_nan=False)
    description: str = Field(default="", max_length=50)


CLOTHING_PROMPT = """너는 따뜻한 생활 도우미야.
날씨 정보를 받고, 입을 옷을 한 문장으로 제안해라.

규칙:
1. 한 문장. 20~35자.
2. 존댓말. 감탄사 절제.
3. 사람의 이름이나 건강 상태를 추측하지 않는다.
4. 기술 용어 금지. 쉬운 단어만.
5. 옷 1~2개만 언급 (나열 금지).

예시:
- 쌀쌀해요. 가디건 챙기세요.
- 비 와요. 우산 꼭 챙기세요.
- 따뜻해요. 반팔이 좋겠어요."""


@app.post("/api/clothing")
@limiter.limit("30/minute")
async def clothing_advice(request: Request, body: ClothingRequest, _t=Depends(verify_token)):
    """온도·날씨만 이용하는 옷 제안 (AI)."""
    user_msg = (
        f"기온: {body.temp}도\n"
        f"날씨: {body.description or '보통'}"
    )

    try:
        text = await llm_generate(
            CLOTHING_PROMPT, user_msg,
            json_schema=None, json_mode=False, max_tokens=80,
        )
        return {"text": valid_response_text(text)}
    except Exception:
        # 폴백: 템플릿
        temp = body.temp
        if temp <= 5:
            tip = "코트나 패딩 입으세요."
        elif temp <= 10:
            tip = "쌀쌀해요. 가디건 챙기세요."
        elif temp <= 20:
            tip = "긴팔이 좋겠어요."
        elif temp <= 25:
            tip = "반팔이면 딱이에요."
        else:
            tip = "시원한 옷이 좋아요."
        return {"text": tip}


# ── 4. TTS (Edge TTS — 완전 무료) ─────────────────────────────────


class TtsRequest(BaseModel):
    text: str = Field(..., max_length=4096)


@app.post("/api/tts")
@limiter.limit("30/minute")
async def synthesize_tts(request: Request, body: TtsRequest, _=Depends(verify_token)):
    if LOCAL_DRAFT_MODE:
        raise HTTPException(503, '로컬 시험에서는 기기 음성을 이용해 주세요.')
    text = sanitize(body.text, max_length=4096)
    if not text:
        raise HTTPException(status_code=400, detail="읽어줄 텍스트가 없습니다.")

    # Check cache
    cache_key = hashlib.sha256(text.encode()).hexdigest()
    cache_path = TTS_CACHE_DIR / f"{cache_key}.mp3"
    if cache_path.exists():
        return Response(content=cache_path.read_bytes(), media_type="audio/mpeg")

    # Edge TTS 합성 (edge-tts 7.x pattern with stream)
    try:
        communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE, rate="-10%")
        with open(str(cache_path), "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
    except Exception as e:
        logger.warning("Edge TTS error: %s", type(e).__name__)
        # 폴백: 파일 정리
        try:
            if cache_path.exists():
                cache_path.unlink()
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"TTS: 음성 합성 실패 ({type(e).__name__})")

    if not cache_path.exists() or cache_path.stat().st_size < 100:
        try:
            if cache_path.exists():
                cache_path.unlink()
        except Exception:
            pass
        raise HTTPException(status_code=502, detail="TTS: 파일 생성 실패 (empty)")

    return Response(content=cache_path.read_bytes(), media_type="audio/mpeg")


# ── 4. YouTube Search ───────────────────────────────────────────────


@app.get("/api/youtube/search")
@limiter.limit("20/minute")
async def search_youtube(
    request: Request,
    q: str = Query(..., max_length=200),
    maxResults: int = Query(default=4, ge=1, le=10),
    _=Depends(verify_token),
):
    query = sanitize(q, max_length=200)
    if not query:
        return []

    client = await get_client()
    resp = await client.get(
        "https://www.googleapis.com/youtube/v3/search",
        params={
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": maxResults,
            "key": YOUTUBE_API_KEY,
        },
    )
    raise_for_upstream(resp, "YouTube")

    data = resp.json()
    items = data.get("items", [])
    results = []
    for item in items:
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId", "")
        results.append(
            {
                "title": snippet.get("title", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "videoId": video_id,
            }
        )
    return results


# ── 5. Google Image Search ──────────────────────────────────────────


@app.get("/api/image/search")
@limiter.limit("20/minute")
async def search_images(
    request: Request,
    q: str = Query(..., max_length=200),
    maxResults: int = Query(default=4, ge=1, le=10),
    _=Depends(verify_token),
):
    query = sanitize(q, max_length=200)
    if not query:
        return []

    client = await get_client()
    resp = await client.get(
        "https://www.googleapis.com/customsearch/v1",
        params={
            "q": query,
            "searchType": "image",
            "num": maxResults,
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "safe": "active",
        },
    )
    raise_for_upstream(resp, "Google Image")

    data = resp.json()
    items = data.get("items", [])
    results = []
    for item in items:
        results.append(
            {
                "link": item.get("link", ""),
                "thumbnail": item.get("image", {}).get("thumbnailLink", ""),
                "title": item.get("title", ""),
            }
        )
    return results


# ── 6. Recipes & Health Routines ──────────────────────────────────

RECIPES_FILE = Path(__file__).parent.parent / "hi_buddy_app" / "assets" / "data" / "recipes.json"


@app.get("/api/recipes")
@limiter.limit("30/minute")
async def get_recipes(request: Request, _=Depends(verify_token)):
    """레시피 및 운동 루틴 JSON 반환.
    향후 DB로 마이그레이션 시 이 엔드포인트만 수정하면 됨."""
    if not RECIPES_FILE.exists():
        raise HTTPException(status_code=404, detail="레시피 파일을 찾을 수 없습니다.")
    data = json.loads(RECIPES_FILE.read_text(encoding="utf-8"))
    return data


# ── 7. Schedule Persistence (SQLite) ──────────────────────────────

@app.post("/api/schedule/save")
@limiter.limit("20/minute")
async def save_schedule(request: Request, body: PlanEnvelope, device=Depends(verify_token)):
    device_store.save(device, body.model_dump())
    return {'status': 'ok', 'plan_id': body.plan.id, 'version_number': body.plan.version_number}


@app.get("/api/schedule/load")
@limiter.limit("30/minute")
async def load_schedule(
    request: Request,
    date: str = Query(default="", max_length=10),
    device=Depends(verify_token),
):
    if 'user_id' in request.query_params:
        raise HTTPException(422, 'user_id 조회는 지원하지 않아요. 연결된 기기로 조회해 주세요.')
    if date:
        try:
            CalendarDate.fromisoformat(date)
        except ValueError:
            raise HTTPException(422, '날짜가 올바르지 않아요.')
    return device_store.load(device, date)


# Separate opt-in purpose gate; this endpoint never uses llm_generate/cascade.
from routers.evidence import create_evidence_router


async def _physio_gemini_generate(*args, **kwargs):
    return await gemini_generate(*args, **kwargs)


app.include_router(create_evidence_router(
    authenticate=verify_token,
    generate=_physio_gemini_generate,
    provider_configured=lambda: bool(GEMINI_API_KEY),
    limiter=limiter,
))
