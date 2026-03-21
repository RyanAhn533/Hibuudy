# utils/image_ai.py
# -*- coding: utf-8 -*-
"""
Google Custom Search를 이용해서
음식 이미지를 검색하고,
선택된 이미지는 assets/images/ 폴더에 저장하는 유틸.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Dict, List

import requests
from PIL import Image, UnidentifiedImageError
import io

from .config import (
    check_google_keys,
    GOOGLE_API_KEY,
    GOOGLE_CSE_ID,
)

# 이미지 저장 폴더
ASSETS_DIR = Path("assets/images")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# 공통 헤더 (일부 서버는 User-Agent 없으면 막기도 해서 추가)
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ImageFetcher/1.0; +https://example.com)"
}


# ─────────────────────────────────────────────
# 0. 이미지 URL 유효성 체크
# ─────────────────────────────────────────────

def _is_usable_image_url(url: str, timeout: int = 5) -> bool:
    """
    실제로 요청이 성공하고, Content-Type이 image/* 인 경우만 True 반환.
    - HEAD로 먼저 체크하고, Content-Type이 불명확하면 stream GET으로 한 번 더 확인.
    - 예외 및 에러 응답 코드는 False 처리.
    """
    if not url:
        return False
    if not url.startswith("http"):
        return False

    try:
        # 1) HEAD 요청으로 상태/헤더만 먼저 확인
        resp = requests.head(url, allow_redirects=True, timeout=timeout, headers=DEFAULT_HEADERS)
        if resp.status_code >= 400:
            return False

        content_type = (resp.headers.get("Content-Type") or "").lower()

        # 일부 서버는 HEAD에서 Content-Type을 제대로 안 줄 수도 있음
        if not content_type.startswith("image/"):
            # 2) stream GET으로 한 번 더 확인 (내용은 다 받지 않고 헤더만 확인)
            resp_get = requests.get(url, stream=True, timeout=timeout, headers=DEFAULT_HEADERS)
            if resp_get.status_code >= 400:
                return False
            content_type = (resp_get.headers.get("Content-Type") or "").lower()
            if not content_type.startswith("image/"):
                return False

        return True

    except Exception:
        # 어떤 에러든 나면 쓸 수 없는 URL로 간주
        return False


# ─────────────────────────────────────────────
# 1. 기본 이미지 검색 (Google Custom Search)
# ─────────────────────────────────────────────

def search_food_images_raw(query: str, max_results: int = 8) -> List[Dict]:
    """
    Google Custom Search JSON API로 이미지 검색.
    - query: 검색어
    - max_results: 최대 몇 개까지 받을지 (1~10)
    - 여기서부터 '실제로 요청 가능한 이미지'만 필터링해서 반환.
    """
    check_google_keys()

    query = (query or "").strip()
    if not query:
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    num = max(1, min(max_results, 10))

    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "searchType": "image",   # 이미지 전용 검색
        "num": num,
        "safe": "active",        # 안전검색
        "imgType": "photo",      # 사진 위주
    }

    resp = requests.get(url, params=params, timeout=10, headers=DEFAULT_HEADERS)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])
    results: List[Dict] = []

    for item in items:
        link = item.get("link")  # 원본 이미지 URL
        if not link:
            continue

        # 여기서 먼저 '실제로 다운로드 가능한 이미지 URL인지' 체크
        if not _is_usable_image_url(link):
            continue

        title = item.get("title") or ""
        img_info = item.get("image") or {}
        thumb = img_info.get("thumbnailLink") or link

        results.append(
            {
                "title": title,
                "link": link,
                "thumbnail": thumb,
            }
        )

    return results


# ─────────────────────────────────────────────
# 2. 이미지 검색 + 필터링 (GPT Vision 제거, Google 결과 그대로 사용)
# ─────────────────────────────────────────────

def search_and_filter_food_images(menu_name: str, max_results: int = 6) -> List[Dict]:
    """
    1) Google Image 검색으로 후보 이미지 가져오고
    2) 상위 max_results 개만 반환 (Google 관련성 순서 그대로 사용)
    """
    base = (menu_name or "").strip()
    if not base:
        return []

    # CSE 웹에서 직접 치던 것과 최대한 비슷하게: 메뉴 이름 + 음식 정도만
    # 예) "라면 음식", "카레 음식"
    query = f"{base} 음식"

    raw_images = search_food_images_raw(query, max_results=max_results)
    return raw_images[:max_results]


# ─────────────────────────────────────────────
# 3. 선택된 이미지를 로컬 assets/images/ 에 저장
# ─────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_ㄱ-힣]", "", text)
    if not text:
        text = "menu"
    return text


def download_image_to_assets(url: str, menu_name: str) -> str:
    """
    선택된 이미지 URL을 다운로드해서 assets/images/ 아래에 저장하고,
    저장된 로컬 경로(문자열)를 반환.
    실패 시 예외 발생.

    여기서 한 번 더:
    - URL이 image/* 인지 확인
    - 실제로 받은 바이트가 PIL로 열리는지 verify()로 검사
    """
    # 혹시라도 이전 단계에서 필터가 안 되었을 수 있으니 한 번 더 체크
    if not _is_usable_image_url(url):
        raise RuntimeError(f"사용할 수 없는 이미지 URL입니다: {url}")

    resp = requests.get(url, timeout=10, headers=DEFAULT_HEADERS)
    resp.raise_for_status()
    content = resp.content

    # 1) PIL로 실제 이미지인지 검증
    try:
        img = Image.open(io.BytesIO(content))
        img.verify()  # 포맷 및 손상 여부 검사
    except (UnidentifiedImageError, OSError) as e:
        raise RuntimeError(f"다운로드한 데이터가 유효한 이미지가 아닙니다: {url} ({e})")

    # 2) 확장자 추정
    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "png" in content_type:
        ext = ".png"
    elif "jpeg" in content_type or "jpg" in content_type:
        ext = ".jpg"
    else:
        # URL에서 한 번 더 추정
        if url.lower().endswith(".png"):
            ext = ".png"
        else:
            ext = ".jpg"

    slug = _slugify(menu_name)
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    filename = f"menu_{slug}_{h}{ext}"

    path = ASSETS_DIR / filename
    with open(path, "wb") as f:
        f.write(content)

    # 스트림릿에서 쓸 수 있도록 문자열 경로 반환
    return str(path)
