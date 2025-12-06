# utils/weather_ai.py
# -*- coding: utf-8 -*-
"""
Google Custom Search + GPT 를 이용해서
'서울 오늘 날씨' 같은 검색 결과를 읽고,
발달장애인이 이해하기 쉬운 날씨 요약 + 옷차림 가이드를 만드는 유틸.
"""

import json
from typing import Dict, List

import requests

from .config import (
    check_google_keys,
    GOOGLE_API_KEY,
    GOOGLE_CSE_ID,
    get_openai_client,
    OPENAI_MODEL_VISION,  # 텍스트 모델이 따로 있으면 그걸 써도 됨
)


def search_weather_raw(location_ko: str) -> str:
    """
    Google Custom Search 로 '<지역> 오늘 날씨' 검색해서
    검색 결과 snippet 들을 하나의 텍스트로 합쳐서 반환.
    """
    check_google_keys()

    location_ko = (location_ko or "").strip()
    if not location_ko:
        return ""

    query = f"{location_ko} 오늘 날씨"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": 5,          # 상위 5개 정도만
        "safe": "active",
        # searchType=image 를 쓰지 않고, 일반 웹 검색으로 텍스트 snippet을 받는다.
    }

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", []) or []
    snippets: List[str] = []
    for item in items:
        snippet = item.get("snippet")
        if snippet:
            snippets.append(snippet)

    return "\n".join(snippets)


def analyze_weather_and_suggest_clothes(location_ko: str) -> Dict:
    """
    - Google 검색으로 오늘 날씨 관련 텍스트(snippet)를 가져오고
    - GPT에게 '날씨 요약 + 옷차림 추천 + guide_script 문장 리스트'를 JSON으로 만들어 달라고 요청.

    반환 예:
    {
      "location": "서울",
      "weather_summary": "오늘 서울은 맑고, 낮에는 25도 정도입니다.",
      "clothes": ["반팔 티셔츠", "얇은 긴팔 겉옷"],
      "guide_script": [
        "오늘은 날씨가 따뜻해요.",
        "반팔 티셔츠를 입고, 필요하면 얇은 겉옷을 준비해요."
      ]
    }
    """
    client = get_openai_client()
    raw_weather_text = search_weather_raw(location_ko)

    # 검색 결과가 아무것도 없을 때
    if not raw_weather_text.strip():
        return {
            "location": location_ko,
            "weather_summary": "오늘 날씨 정보를 찾지 못했습니다.",
            "clothes": [],
            "guide_script": [
                "날씨 정보를 불러오지 못했어요.",
                "코디네이터가 오늘 입을 옷을 직접 안내해 주세요.",
            ],
        }

    prompt = f"""
너는 발달장애인이 이해하기 쉬운 한국어로 옷차림을 추천하는 도우미야.

아래는 "{location_ko}" 지역의 오늘 날씨에 대한 검색 결과 snippet 모음이야.
이 내용을 토대로, 오늘 하루 외출/등원/산책을 할 때 어떤 옷을 입으면 좋을지 알려줘.

검색 결과 텍스트:
----------------
{raw_weather_text}
----------------

다음 JSON 형식으로만 답해줘. 다른 설명은 쓰지 마.

{{
  "location": "지역 이름 (예: 서울)",
  "weather_summary": "오늘 날씨를 한두 문장으로, 발달장애인이 이해하기 쉬운 말로 정리",
  "clothes": [
    "권장 옷차림 1",
    "권장 옷차림 2"
  ],
  "guide_script": [
    "사용자 화면에서 순서대로 읽어줄 간단한 안내 문장 1",
    "사용자 화면에서 순서대로 읽어줄 간단한 안내 문장 2",
    "필요하면 3~4줄까지"
  ]
}}
"""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL_VISION,  # 텍스트 전용 모델이 있으면 그걸 써도 무방
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=512,
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
    except Exception as e:  # GPT 에러나 JSON 파싱 에러
        print("[weather_ai] GPT error:", e)
        data = {
            "location": location_ko,
            "weather_summary": "날씨 요약 생성 중 오류가 발생했습니다.",
            "clothes": [],
            "guide_script": [
                "날씨 정보를 읽어오다가 오류가 발생했어요.",
                "코디네이터가 오늘 입을 옷을 직접 안내해 주세요.",
            ],
        }

    # 최소 필드 보정
    if not isinstance(data, dict):
        data = {}
    data.setdefault("location", location_ko)
    data.setdefault("weather_summary", "")
    data.setdefault("clothes", [])
    data.setdefault("guide_script", [])

    # 타입 강제
    if not isinstance(data["clothes"], list):
        data["clothes"] = []
    if not isinstance(data["guide_script"], list):
        data["guide_script"] = []

    return data
