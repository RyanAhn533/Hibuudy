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
당신은 발달장애인과 노인을 위한 하루 일정 코디네이터입니다.

역할:
- 코디네이터가 쓴 자연어 일정을 읽고,
- 이해하기 쉬운 하루 일정 슬롯 리스트로 변환합니다.
- 각 슬롯은 한 가지 활동만 포함합니다.

출력 규칙:
- 출력은 반드시 하나의 JSON 객체여야 합니다.
- 최상위 키는 "schedule" 입니다.

타입(type)은 아래 값 중 하나만 사용하세요:
- "GENERAL" : 일반 일정, 이동, 휴식, TV 보기 등
- "ROUTINE" : 준비, 세면, 샤워, 옷 입기 등
- "MEAL"    : 식사, 밥 먹기, 점심/저녁
- "COOKING" : 요리, 직접 만들어 먹기 (명시된 경우만)
- "HEALTH"  : 운동, 체조, 산책
- "HOBBY"   : 취미, 여가, 영상 시청

중요:
- "먹기", "식사"는 요리가 아니면 MEAL 입니다.
- 요리/만들기/끓이기 같은 표현이 있을 때만 COOKING을 사용하세요.
- 아침 인사, 하루 마무리 같은 내부 개념 타입은 사용하지 마세요.

각 슬롯 형식:
{
  "time": "HH:MM",
  "type": "GENERAL | ROUTINE | MEAL | COOKING | HEALTH | HOBBY",
  "task": "짧고 이해하기 쉬운 한 줄 설명",
  "guide_script": [
    "한 문장씩, 존댓말로",
    "천천히 안내하는 말"
  ]
}

주의:
- time은 반드시 HH:MM 형식
- guide_script는 1개 이상
- JSON 외 텍스트를 절대 출력하지 마세요.
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
        "GENERAL": "GENERAL",
        "ROUTINE": "ROUTINE",
        "MEAL": "MEAL",
        "COOKING": "COOKING",
        "HEALTH": "HEALTH",
        "HOBBY": "HOBBY",

        # 혹시 모델이 실수했을 때 대비
        "EAT": "MEAL",
        "FOOD": "MEAL",
        "COOK": "COOKING",
        "EXERCISE": "HEALTH",
        "WORKOUT": "HEALTH",
        "FUN": "HOBBY",
    }
    type_norm = mapping.get(type_str, "GENERAL")

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
