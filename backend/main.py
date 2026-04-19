"""
Hi-Buddy Backend Proxy Server
─────────────────────────────
API 키를 서버에서만 관리하고, Flutter 앱은 이 서버만 호출합니다.

LLM: Gemini 2.0 Flash (무료 티어 가능, 가성비 최고)
TTS: Edge TTS (완전 무료, 한국어 품질 우수)
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import edge_tts
import httpx
from response_evaluator import evaluate_schedule, generate_retry_feedback
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "") or GOOGLE_API_KEY
APP_AUTH_TOKEN = os.getenv("APP_AUTH_TOKEN", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

# Edge TTS 한국어 음성 (여성: ko-KR-SunHiNeural, 남성: ko-KR-InJoonNeural)
EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "ko-KR-SunHiNeural")

# TTS cache directory
TTS_CACHE_DIR = Path("tts_cache")
TTS_CACHE_DIR.mkdir(exist_ok=True)

# ── FastAPI + Rate Limiter ──────────────────────────────────────────

app = FastAPI(title="Hi-Buddy API", docs_url=None, redoc_url=None)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return detailed validation errors instead of generic 'error parsing body'."""
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)[:200] if exc.body else None},
    )


@app.on_event("startup")
async def startup():
    logger.info("Hi-Buddy API started successfully")


# ── Auth Dependency ─────────────────────────────────────────────────


def verify_token(request: Request):
    """Static bearer token 인증. 토큰 미설정 시 인증 건너뜀 (개발/무료 tier 대응)."""
    if not APP_AUTH_TOKEN:
        return  # 토큰 미설정이면 인증 없이 통과
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {APP_AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="인증 실패")


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
    messages = {
        401: f"{service}: 인증 실패",
        403: f"{service}: 접근 거부",
        429: f"{service}: 요청 한도 초과 - 잠시 후 다시 시도하세요.",
    }
    if code in messages:
        raise HTTPException(status_code=code, detail=messages[code])
    if code >= 500:
        raise HTTPException(status_code=502, detail=f"{service}: 외부 서버 오류")
    raise HTTPException(status_code=code, detail=f"{service}: 요청 실패 ({code})")


# ── Gemini API Helper ───────────────────────────────────────────────


async def gemini_generate(
    system_prompt: str,
    user_text: str,
    response_schema: dict = None,
) -> str:
    """Gemini 2.0 Flash API 호출 → 정제된 JSON 텍스트 반환.

    CoT/hallucination 방지:
    1. system_instruction 분리
    2. responseMimeType: "application/json"
    3. response_schema로 출력 구조 강제 (선택)
    4. 후처리로 마크다운/CoT 잔재 제거
    """
    generation_config = {
        "temperature": 0.15,
        "responseMimeType": "application/json",
    }
    if response_schema:
        generation_config["responseSchema"] = response_schema

    client = await get_client()
    resp = await client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_text}]}],
            "generationConfig": generation_config,
        },
    )
    raise_for_upstream(resp, "Gemini")
    data = resp.json()
    try:
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Gemini: 응답 파싱 실패")

    return _clean_json_response(raw_text)


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
    return {"status": "ok"}


# ── 1. Schedule Generation (Gemini 2.0 Flash) ─────────────────────


class ScheduleRequest(BaseModel):
    text: str = Field(..., max_length=2000)


SCHEDULE_SYSTEM_PROMPT = """너는 발달장애인의 하루 일정을 설계하는 코디네이터 도우미다.
사용자가 입력한 텍스트를 읽고 JSON 일정표를 생성한다.
출력 스키마: { "schedule": [ { "time": "HH:MM", "type": "TYPE", "task": "할 일", "guide_script": ["안내문1","안내문2"] } ] }
type은: MORNING_BRIEFING, NIGHT_WRAPUP, GENERAL, ROUTINE, COOKING, MEAL, HEALTH, CLOTHING, LEISURE, REST 중 하나.
guide_script 문장은 20~45자 이내, 존댓말, 1~5문장.
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

    # Gemini 무료 tier (15 RPM) 대응: 1회만 호출, 재생성 없음
    content = await gemini_generate(
        SCHEDULE_SYSTEM_PROMPT, text, response_schema=SCHEDULE_RESPONSE_SCHEMA
    )

    try:
        json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="일정 생성: JSON 파싱 실패")

    return Response(content=content, media_type="application/json")


# ── 2. Schedule Edit (Gemini 2.0 Flash) ───────────────────────────


class EditRequest(BaseModel):
    current_item: dict
    request: str = Field(..., max_length=500)


EDIT_SYSTEM_PROMPT = """너는 일정표를 수정하는 코디네이터 도우미다.
사용자 요청에 따라 time(HH:MM), task, type, guide_script를 수정한다.
반드시 JSON만 출력. 한국어만. 기존 의미를 최대한 유지.
type: MORNING_BRIEFING, NIGHT_WRAPUP, GENERAL, ROUTINE, COOKING, MEAL, HEALTH, CLOTHING, LEISURE, REST"""


@app.post("/api/schedule/edit")
@limiter.limit("10/minute")
async def edit_schedule(request: Request, body: EditRequest, _=Depends(verify_token)):
    edit_text = sanitize(body.request, max_length=500)
    if not edit_text:
        raise HTTPException(status_code=400, detail="수정 요청을 입력해 주세요.")

    user_msg = f"현재 항목 JSON:\n{json.dumps(body.current_item, ensure_ascii=False)}\n\n수정 요청: {edit_text}"

    content = await gemini_generate(EDIT_SYSTEM_PROMPT, user_msg)
    try:
        json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="일정 수정: JSON 파싱 실패")
    return Response(content=content, media_type="application/json")


# ── 3. Claude Agent Proxy (발달장애인 생활 에이전트) ─────────────


class AgentContext(BaseModel):
    """앱에서 전송하는 최소 컨텍스트"""
    profile_name: str = Field(default="사용자", max_length=50)
    disability_level: str = Field(default="mild", max_length=20)
    ingredients: list[str] = Field(default_factory=list, max_length=30)
    today_schedule: list = Field(default_factory=list, max_length=30)
    recent_completions: list[str] = Field(default_factory=list, max_length=20)
    emergency_contacts: list[str] = Field(default_factory=list, max_length=10)


class AgentRequest(BaseModel):
    input: str = Field(..., max_length=500)
    context: AgentContext | None = None


AGENT_SYSTEM_TEMPLATE = """너는 발달장애인 {name}님의 하루 도우미다.
따뜻하게, 짧게, 존댓말로 대답해라.

규칙:
1. 한 문장은 20~45자 이내.
2. 전체 답은 3문장 이내.
3. 어려운 단어 금지. "추가" 대신 "넣기", "삭제" 대신 "지우기".
4. 격려는 담백하게. 이모지 🎉 금지.
5. 요리 추천 시 냉장고 재료 기반으로만.
6. 감정 대화는 공감 먼저, 조언은 묻기 전까지 하지 않는다.

{name}님 정보:
- 장애 정도: {level}
- 냉장고: {ingredients}
- 오늘 일정: {schedule}
- 최근 수행: {completions}
- 긴급 연락처: {contacts}

JSON으로 응답하지 말고, 자연스러운 한국어 문장만 출력해라."""


@app.post("/api/agent")
@limiter.limit("20/minute")
async def agent_chat(request: Request, body: AgentRequest, _=Depends(verify_token)):
    """맥락 기반 대화 에이전트.
    v3.1: Gemini 2.0 Flash 기본 (무료 15 RPM), CLAUDE_API_KEY 있으면 Claude 자동 승급.
    """
    user_input = sanitize(body.input, max_length=500)
    if not user_input:
        raise HTTPException(status_code=400, detail="무엇을 물어볼지 적어주세요.")

    ctx = body.context or AgentContext()
    system_prompt = AGENT_SYSTEM_TEMPLATE.format(
        name=ctx.profile_name,
        level=ctx.disability_level,
        ingredients=", ".join(ctx.ingredients[:15]) or "(정보 없음)",
        schedule="; ".join(str(s) for s in ctx.today_schedule[:10]) or "(오늘 일정 없음)",
        completions=", ".join(ctx.recent_completions[:10]) or "(기록 없음)",
        contacts=", ".join(ctx.emergency_contacts[:5]) or "(등록 안 됨)",
    )

    # ── Claude 우선 (품질↑), 없으면 Gemini 폴백 (비용 0) ──
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
                data = resp.json()
                text = data["content"][0]["text"]
                return {"text": text.strip()}
            # 실패 시 Gemini 폴백
            logger.warning("Claude %s, fallback to Gemini", resp.status_code)
        except Exception as e:
            logger.warning("Claude err %s, fallback to Gemini", e)

    # Gemini 2.0 Flash (무료 15 RPM)
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="도우미 서비스 준비 중이에요.")

    client = await get_client()
    try:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_input}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 400,
                    # NOTE: JSON 강제 X — 자연스러운 한국어 대화
                },
            },
            timeout=20.0,
        )
    except Exception as e:
        logger.warning("Gemini agent failed: %s", e)
        raise HTTPException(status_code=502, detail="도우미가 잠깐 쉬고 있어요.")

    if resp.status_code == 429:
        raise HTTPException(status_code=429, detail="잠시 후 다시 시도해 주세요.")
    if resp.status_code != 200:
        logger.warning("Gemini error %s: %s", resp.status_code, resp.text[:200])
        raise HTTPException(status_code=502, detail="도우미 응답에 문제가 있어요.")

    data = resp.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="도우미 응답 파싱 실패")

    return {"text": text.strip()}


# ── 4. TTS (Edge TTS — 완전 무료) ─────────────────────────────────


class TtsRequest(BaseModel):
    text: str = Field(..., max_length=4096)


@app.post("/api/tts")
@limiter.limit("30/minute")
async def synthesize_tts(request: Request, body: TtsRequest, _=Depends(verify_token)):
    text = sanitize(body.text, max_length=4096)
    if not text:
        raise HTTPException(status_code=400, detail="읽어줄 텍스트가 없습니다.")

    # Check cache
    cache_key = hashlib.sha256(text.encode()).hexdigest()
    cache_path = TTS_CACHE_DIR / f"{cache_key}.mp3"
    if cache_path.exists():
        return Response(content=cache_path.read_bytes(), media_type="audio/mpeg")

    # Edge TTS 합성
    try:
        communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE, rate="-10%")
        await communicate.save(str(cache_path))
    except Exception:
        raise HTTPException(status_code=502, detail="TTS: 음성 합성 실패")

    if not cache_path.exists():
        raise HTTPException(status_code=502, detail="TTS: 파일 생성 실패")

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

SCHEDULE_DB = Path(__file__).parent / "schedules.db"


def _init_db():
    try:
        with sqlite3.connect(str(SCHEDULE_DB)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    data TEXT NOT NULL,
                    updated_at TEXT DEFAULT (datetime('now')),
                    PRIMARY KEY (user_id, date)
                )
            """)
    except Exception as e:
        logger.warning("Failed to initialize schedule DB: %s", e)


_init_db()

@contextmanager
def _get_db():
    conn = sqlite3.connect(str(SCHEDULE_DB))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


class ScheduleSaveRequest(BaseModel):
    user_id: str = Field(..., max_length=100)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    schedule: list


@app.post("/api/schedule/save")
@limiter.limit("20/minute")
async def save_schedule(request: Request, body: ScheduleSaveRequest, _=Depends(verify_token)):
    data_str = json.dumps(body.schedule, ensure_ascii=False)
    with _get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO schedules (user_id, date, data) VALUES (?, ?, ?)",
            (body.user_id, body.date, data_str),
        )
    return {"status": "ok"}


@app.get("/api/schedule/load")
@limiter.limit("30/minute")
async def load_schedule(
    request: Request,
    user_id: str = Query(..., max_length=100),
    date: str = Query(default="", max_length=10),
    _=Depends(verify_token),
):
    with _get_db() as conn:
        if date:
            row = conn.execute(
                "SELECT date, data FROM schedules WHERE user_id = ? AND date = ?",
                (user_id, date),
            ).fetchone()
        else:
            # Get latest
            row = conn.execute(
                "SELECT date, data FROM schedules WHERE user_id = ? ORDER BY date DESC LIMIT 1",
                (user_id,),
            ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="저장된 일정이 없습니다.")
    return {"date": row["date"], "schedule": json.loads(row["data"])}
