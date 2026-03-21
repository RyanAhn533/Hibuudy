# utils/tts.py
# -*- coding: utf-8 -*-
"""
Edge TTS를 이용해 텍스트를 mp3 바이트로 변환하는 유틸.
"""

import asyncio
import hashlib
from pathlib import Path
from typing import Optional

import edge_tts

TMP_DIR = Path("tmp_audio")
TMP_DIR.mkdir(exist_ok=True)

TTS_VOICE = "ko-KR-SunHiNeural"
TTS_RATE = "-10%"


def synthesize_tts(text: str) -> Optional[bytes]:
    """
    text를 음성으로 변환해서 mp3 바이트를 반환.
    실패 시 None.
    """
    text = (text or "").strip()
    if not text:
        return None

    # 캐시 키: sha256 해시
    cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    cache_path = TMP_DIR / f"tts_{cache_key}.mp3"

    # 캐시에 있으면 바로 반환
    if cache_path.exists():
        with open(cache_path, "rb") as f:
            return f.read()

    # Edge TTS 비동기 호출
    async def _synthesize():
        communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
        await communicate.save(str(cache_path))

    try:
        # 이미 이벤트 루프가 돌고 있는 경우 (Streamlit 등) 대응
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.submit(lambda: asyncio.run(_synthesize())).result()
        else:
            asyncio.run(_synthesize())
    except Exception:
        return None

    if not cache_path.exists():
        return None

    with open(cache_path, "rb") as f:
        audio_bytes = f.read()

    return audio_bytes
