# utils/config.py
import os
from typing import Optional

import requests
from dotenv import load_dotenv

# Streamlit이 없는 환경(로컬 스크립트 실행 등)에서도 돌아가도록 try/except
try:
    import streamlit as st
except ImportError:  # streamlit 없이도 import 가능하게
    st = None

load_dotenv()


# ------------------------------------------------------------
# 공통: 환경값 가져오는 헬퍼
#   1) st.secrets 우선
#   2) 없으면 os.getenv 사용
# ------------------------------------------------------------
def _get_config(key: str, default: str = "") -> str:
    # 1) Streamlit Cloud / Streamlit 앱에서 실행될 때
    if st is not None:
        try:
            if key in st.secrets:
                value = st.secrets[key]
                if value is not None and value != "":
                    return str(value)
        except Exception:
            # secrets 접근 실패하면 그냥 넘어가고 os.getenv로 폴백
            pass

    # 2) 로컬 .env / 환경변수
    return os.getenv(key, default) or default


# ============================================================
# 1) Gemini 설정
# ============================================================

GEMINI_API_KEY = _get_config("GEMINI_API_KEY") or _get_config("GOOGLE_API_KEY")

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)


def gemini_generate(
    system_prompt: str,
    user_text: str,
    response_schema: dict = None,
) -> str:
    """
    Gemini 2.0 Flash REST API를 호출하여 JSON 텍스트를 생성한다.

    CoT/hallucination 방지 전략:
    1. system_instruction 필드로 system prompt 분리 (user content와 혼동 방지)
    2. responseMimeType: "application/json" 강제
    3. response_schema가 있으면 출력 구조를 명시적으로 제약
    4. 응답에서 마크다운/CoT 잔재 제거 후처리

    Args:
        system_prompt: 시스템 프롬프트 (역할/규칙 정의)
        user_text: 사용자 입력
        response_schema: Gemini responseSchema (선택. 출력 JSON 구조를 강제)

    Returns:
        정제된 JSON 문자열.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY (또는 GOOGLE_API_KEY)가 설정되어 있지 않습니다. "
            "Streamlit Secrets 또는 .env 파일을 확인하세요."
        )

    generation_config = {
        "responseMimeType": "application/json",
        "temperature": 0.15,  # hallucination 줄이기 위해 낮춤
    }

    if response_schema:
        generation_config["responseSchema"] = response_schema

    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_text}],
            }
        ],
        "generationConfig": generation_config,
    }

    resp = requests.post(
        GEMINI_ENDPOINT,
        params={"key": GEMINI_API_KEY},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    # Gemini 응답 구조: {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini API가 빈 응답을 반환했습니다.")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError("Gemini API 응답에 parts가 없습니다.")

    raw_text = parts[0].get("text", "")

    # ── CoT / 마크다운 잔재 제거 후처리 ──
    return _clean_json_response(raw_text)


def _clean_json_response(text: str) -> str:
    """
    Gemini가 JSON 모드에서도 간혹 섞어 넣는 잔재 제거:
    - ```json ... ``` 마크다운 블록
    - 앞뒤 설명 텍스트 (JSON 전후)
    - BOM, 공백 정리
    """
    import re

    text = text.strip()

    # 1) ```json ... ``` 또는 ``` ... ``` 블록 추출
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if md_match:
        text = md_match.group(1).strip()

    # 2) 첫 번째 { 또는 [ 앞의 텍스트 제거 (CoT 설명)
    first_brace = -1
    for i, ch in enumerate(text):
        if ch in ('{', '['):
            first_brace = i
            break
    if first_brace > 0:
        text = text[first_brace:]

    # 3) 마지막 } 또는 ] 뒤의 텍스트 제거
    last_brace = -1
    for i in range(len(text) - 1, -1, -1):
        if text[i] in ('}', ']'):
            last_brace = i
            break
    if last_brace >= 0 and last_brace < len(text) - 1:
        text = text[:last_brace + 1]

    return text


# ============================================================
# 2) Google Custom Search (이미지 + 유튜브 검색 통합)
# ============================================================

GOOGLE_API_KEY = _get_config("GOOGLE_API_KEY")
GOOGLE_CSE_ID = _get_config("GOOGLE_CSE_ID")


def check_google_keys() -> None:
    """
    Google Custom Search API 키 체크
    이미지 검색 + 유튜브 검색 둘 다 이 키 하나로 처리한다.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise RuntimeError(
            "GOOGLE_API_KEY / GOOGLE_CSE_ID 가 설정되어 있지 않습니다. "
            "Streamlit Secrets 또는 .env 파일을 확인하세요."
        )


# ============================================================
# 3) YouTube Data API v3 (YouTube 검색용)
# ============================================================

# secrets에 YOUTUBE_API_KEY가 없으면 GOOGLE_API_KEY를 그대로 재사용
YOUTUBE_API_KEY = _get_config("YOUTUBE_API_KEY") or GOOGLE_API_KEY


def check_youtube_key():
    if not YOUTUBE_API_KEY:
        raise RuntimeError(
            "[config] YOUTUBE_API_KEY / GOOGLE_API_KEY 가 비어 있습니다. "
            "Google Cloud Console에서 YouTube Data API v3 를 Enable 하고, "
            "해당 프로젝트의 API 키를 Streamlit Secrets 또는 .env에 설정하세요."
        )
