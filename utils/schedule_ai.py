# utils/schedule_ai.py
# -*- coding: utf-8 -*-
"""
코디네이터가 적은 자연어 하루 일정을
발달장애인용 스케줄 JSON 구조로 변환하는 모듈.

외부에서 쓰는 함수는 딱 하나:
    generate_schedule_from_text(text: str) -> List[Dict]
"""

import json
from typing import Dict, List

from .config import gemini_generate
from .response_evaluator import evaluate_schedule, generate_retry_feedback


# ─────────────────────────────────────────────
# 1. 시스템 프롬프트
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """
당신은 발달장애인 당사자를 위한 하루 일정 코디네이터입니다.

역할:
- 코디네이터(보호자, 교사 등)가 쓴 자연어 일정을 읽고,
- 당사자가 이해하기 쉬운 '슬롯' 리스트로 변환합니다.
- 각 슬롯은 한 가지 활동만 포함합니다.

!!! 출력 형식 매우 중요 !!!
- 출력은 반드시 하나의 JSON 객체(object)만이어야 합니다.
- 최상위 키는 반드시 "schedule" 이어야 합니다.
- 구조는 다음과 같습니다.

{
  "schedule": [
    {
      "time": "08:00",
      "type": "MORNING_BRIEFING",
      "task": "아침 인사 및 오늘 일정 안내",
      "guide_script": [
        "좋은 아침이에요.",
        "오늘 하루 계획을 함께 살펴볼게요."
      ]
    },
    ...
  ]
}

각 필드 설명:
- time: "HH:MM" 24시간 형식 문자열 (예: "08:00", "13:30")
- type: 아래 값 중 하나 (대문자)
  - "MORNING_BRIEFING" : 아침 인사, 날씨, 오늘 일정 소개
  - "MEAL"             : 밥 먹기(식사), 간식 먹기(식사 행위 중심)
  - "COOKING"          : 요리하기(조리/레시피 수행 중심)
  - "HEALTH"           : 운동, 산책, 스트레칭, 건강 관리
  - "CLOTHING"         : 옷 입기 연습, 옷 갈아입기
  - "LEISURE"          : 쉬기, 놀이, TV 보기, 취미, 여가 시간
  - "ROUTINE"          : 준비/위생(세수, 양치, 샤워, 정리정돈 등)
  - "GENERAL"          : 공부, 외출, 병원, 이동 등 일반 활동
  - "NIGHT_WRAPUP"     : 하루 마무리, 정리, 취침 준비

- task: 코디네이터가 이해하기 쉬운 한 줄 설명
  예: "라면 또는 카레 중 하나 먹기"
- guide_script: 발달장애인이 보기 쉬운 짧은 문장 배열
  - 존댓말 사용 (예: "~해요.")
  - 한 문장도 너무 길지 않게
  - 단계별로 천천히 안내
  - guide_script 는 적어도 1개 이상의 문자열을 포함해야 합니다.

타입 분류 힌트:
- "밥", "식사", "점심", "저녁", "아침 먹기", "간식", "먹기" → MEAL
- "요리", "만들기", "조리", "레시피", "끓이기", "볶기" → COOKING
- "운동", "체조", "스트레칭", "산책", "걷기", "헬스" → HEALTH
- "옷", "갈아입기", "옷 입기" → CLOTHING
- "쉬기", "휴식", "놀이", "TV", "영화", "여가" → LEISURE
- "세수", "양치", "샤워", "정리", "준비" → ROUTINE
- "잠자기", "취침", "하루 마무리" → NIGHT_WRAPUP
- "날씨 안내", "아침 인사", "오늘 일정 소개" → MORNING_BRIEFING
- 그 외 → GENERAL

주의:
- time 은 반드시 "HH:MM" 형식만 사용합니다.
- JSON 외의 설명, 코드블럭, 텍스트를 절대 추가하지 마세요.
"""


# ─────────────────────────────────────────────
# 2. 내부 유틸
# ─────────────────────────────────────────────

def _normalize_item(raw: Dict) -> Dict:
    """GPT가 준 한 슬롯(dict)을 안전하게 정리."""
    time_str = str(raw.get("time", "00:00"))
    type_str = str(raw.get("type", "GENERAL")).upper().strip()
    task = raw.get("task") or ""

    guide = raw.get("guide_script") or []
    if isinstance(guide, str):
        guide = [guide]
    elif isinstance(guide, list):
        guide = [str(g) for g in guide if g]
    else:
        guide = []

    # type 값 정리 (MEAL/LEISURE 등 유지)
    mapping = {
        # morning
        "MORNING": "MORNING_BRIEFING",
        "MORNING_BRIEFING": "MORNING_BRIEFING",

        # meal / cooking
        "MEAL": "MEAL",
        "EAT": "MEAL",
        "EATING": "MEAL",
        "FOOD": "MEAL",

        "COOK": "COOKING",
        "COOKING": "COOKING",
        "COOK_MEAL": "COOKING",

        # health
        "HEALTH": "HEALTH",
        "EXERCISE": "HEALTH",
        "WORKOUT": "HEALTH",

        # clothing
        "CLOTH": "CLOTHING",
        "CLOTHES": "CLOTHING",
        "CLOTHING": "CLOTHING",
        "DRESS": "CLOTHING",

        # leisure
        "LEISURE": "LEISURE",
        "REST": "LEISURE",
        "BREAK": "LEISURE",
        "RELAX": "LEISURE",
        "FUN": "LEISURE",
        "PLAY": "LEISURE",

        # routine
        "ROUTINE": "ROUTINE",
        "HYGIENE": "ROUTINE",
        "PREP": "ROUTINE",
        "PREPARATION": "ROUTINE",

        # night wrapup
        "NIGHT": "NIGHT_WRAPUP",
        "WRAPUP": "NIGHT_WRAPUP",
        "NIGHT_WRAPUP": "NIGHT_WRAPUP",

        # general
        "GENERAL": "GENERAL",
        "ETC": "GENERAL",
        "OTHER": "GENERAL",
    }
    type_norm = mapping.get(type_str, "GENERAL")

    # guide_script 최소 1개 보장 (혹시 비어 있으면 task 기반으로 채움)
    if not guide:
        if task:
            guide = [f"{task} 해요."]
        else:
            guide = ["이제 다음 활동을 해요."]

    return {
        "time": time_str,
        "type": type_norm,
        "task": task,
        "guide_script": guide,
    }


# ─────────────────────────────────────────────
# 3. 외부에서 쓰는 메인 함수
# ─────────────────────────────────────────────

_FALLBACK = [
    {
        "time": "09:00",
        "type": "GENERAL",
        "task": "일정 변환 오류. 코디네이터에게 다시 요청하기",
        "guide_script": [
            "일정을 불러오는 데 문제가 생겼어요.",
            "코디네이터에게 다시 한 번 일정을 만들어 달라고 부탁해 주세요.",
        ],
    }
]

# Gemini responseSchema로 출력 구조 강제
_SCHEDULE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "schedule": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "time": {"type": "STRING"},
                    "type": {"type": "STRING"},
                    "task": {"type": "STRING"},
                    "guide_script": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                    },
                },
                "required": ["time", "type", "task", "guide_script"],
            },
        }
    },
    "required": ["schedule"],
}

# 점수 기준
_MIN_SCORE = 60  # 이 점수 미만이면 재생성
_MAX_RETRIES = 1  # 최대 재시도 횟수 (무료 tier 고려)


def generate_schedule_from_text(user_text: str) -> List[Dict]:
    """
    자연어 일정 설명 → Gemini → 품질 평가 → (저점수 시 재생성) → 스케줄 리스트 반환.

    평가 + 재생성 루프:
    1. Gemini로 JSON 생성
    2. 규칙 기반 품질 평가 (0~100점)
    3. 60점 미만이면 구체적 피드백 주입 후 1회 재생성
    4. 최종 결과 반환
    """
    user_text = (user_text or "").strip()
    if not user_text:
        return []

    base_instruction = (
        "다음은 코디네이터가 적은 오늘 하루 일정 설명입니다.\n"
        "위에서 설명한 JSON 형식에 맞게 'schedule' 필드를 가진 하나의 객체로 변환해 주세요.\n"
        "설명이나 주석 없이 JSON만 출력하세요.\n\n"
        f"{user_text}"
    )

    best_schedule = None
    best_score = -1.0

    for attempt in range(_MAX_RETRIES + 1):
        # 재시도 시 피드백 주입
        if attempt == 0:
            instruction = base_instruction
        else:
            feedback = generate_retry_feedback(best_score, best_issues)
            instruction = f"{base_instruction}\n\n--- 수정 요청 ---\n{feedback}"

        try:
            content = gemini_generate(
                SYSTEM_PROMPT, instruction, response_schema=_SCHEDULE_SCHEMA
            )
        except Exception:
            if best_schedule is not None:
                return best_schedule
            return _FALLBACK

        # JSON 파싱
        try:
            obj = json.loads(content)
        except json.JSONDecodeError:
            if best_schedule is not None:
                return best_schedule
            return _FALLBACK

        # 스케줄 추출 + 정규화
        if isinstance(obj, dict):
            raw_schedule = obj.get("schedule", [])
        elif isinstance(obj, list):
            raw_schedule = obj
        else:
            raw_schedule = []

        schedule: List[Dict] = []
        for raw in raw_schedule:
            if isinstance(raw, dict):
                schedule.append(_normalize_item(raw))
        schedule.sort(key=lambda it: it.get("time", "00:00"))

        # 품질 평가
        score, issues = evaluate_schedule(schedule, user_text)

        # 베스트 갱신
        if score > best_score:
            best_schedule = schedule
            best_score = score
            best_issues = issues

        # 합격이면 바로 반환
        if score >= _MIN_SCORE:
            return schedule

    # 최대 재시도 후 베스트 반환
    return best_schedule if best_schedule else _FALLBACK
