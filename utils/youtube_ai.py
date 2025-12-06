# utils/youtube_ai.py
# -*- coding: utf-8 -*-
"""
YouTube Data API v3를 이용해서
발달장애인용 요리 / 운동 / 옷입기 유튜브 영상을 검색하는 유틸.

전제:
- Google Cloud Console에서 YouTube Data API v3를 Enable 해둔다.
- utils/config.py 에서 YOUTUBE_API_KEY 를 제공하고, check_youtube_key() 로 키 유효성을 검사한다.

반환 형식:
- 각 검색 함수는 List[Dict] 를 반환하며, 각 Dict는 다음 키를 가진다.
  {
      "title": 제목(str),
      "description": 설명(str),
      "video_id": 영상 ID(str),
      "url": 전체 URL(str, https://www.youtube.com/watch?v=...),
      "thumbnail": 썸네일 URL(str, 보통 medium 혹은 default)
  }
"""

from typing import Dict, List

import requests

from .config import YOUTUBE_API_KEY, check_youtube_key

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def _search_youtube_via_api(query: str, max_results: int = 6) -> List[Dict]:
    """
    YouTube Data API v3 의 search.list 엔드포인트를 이용한 유튜브 영상 검색.
    - part=snippet
    - type=video
    - safeSearch=strict
    """
    q = (query or "").strip()
    if not q:
        return []

    check_youtube_key()

    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "type": "video",
        "maxResults": max(1, min(max_results, 10)),
        "q": q,
        "safeSearch": "strict",
    }

    print(f"[YOUTUBE_API] query={q}, max_results={max_results}")
    resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])
    results: List[Dict] = []

    for item in items:
        id_info = item.get("id", {}) or {}
        video_id = id_info.get("videoId", "")
        snippet = item.get("snippet", {}) or {}

        title = snippet.get("title", "")
        description = snippet.get("description", "")

        thumbnails = snippet.get("thumbnails", {}) or {}
        thumb_url = ""
        # medium 우선 사용, 없으면 default
        if "medium" in thumbnails:
            thumb_url = thumbnails["medium"].get("url", "") or ""
        elif "default" in thumbnails:
            thumb_url = thumbnails["default"].get("url", "") or ""

        url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""

        results.append(
            {
                "title": title,
                "description": description,
                "video_id": video_id,
                "url": url,
                "thumbnail": thumb_url,
            }
        )

    print(f"[YOUTUBE_API] found={len(results)}")
    return results


# ─────────────────────────────────────────────
# 발달장애인용 특화 쿼리 래퍼들
# ─────────────────────────────────────────────

def search_cooking_videos_for_dd(menu_name: str, max_results: int = 6) -> List[Dict]:
    """
    발달장애인용 요리 영상 검색.
    예: "카레 요리 발달장애 쉬운 설명 따라하기 단계별"
    """
    base = (menu_name or "").strip()
    if not base:
        return []

    query = f"{base} 요리 발달장애 쉬운 설명 따라하기 단계별"
    return _search_youtube_via_api(query, max_results=max_results)


def search_exercise_videos_for_dd(task_or_mode: str, max_results: int = 6) -> List[Dict]:
    """
    발달장애인용 운동 영상 검색.
    예: "발달장애 앉아서 하는 운동 쉬운 동작 따라하기 천천히"
    """
    base = (task_or_mode or "").strip()
    if not base:
        base = "운동"

    query = f"발달장애 {base} 운동 쉬운 동작 따라하기 천천히"
    return _search_youtube_via_api(query, max_results=max_results)


def search_clothing_videos_for_dd(task: str, max_results: int = 6) -> List[Dict]:
    """
    발달장애인용 옷 입기 연습 영상 검색.
    예: "발달장애 옷 입기 티셔츠 바지 따라하기"
    """
    base = (task or "").strip()
    query = f"발달장애 옷 입기 {base} 실습 영상 따라하기"
    return _search_youtube_via_api(query, max_results=max_results)
