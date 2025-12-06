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

from .config import get_openai_client, OPENAI_MODEL_SCHEDULE


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
- type: 아래 값 중 하나
  - "MORNING_BRIEFING" : 아침 인사, 날씨, 오늘 일정 소개
  - "COOKING"          : 요리, 식사, 간식, 밥 먹기
  - "HEALTH"           : 운동, 산책, 스트레칭, 건강 관리
  - "GENERAL"          : 공부, 놀이, TV 보기, 외출 등 일반 활동
  - "NIGHT_WRAPUP"     : 하루 마무리, 정리, 취침 준비
- task: 코디네이터가 이해하기 쉬운 한 줄 설명
  예: "라면 또는 카레 중 하나 먹기"
- guide_script: 발달장애인이 보기 쉬운 짧은 문장 배열
  - 존댓말 사용 (예: "~해요.")
  - 한 문장도 너무 길지 않게
  - 단계별로 천천히 안내

타입 분류 힌트:
- "밥", "식사", "점심", "저녁", "아침 먹기", "요리", "간식" → COOKING
- "운동", "체조", "스트레칭", "산책", "걷기", "헬스" → HEALTH
- "잠자기", "취침", "하루 마무리", "정리하기" → NIGHT_WRAPUP
- "날씨 안내", "아침 인사", "오늘 일정 소개" → MORNING_BRIEFING
- 그 외 → GENERAL

주의:
- time 은 반드시 "HH:MM" 형식만 사용합니다.
- guide_script 는 적어도 1개 이상의 문자열을 포함해야 합니다.
- JSON 외의 설명, 코드블럭, 텍스트를 절대 추가하지 마세요.
"""


# ─────────────────────────────────────────────
# 2. 내부 유틸
# ─────────────────────────────────────────────

def _normalize_item(raw: Dict) -> Dict:
    """GPT가 준 한 슬롯(dict)을 안전하게 정리."""
    time_str = str(raw.get("time", "00:00"))
    type_str = str(raw.get("type", "GENERAL")).upper()
    task = raw.get("task") or ""

    guide = raw.get("guide_script") or []
    if isinstance(guide, str):
        guide = [guide]
    elif isinstance(guide, list):
        guide = [str(g) for g in guide if g]
    else:
        guide = []

    # type 값 조금 정리
    mapping = {
        "MORNING": "MORNING_BRIEFING",
        "MORNING_BRIEFING": "MORNING_BRIEFING",
        "COOK": "COOKING",
        "COOKING": "COOKING",
        "MEAL": "COOKING",
        "EAT": "COOKING",
        "HEALTH": "HEALTH",
        "EXERCISE": "HEALTH",
        "WORKOUT": "HEALTH",
        "NIGHT": "NIGHT_WRAPUP",
        "WRAPUP": "NIGHT_WRAPUP",
        "NIGHT_WRAPUP": "NIGHT_WRAPUP",
        "GENERAL": "GENERAL",
    }
    type_norm = mapping.get(type_str, "GENERAL")

    return {
        "time": time_str,
        "type": type_norm,
        "task": task,
        "guide_script": guide,
    }


# ─────────────────────────────────────────────
# 3. 외부에서 쓰는 메인 함수
# ─────────────────────────────────────────────

def generate_schedule_from_text(user_text: str) -> List[Dict]:
    """
    자연어 일정 설명 → GPT → 스케줄 리스트(List[Dict]) 반환.

    pages/1_코디네이터_일정입력.py 에서 이 함수를 호출해서
    바로 schedule 리스트를 받는 구조.
    """
    user_text = (user_text or "").strip()
    if not user_text:
        return []

    client = get_openai_client()

    # chat.completions에 JSON 강제 옵션 사용
    response = client.chat.completions.create(
        model=OPENAI_MODEL_SCHEDULE,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "다음은 코디네이터가 적은 오늘 하루 일정 설명입니다.\n"
                    "위에서 설명한 JSON 형식에 맞게 'schedule' 필드를 가진 하나의 객체로 변환해 주세요.\n\n"
                    f"{user_text}"
                ),
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},  # 🔥 JSON 강제
    )

    content = response.choices[0].message.content or ""

    # response_format을 json_object로 줬기 때문에 content는 순수 JSON 문자열이어야 함
    try:
        obj = json.loads(content)
    except json.JSONDecodeError:
        # 혹시라도 깨지면 아주 단순한 fallback 반환
        return [
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

    # obj 가 {"schedule": [...]} 구조라고 가정
    if isinstance(obj, dict):
        raw_schedule = obj.get("schedule", [])
    elif isinstance(obj, list):
        # 혹시 모델이 그대로 리스트만 준 경우
        raw_schedule = obj
    else:
        raw_schedule = []

    schedule: List[Dict] = []
    for raw in raw_schedule:
        if isinstance(raw, dict):
            schedule.append(_normalize_item(raw))

    # time 기준 정렬
    schedule.sort(key=lambda it: it.get("time", "00:00"))
    return schedule
