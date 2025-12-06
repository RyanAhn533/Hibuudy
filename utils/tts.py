# utils/tts.py
# -*- coding: utf-8 -*-
"""
OpenAI TTS(gpt-4o-mini-tts)를 이용해 텍스트를 mp3 바이트로 변환하는 유틸.
"""

import os
from pathlib import Path
from typing import Optional

from .config import get_openai_client

# .env에서 재정의 가능 (없으면 기본값 사용)
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")

TMP_DIR = Path("tmp_audio")
TMP_DIR.mkdir(exist_ok=True)


def synthesize_tts(text: str) -> Optional[bytes]:
    """
    text를 음성으로 변환해서 mp3 바이트를 반환.
    실패 시 None.
    """
    text = (text or "").strip()
    if not text:
        return None

    client = get_openai_client()

    # OpenAI Audio API - TTS
    resp = client.audio.speech.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=text,
    )

    tmp_path = TMP_DIR / "hibuddy_tts.mp3"
    resp.stream_to_file(tmp_path)

    with open(tmp_path, "rb") as f:
        audio_bytes = f.read()

    return audio_bytes
