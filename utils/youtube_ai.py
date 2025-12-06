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
import json

import requests

from .config import (
    YOUTUBE_API_KEY,
    check_youtube_key,
    get_openai_client,
    OPENAI_MODEL_SCHEDULE,
)

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


# ─────────────────────────────────────────────
# 0. GPT 기반 검색 쿼리 생성
# ─────────────────────────────────────────────

def _generate_youtube_queries_with_gpt(
    base_query: str,
    domain: str,
    max_queries: int = 4,
) -> List[str]:
    """
    GPT를 이용해서 발달장애인용 유튜브 영상에 적합한
    한국어 검색 쿼리 여러 개를 생성한다.

    - base_query: 기본이 되는 검색어 (예: "카레 요리 발달장애 쉬운 설명 따라하기 단계별")
    - domain: "cooking" / "exercise" / "clothing" 등 용도 구분용 태그
    """
    base_query = (base_query or "").strip()
    if not base_query:
        return []

    client = get_openai_client()

    # 도메인에 따라 설명만 살짝 바꿔준다.
    if domain == "cooking":
        domain_desc = "요리"
    elif domain == "exercise":
        domain_desc = "운동"
    elif domain == "clothing":
        domain_desc = "옷 입기 연습"
    else:
        domain_desc = "학습"

    prompt = f"""
너는 유튜브 검색 쿼리를 만들어 주는 도우미야.

목표:
- 발달장애인 또는 인지적 지원이 필요한 사용자가 보기 좋은 '{domain_desc}' 관련 영상을 찾기 위한
  한국어 유튜브 검색어를 여러 개 만들어라.

조건:
- 기본 의미는 다음 검색어와 비슷해야 한다: "{base_query}"
- 다음과 같은 키워드를 적절히 섞어서, 발달장애인에게 친화적인 영상을 찾도록 돕는다.
  - 발달장애, 지적장애, 쉬운 설명, 천천히, 단계별, 따라하기, 자막, 그림, 시각적 안내
- 각 검색어는 25자 이내의 자연스러운 한국어 검색 문장 또는 단어 조합으로 만든다.
- 광고, 먹방, ASMR, 쇼츠 위주의 검색은 피하도록 만든다.
- 결과는 JSON 형식만 반환한다.

반드시 다음 형식으로만 출력해라:
{{
  "queries": [
    "검색어1",
    "검색어2",
    "검색어3"
  ]
}}
"""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL_SCHEDULE,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=256,
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        queries = data.get("queries", [])
        cleaned: List[str] = []
        for q in queries:
            qs = str(q).strip()
            if qs:
                cleaned.append(qs)

        # 아무것도 안 나오면 base_query만 사용
        if not cleaned:
            return [base_query]

        # base_query가 없으면 맨 앞에 추가
        if base_query not in cleaned:
            cleaned.insert(0, base_query)

        return cleaned[:max_queries]
    except Exception as e:
        print(f"[YOUTUBE_GPT_QUERY] error={e}, fallback to base_query")
        return [base_query]


# ─────────────────────────────────────────────
# 1. YouTube API 검색 (기본)
# ─────────────────────────────────────────────

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


def _search_youtube_via_api_multi(queries: List[str], max_results: int, domain: str) -> List[Dict]:
    """
    여러 검색어로 유튜브를 검색해서 결과를 합친다.
    - 중복 video_id는 제거
    - max_results는 "최종 반환 개수"가 아니라, 각 쿼리 당 요청 개수의 상한으로 사용한다.
    """
    if not queries:
        return []

    all_results: List[Dict] = []
    seen_ids = set()

    # 각 쿼리마다 max_results 개씩만 가져온다.
    for q in queries:
        partial = _search_youtube_via_api(q, max_results=max_results)
        for v in partial:
            vid = v.get("video_id")
            if not vid:
                continue
            if vid in seen_ids:
                continue
            seen_ids.add(vid)
            all_results.append(v)

    print(f"[YOUTUBE_MULTI] domain={domain}, total_unique={len(all_results)}")
    return all_results


# ─────────────────────────────────────────────
# 2. 발달장애 친화도 기반 점수화 / 정렬
# ─────────────────────────────────────────────

def _score_video_for_dd(video: Dict, domain: str) -> int:
    """
    제목/설명 텍스트를 기준으로 발달장애인에게 얼마나 친화적인지
    간단한 규칙 기반으로 점수를 부여한다.
    """
    title = (video.get("title") or "").strip()
    desc = (video.get("description") or "").strip()
    text = f"{title} {desc}"

    score = 0

    # 공통 긍정 키워드
    positive_keywords = [
        "발달장애",
        "지적장애",
        "장애인",
        "쉬운",
        "천천히",
        "슬로우",
        "단계별",
        "따라하기",
        "step",
        "자막",
        "sub",
        "시각",
        "그림",
        "픽토그램",
    ]
    for kw in positive_keywords:
        if kw.lower() in text.lower():
            score += 2

    # 도메인별 긍정 키워드
    if domain == "cooking":
        domain_positive = ["요리", "레시피", "간단", "초보", "기초", "손질"]
    elif domain == "exercise":
        domain_positive = ["운동", "스트레칭", "체조", "근력", "기초", "홈트"]
    elif domain == "clothing":
        domain_positive = ["옷 입기", "티셔츠", "바지", "양말", "지퍼", "단추", "생활 기술"]
    else:
        domain_positive = []

    for kw in domain_positive:
        if kw.lower() in text.lower():
            score += 1

    # 부정 키워드 (먹방, 광고, 쇼츠, ASMR 등은 낮게)
    negative_keywords = [
        "먹방",
        "mukbang",
        "리뷰",
        "광고",
        "협찬",
        "쇼츠",
        "shorts",
        "쇼트",
        "asmr",
        "브이로그",
        "vlog",
    ]
    for kw in negative_keywords:
        if kw.lower() in text.lower():
            score -= 3

    # 아주 짧은 제목, 설명이 거의 없는 것도 약간 감점
    if len(title) < 5:
        score -= 1
    if len(desc) < 10:
        score -= 1

    return score


def _rerank_for_dd(videos: List[Dict], domain: str) -> List[Dict]:
    """
    규칙 기반 점수를 이용해서 발달장애 친화도가 높은 순으로 정렬한다.
    """
    if not videos:
        return []

    scored = []
    for v in videos:
        s = _score_video_for_dd(v, domain=domain)
        vv = dict(v)
        vv["_dd_score"] = s
        scored.append(vv)

    # 점수 내림차순, 점수가 같으면 원래 순서 유지
    scored_sorted = sorted(scored, key=lambda x: x.get("_dd_score", 0), reverse=True)
    return scored_sorted


# ─────────────────────────────────────────────
# 3. 발달장애인용 특화 검색 래퍼들
# ─────────────────────────────────────────────

def search_cooking_videos_for_dd(menu_name: str, max_results: int = 6) -> List[Dict]:
    """
    발달장애인용 요리 영상 검색.
    예: "카레 요리 발달장애 쉬운 설명 따라하기 단계별"
    + GPT로 여러 검색어를 생성한 후, 결과를 합쳐서 정렬.
    """
    base = (menu_name or "").strip()
    if not base:
        return []

    base_query = f"{base} 요리 발달장애 쉬운 설명 따라하기 단계별"
    gpt_queries = _generate_youtube_queries_with_gpt(base_query, domain="cooking")
    raw_results = _search_youtube_via_api_multi(gpt_queries, max_results=max_results, domain="cooking")
    ranked = _rerank_for_dd(raw_results, domain="cooking")
    return ranked[:max_results]


def search_exercise_videos_for_dd(task_or_mode: str, max_results: int = 6) -> List[Dict]:
    """
    발달장애인용 운동 영상 검색.
    예: "발달장애 앉아서 하는 운동 쉬운 동작 따라하기 천천히"
    + GPT로 여러 검색어를 생성한 후, 결과를 합쳐서 정렬.
    """
    base = (task_or_mode or "").strip()
    if not base:
        base = "앉아서 하는"

    base_query = f"발달장애 {base} 운동 쉬운 동작 따라하기 천천히"
    gpt_queries = _generate_youtube_queries_with_gpt(base_query, domain="exercise")
    raw_results = _search_youtube_via_api_multi(gpt_queries, max_results=max_results, domain="exercise")
    ranked = _rerank_for_dd(raw_results, domain="exercise")
    return ranked[:max_results]


def search_clothing_videos_for_dd(task: str, max_results: int = 6) -> List[Dict]:
    """
    발달장애인용 옷 입기 연습 영상 검색.
    예: "발달장애 옷 입기 티셔츠 바지 따라하기"
    + GPT로 여러 검색어를 생성한 후, 결과를 합쳐서 정렬.
    """
    base = (task or "").strip()
    if not base:
        base = "티셔츠"

    base_query = f"발달장애 옷 입기 {base} 실습 영상 따라하기"
    gpt_queries = _generate_youtube_queries_with_gpt(base_query, domain="clothing")
    raw_results = _search_youtube_via_api_multi(gpt_queries, max_results=max_results, domain="clothing")
    ranked = _rerank_for_dd(raw_results, domain="clothing")
    return ranked[:max_results]
