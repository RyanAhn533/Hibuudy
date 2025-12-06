# utils/config.py
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

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
# 1) OpenAI 설정
# ============================================================

OPENAI_API_KEY = _get_config("OPENAI_API_KEY")
OPENAI_MODEL_SCHEDULE = _get_config("OPENAI_MODEL_SCHEDULE", "gpt-4.1-mini")
OPENAI_MODEL_VISION = _get_config("OPENAI_MODEL_VISION", "gpt-4.1-vision")

_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. "
                "Streamlit Secrets 또는 .env 파일을 확인하세요."
            )
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


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
