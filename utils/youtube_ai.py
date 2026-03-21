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
import re

import requests

from .config import (
    YOUTUBE_API_KEY,
    check_youtube_key,
    gemini_generate,
)
from .response_evaluator import evaluate_youtube_queries

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


# ─────────────────────────────────────────────
# 0. 메뉴 이름 정제 (코디네이터에서 온 긴 제목 → 핵심 키워드)
# ─────────────────────────────────────────────

def _normalize_menu_name(raw: str) -> str:
    """
    코디네이터에서 넘어오는 요리 제목이 다음처럼 복잡할 수 있음:
    - "아침: 카레라이스 (단백질 강화)"
    - "🍛 카레 / 샐러드 세트"
    - "저염 카레라이스 1인분"

    유튜브 검색용으로는 핵심 음식 이름만 남기는 게 좋으므로:
    1) 이모지/특수문자 제거
    2) ":", "/", "|" 기준으로 나눠서 첫 덩어리만 사용
    3) 괄호 안 설명 제거
    4) 양/단위(1인분, 200g 등) 같은 숫자/단위는 웬만하면 제거
    """
    if not raw:
        return ""

    text = raw.strip()

    # 1) 이모지/특수문자 대략 제거
    text = re.sub(r"[^\w\sㄱ-ㅎ가-힣:/()|]", " ", text)

    # 2) 구분자 기준으로 첫 덩어리만 사용
    for sep in [":", "|", "/", "·"]:
        if sep in text:
            text = text.split(sep)[-1]  # "아침: 카레라이스" → " 카레라이스"

    text = text.strip()

    # 3) 괄호 내용 제거
    text = re.sub(r"\(.*?\)", " ", text).strip()

    # 4) 숫자+단위 제거 (대략)
    text = re.sub(r"\d+\s*(인분|g|그램|개|조각|ml|mL)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text or raw.strip()


# ─────────────────────────────────────────────
# 1. Gemini 기반 검색 쿼리 생성
# ─────────────────────────────────────────────

def _generate_youtube_queries_with_gpt(
    base_query: str,
    domain: str,
    max_queries: int = 4,
) -> List[str]:
    """
    Gemini를 이용해서 발달장애인용 유튜브 영상에 적합한
    한국어 검색 쿼리 여러 개를 생성한다.

    - base_query: 기본이 되는 검색어
    - domain: "cooking" / "exercise" / "clothing" 등 용도 구분용 태그
    """
    base_query = (base_query or "").strip()
    if not base_query:
        return []

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
        raw = gemini_generate(prompt, base_query)
        data = json.loads(raw)
        queries = data.get("queries", [])
        cleaned: List[str] = []
        for q in queries:
            qs = str(q).strip()
            if qs:
                cleaned.append(qs)

        if not cleaned:
            return [base_query]

        if base_query not in cleaned:
            cleaned.insert(0, base_query)

        cleaned = cleaned[:max_queries]

        # 쿼리 품질 평가 — 부적절 키워드 포함 시 필터링
        score, issues = evaluate_youtube_queries(cleaned)
        if issues:
            print(f"[YOUTUBE_QUERY_EVAL] score={score}, issues={issues}")
            # 부적절 키워드 포함 쿼리 제거
            bad_kws = {"먹방", "asmr", "shorts", "쇼츠", "광고", "리뷰"}
            cleaned = [
                q for q in cleaned
                if not any(kw in q.lower() for kw in bad_kws)
            ] or [base_query]

        return cleaned
    except Exception as e:
        print(f"[YOUTUBE_GEMINI_QUERY] error={e}, fallback to base_query={base_query}")
        return [base_query]


# ─────────────────────────────────────────────
# 2. YouTube API 검색 (기본)
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


def _search_youtube_via_api_multi(queries: List[str], per_query_max: int, domain: str) -> List[Dict]:
    """
    여러 검색어로 유튜브를 검색해서 결과를 합친다.
    - 중복 video_id는 제거
    - per_query_max: 쿼리 하나당 YouTube에서 가져올 개수 상한
    """
    if not queries:
        return []

    all_results: List[Dict] = []
    seen_ids = set()

    for q in queries:
        partial = _search_youtube_via_api(q, max_results=per_query_max)
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
# 3. 발달장애 친화도 기반 점수화 / 정렬
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

    if len(title) < 5:
        score -= 1
    if len(desc) < 10:
        score -= 1

    return score


def _rerank_for_dd(videos: List[Dict], domain: str) -> List[Dict]:
    if not videos:
        return []

    scored = []
    for v in videos:
        s = _score_video_for_dd(v, domain=domain)
        vv = dict(v)
        vv["_dd_score"] = s
        scored.append(vv)

    scored_sorted = sorted(scored, key=lambda x: x.get("_dd_score", 0), reverse=True)
    return scored_sorted


# ─────────────────────────────────────────────
# 4. 발달장애인용 특화 검색 래퍼들
# ─────────────────────────────────────────────

def _has_dd_keywords(q: str) -> bool:
    """
    코디네이터가 이미 발달장애 친화 쿼리로 손 본 경우인지 체크
    그럴 때는 GPT 확장을 하지 않고, 그대로 검색에 쓴다.
    """
    q = (q or "").strip()
    if not q:
        return False

    dd_keywords = ["발달장애", "지적장애", "쉬운", "천천히", "자막", "픽토그램", "따라하기"]
    return any(kw in q for kw in dd_keywords)


def search_cooking_videos_for_dd(menu_name_or_query: str, max_results: int = 4) -> List[Dict]:
    """
    발달장애인용 요리 영상 검색.

    - 코디네이터가 직접 입력한 유튜브 검색어가 들어오는 경우:
      → 그 검색어 그대로로만 검색하고, GPT 확장 없이 단일 쿼리만 사용
    - 단순 메뉴 이름만 들어오는 경우:
      → 메뉴 이름을 정제(normalize)하고, GPT로 여러 검색어를 생성해서 검색
    """
    raw = (menu_name_or_query or "").strip()
    if not raw:
        return []

    print(f"[YOUTUBE_COOKING] input='{raw}'")

    if _has_dd_keywords(raw):
        queries = [raw]
        print(f"[YOUTUBE_COOKING] use_raw_query_only={queries}")
    else:
        menu_core = _normalize_menu_name(raw)
        base_query = f"{menu_core} 요리 발달장애 쉬운 설명 따라하기 단계별"
        gpt_queries = _generate_youtube_queries_with_gpt(base_query, domain="cooking")
        print(f"[YOUTUBE_COOKING] normalized_menu='{menu_core}', base_query='{base_query}', gpt_queries={gpt_queries}")
        queries = gpt_queries

    raw_results = _search_youtube_via_api_multi(queries, per_query_max=4, domain="cooking")
    ranked = _rerank_for_dd(raw_results, domain="cooking")
    return ranked[:max_results]


def search_exercise_videos_for_dd(task_or_query: str, max_results: int = 4) -> List[Dict]:
    """
    발달장애인용 운동 영상 검색.

    - 코디네이터가 직접 만든 검색어가 들어오면 그대로 사용
    - 그렇지 않으면 task 문장을 바탕으로 템플릿 + GPT 확장 사용

    변경: 입력이 비면 기본 추천("앉아서 하는 쉬운 운동")을 넣지 않고 빈 리스트 반환
    """
    base = (task_or_query or "").strip()
    print(f"[YOUTUBE_EXERCISE] input='{base}'")

    if not base:
        return []

    if _has_dd_keywords(base):
        queries = [base]
        print(f"[YOUTUBE_EXERCISE] use_raw_query_only={queries}")
    else:
        base_query = f"발달장애 {base} 운동 쉬운 동작 따라하기 천천히"
        gpt_queries = _generate_youtube_queries_with_gpt(base_query, domain="exercise")
        print(f"[YOUTUBE_EXERCISE] base_query='{base_query}', gpt_queries={gpt_queries}")
        queries = gpt_queries

    raw_results = _search_youtube_via_api_multi(queries, per_query_max=4, domain="exercise")
    ranked = _rerank_for_dd(raw_results, domain="exercise")
    return ranked[:max_results]


def search_clothing_videos_for_dd(task_or_query: str, max_results: int = 4) -> List[Dict]:
    """
    발달장애인용 옷 입기 영상 검색.

    - 코디네이터가 직접 만든 검색어가 들어오면 그대로 사용
    - 그렇지 않으면 task 문장을 바탕으로 템플릿 + GPT 확장 사용

    변경: 입력이 비면 기본 추천("티셔츠 입기 연습")을 넣지 않고 빈 리스트 반환
    """
    base = (task_or_query or "").strip()
    print(f"[YOUTUBE_CLOTHING] input='{base}'")

    if not base:
        return []

    if _has_dd_keywords(base):
        queries = [base]
        print(f"[YOUTUBE_CLOTHING] use_raw_query_only={queries}")
    else:
        base_query = f"발달장애 옷 입기 {base} 실습 영상 따라하기"
        gpt_queries = _generate_youtube_queries_with_gpt(base_query, domain="clothing")
        print(f"[YOUTUBE_CLOTHING] base_query='{base_query}', gpt_queries={gpt_queries}")
        queries = gpt_queries

    raw_results = _search_youtube_via_api_multi(queries, per_query_max=4, domain="clothing")
    ranked = _rerank_for_dd(raw_results, domain="clothing")
    return ranked[:max_results]


# ─────────────────────────────────────────────
# 5. 코디네이터 "직접 검색어"용 RAW 검색 래퍼
#    (GPT 확장 없이, 입력한 검색어 그대로 사용)
# ─────────────────────────────────────────────

def _search_videos_for_dd_raw(query: str, max_results: int, domain: str) -> List[Dict]:
    """
    코디네이터가 직접 입력한 유튜브 검색어를
    그대로 YouTube API에 넘기고, DD 친화도 점수로만 재정렬하는 버전.

    변경: query가 비면 "기본 프롬프트"를 넣지 않고 빈 리스트 반환
    """
    q = (query or "").strip()
    if not q:
        return []

    print(f"[YOUTUBE_RAW] domain={domain}, query='{q}'")
    raw = _search_youtube_via_api(q, max_results=max_results)
    ranked = _rerank_for_dd(raw, domain=domain)
    return ranked[:max_results]


def search_cooking_videos_for_dd_raw(query: str, max_results: int = 4) -> List[Dict]:
    """
    GPT 확장 없이, 코디네이터가 입력한 검색어 그대로 쓰는 요리 영상 검색.
    """
    return _search_videos_for_dd_raw(query, max_results=max_results, domain="cooking")


def search_exercise_videos_for_dd_raw(query: str, max_results: int = 4) -> List[Dict]:
    """
    GPT 확장 없이, 코디네이터가 입력한 검색어 그대로 쓰는 운동 영상 검색.
    """
    return _search_videos_for_dd_raw(query, max_results=max_results, domain="exercise")


def search_clothing_videos_for_dd_raw(query: str, max_results: int = 4) -> List[Dict]:
    """
    GPT 확장 없이, 코디네이터가 입력한 검색어 그대로 쓰는 옷 입기 영상 검색.
    """
    return _search_videos_for_dd_raw(query, max_results=max_results, domain="clothing")
