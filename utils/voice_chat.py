# utils/voice_chat.py
# -*- coding: utf-8 -*-
"""
음성 대화 모듈: 사용자의 텍스트 입력(STT 결과)을 받아
현재 활동 맥락에 맞는 GPT 응답을 생성하고 TTS로 재생.
"""
import os
from typing import Dict, Optional

from .config import get_openai_client


def chat_with_buddy(
    user_text: str,
    current_slot: Optional[Dict] = None,
    chat_history: list = None,
) -> str:
    """
    사용자 발화에 대해 Hi-Buddy 캐릭터로 GPT 응답 생성.

    Args:
        user_text: 사용자가 말한 텍스트 (STT 결과)
        current_slot: 현재 활동 슬롯 정보 (type, task, guide_script 등)
        chat_history: 이전 대화 기록 [{"role": "user"/"assistant", "content": "..."}]

    Returns:
        GPT 응답 텍스트
    """
    user_text = (user_text or "").strip()
    if not user_text:
        return "무슨 말인지 잘 못 들었어요. 다시 말해 줄래요?"

    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL_SCHEDULE", "gpt-4.1-mini")

    # 현재 활동 컨텍스트 구성
    context = ""
    if current_slot:
        slot_type = (current_slot.get("type") or "").upper()
        task = current_slot.get("task", "")
        guide = current_slot.get("guide_script", [])
        time_str = current_slot.get("time", "")

        context = f"""
현재 시간대: {time_str}
현재 활동 종류: {slot_type}
현재 할 일: {task}
안내 스크립트: {', '.join([str(x) for x in guide]) if isinstance(guide, list) else ''}
"""

    system_prompt = f"""너는 "하이버디(Hi-Buddy)"라는 이름의 발달장애인 일상 도우미야.
항상 친절하고 따뜻하게 말해. 반말(존댓말)로 말해줘.
문장은 짧고 쉽게 (20~40자). 한 번에 1~3문장만.
어려운 단어 쓰지 마. 이모지 쓰지 마.
사용자가 무엇을 해야 하는지, 어떻게 하는지 안내해줘.
사용자가 불안하거나 힘들다고 하면 위로해줘.
모르는 건 "잘 모르겠어요, 코디네이터에게 물어볼게요"라고 해.

{context}
"""

    messages = [{"role": "system", "content": system_prompt}]

    # 이전 대화 기록 추가 (최근 6개만)
    if chat_history:
        messages.extend(chat_history[-6:])

    messages.append({"role": "user", "content": user_text})

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=200,
    )

    answer = (resp.choices[0].message.content or "").strip()
    return answer or "잠깐만요, 다시 한번 말해 줄래요?"
