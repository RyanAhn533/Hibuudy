# utils/config.py
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ============================================================
# 1) OpenAI 설정
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_SCHEDULE = os.getenv("OPENAI_MODEL_SCHEDULE", "gpt-4.1-mini")
OPENAI_MODEL_VISION = os.getenv("OPENAI_MODEL_VISION", "gpt-4.1")

_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인하세요.")
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


# ============================================================
# 2) Google Custom Search (이미지 + 유튜브 검색 통합)
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")


def check_google_keys() -> None:
    """
    Google Custom Search API 키 체크
    이미지 검색 + 유튜브 검색 둘 다 이 키 하나로 처리한다.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise RuntimeError(
            "GOOGLE_API_KEY / GOOGLE_CSE_ID 가 설정되어 있지 않습니다. .env 파일을 확인하세요."
        )


# ============================================================
# 3) YouTube Data API v3 (YouTube 검색용)
# ============================================================

# .env에 YOUTUBE_API_KEY가 따로 없으면 GOOGLE_API_KEY를 그대로 재사용
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") or GOOGLE_API_KEY

def check_youtube_key():
    if not YOUTUBE_API_KEY:
        raise RuntimeError(
            "[config] YOUTUBE_API_KEY / GOOGLE_API_KEY 가 비어 있습니다. "
            "Google Cloud Console에서 YouTube Data API v3 를 Enable 하고, "
            "해당 프로젝트의 API 키를 .env의 GOOGLE_API_KEY 또는 YOUTUBE_API_KEY로 설정하세요."
        )
