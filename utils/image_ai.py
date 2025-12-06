# utils/image_ai.py
# -*- coding: utf-8 -*-
"""
Google Custom Search + GPT Vision을 이용해서
음식 이미지를 검색하고, 자동으로 필터링한 뒤,
선택된 이미지는 assets/images/ 폴더에 저장하는 유틸.
"""

import json
import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List

import requests

from .config import (
    check_google_keys,
    GOOGLE_API_KEY,
    GOOGLE_CSE_ID,
    get_openai_client,
    OPENAI_MODEL_VISION,)

# 이미지 저장 폴더
ASSETS_DIR = Path("assets/images")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# 1. 기본 이미지 검색 (Google Custom Search)
# ─────────────────────────────────────────────

def search_food_images_raw(query: str, max_results: int = 8) -> List[Dict]:
    """
    Google Custom Search JSON API로 이미지 검색.
    - query: 검색어
    - max_results: 최대 몇 개까지 받을지 (1~10)
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
        # 필요하면 안전검색 정도만 유지
        "safe": "active",
        # 사진 위주로만
        "imgType": "photo",
    }

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])
    results: List[Dict] = []

    for item in items:
        link = item.get("link")  # 원본 이미지 URL
        if not link:
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
# 2. GPT Vision으로 이미지 자동 필터링
# ─────────────────────────────────────────────

def filter_images_with_gpt(menu_name: str, images: List[Dict]) -> List[Dict]:
    """
    GPT Vision에게 여러 이미지를 한 번에 보내고,
    각 이미지가 menu_name(예: '라면') 음식 사진으로 적절한지 평가.
    - 0~100 score + '적합'/'부적합' 라벨
    - score와 label을 붙인 뒤, '적합' & score>=60 위주로 정렬해서 반환

    실패 시에는 원본 images를 그대로 반환.
    """
    if not images:
        return []

    client = get_openai_client()

    # 프롬프트
    prompt = f"""
너는 음식 사진을 분류하는 도우미야.

아래에는 '{menu_name}'이라는 메뉴 후보에 대한 여러 이미지가 있어.
각 이미지는 "이미지 0", "이미지 1", ... 순서로 주어진다고 생각해.

각 이미지가 '{menu_name}' 음식 사진으로 얼마나 적절한지 평가해 줘.

반드시 다음 JSON 형식만 출력해:
{{
  "results": [
    {{"index": 0, "score": 0, "label": "부적합"}},
    {{"index": 1, "score": 85, "label": "적합"}}
  ]
}}

- index: 이미지 번호 (0부터 시작)
- score: 0~100 사이 정수 (높을수록 더 잘 맞음)
- label: "적합" 또는 "부적합"
"""

    # content에 텍스트 + 이미지 URL들 넣기
    content: List[Dict] = [{"type": "text", "text": prompt}]
    for idx, img in enumerate(images):
        # 각 이미지 앞에 번호 텍스트도 한 번 더 넣어줌
        content.append({"type": "text", "text": f"이미지 {idx}"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": img["link"]},
            }
        )

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL_VISION,
            messages=[{"role": "user", "content": content}],
            response_format={"type": "json_object"},
            max_tokens=512,
            temperature=0.0,
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
    except Exception:
        # GPT 호출 실패하면 원본 리스트 그대로
        return images

    results = data.get("results", [])
    by_index: Dict[int, Dict] = {}
    for item in results:
        try:
            idx = int(item.get("index", 0))
        except Exception:
            continue
        by_index[idx] = {
            "score": int(item.get("score", 0)),
            "label": str(item.get("label", "부적합")),
        }

    annotated: List[Dict] = []
    for idx, img in enumerate(images):
        meta = by_index.get(idx)
        if not meta:
            continue
        new_img = dict(img)
        new_img["score"] = meta["score"]
        new_img["label"] = meta["label"]
        annotated.append(new_img)

    if not annotated:
        return images

    # 적합 + score>=60 위주로 정렬
    good = [img for img in annotated if img.get("label") == "적합" and img.get("score", 0) >= 60]

    if good:
        good_sorted = sorted(good, key=lambda x: x.get("score", 0), reverse=True)
        return good_sorted
    else:
        # 전부 부적합이면 그냥 점수 높은 순으로
        return sorted(annotated, key=lambda x: x.get("score", 0), reverse=True)


def search_and_filter_food_images(menu_name: str, max_results: int = 6) -> List[Dict]:
    """
    1) Google Image 검색으로 후보 이미지 가져오고
    2) GPT Vision으로 자동 필터링해서
    3) 상위 max_results 개만 반환
    """
    base = (menu_name or "").strip()
    if not base:
        return []

    # CSE 웹에서 직접 치던 것과 최대한 비슷하게: 메뉴 이름 + 음식 정도만
    # 예) "라면 음식", "카레 음식"
    query = f"{base} 음식"

    # 조금 넉넉하게 가져와서 (최대 10개) 그 중에서 필터
    raw_images = search_food_images_raw(query, max_results=10)
    if not raw_images:
        return []

    # GPT 필터는 그대로 두되, 문제 생기면 그냥 원본 사용
    try:
        filtered = filter_images_with_gpt(menu_name, raw_images)
    except Exception:
        filtered = raw_images

    return filtered[:max_results]



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
    """
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    content = resp.content

    # 확장자 추정
    content_type = resp.headers.get("Content-Type", "")
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
