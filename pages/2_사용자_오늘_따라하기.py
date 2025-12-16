# pages/2_사용자_오늘_따라하기.py
# -*- coding: utf-8 -*-

import base64
import json
import os
import hashlib
from datetime import datetime
from typing import Optional
from urllib.parse import quote as urlquote

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from utils.topbar import render_topbar
from utils.runtime import find_active_item, annotate_schedule_with_status
from utils.recipes import get_recipe, get_health_routine
from utils.tts import synthesize_tts

# ─────────────────────────────────────────────
# 타임존
# ─────────────────────────────────────────────
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

SCHEDULE_PATH = os.path.join("data", "schedule_today.json")
AUTO_REFRESH_SEC = 10
PRE_NOTICE_MINUTES = 5

# ─────────────────────────────────────────────
# 타입 라벨
# ─────────────────────────────────────────────
TYPE_LABEL = {
    "GENERAL": "일정",
    "ROUTINE": "준비/위생",
    "MEAL": "식사",
    "COOKING": "요리",
    "HEALTH": "운동",
    "CLOTHING": "옷 입기",
    "HOBBY": "여가",
    "MORNING_BRIEFING": "아침 준비",
    "NIGHT_WRAPUP": "하루 마무리",
}


def _type_to_label(t: str) -> str:
    return TYPE_LABEL.get((t or "GENERAL").strip(), "일정")


# ─────────────────────────────────────────────
# TTS Queue
# ─────────────────────────────────────────────
TTS_QUEUE_KEY = "tts_queue"
TTS_LAST_MSG_KEY = "tts_last_msg_id"


def _enqueue_tts(text: str):
    text = (text or "").strip()
    if not text:
        return

    if TTS_QUEUE_KEY not in st.session_state:
        st.session_state[TTS_QUEUE_KEY] = []

    msg_id = hashlib.md5(text.encode("utf-8")).hexdigest()

    if st.session_state.get(TTS_LAST_MSG_KEY) == msg_id:
        return

    q = st.session_state[TTS_QUEUE_KEY]
    if q and q[-1]["id"] == msg_id:
        return

    q.append({"id": msg_id, "text": text})
    st.session_state[TTS_QUEUE_KEY] = q


def _play_next_tts_if_any():
    q = st.session_state.get(TTS_QUEUE_KEY, [])
    if not q:
        return

    MAX_CHARS = 800
    merged = []
    total = 0

    while q:
        txt = q[0]["text"]
        if merged and total + len(txt) > MAX_CHARS:
            break
        merged.append(txt)
        total += len(txt)
        q.pop(0)

    st.session_state[TTS_QUEUE_KEY] = q

    final_text = " ".join(merged).strip()
    if not final_text:
        return

    msg_id = hashlib.md5(final_text.encode("utf-8")).hexdigest()
    st.session_state[TTS_LAST_MSG_KEY] = msg_id

    audio = synthesize_tts(final_text)
    if not audio:
        return

    b64 = base64.b64encode(audio).decode("utf-8")
    st.markdown(
        f"""
        <audio autoplay>
          <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
        </audio>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# 일정 로드
# ─────────────────────────────────────────────
def _load_schedule():
    if not os.path.exists(SCHEDULE_PATH):
        return None

    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    schedule = data.get("schedule", []) or []
    schedule = sorted(schedule, key=lambda x: x.get("time", "00:00"))
    return schedule, data.get("date")


# ─────────────────────────────────────────────
# 슬롯 키
# ─────────────────────────────────────────────
def _make_slot_key(date_str: str, slot: Optional[dict]) -> Optional[str]:
    if not slot:
        return None
    return f"{date_str}_{slot.get('time')}_{slot.get('type')}_{slot.get('task')}"


# ─────────────────────────────────────────────
# 슬롯 시작 멘트
# ─────────────────────────────────────────────
def _slot_intro(slot: dict) -> str:
    label = _type_to_label(slot.get("type"))
    task = (slot.get("task") or "").strip()
    if task:
        return f"지금은 {label} 시간이에요. {task}을 시작해볼게요."
    return f"지금은 {label} 시간이에요."


# ─────────────────────────────────────────────
# 자동 TTS (띵동 포함)
# ─────────────────────────────────────────────
def _auto_tts(now, date_str, active, next_item):
    if st.session_state.get("last_date") != date_str:
        st.session_state["last_date"] = date_str
        st.session_state["last_slot_key"] = None
        st.session_state["dingdong_done"] = False

    current_key = _make_slot_key(date_str, active)

    if active and current_key != st.session_state.get("last_slot_key"):
        # 🔔 띵동 + 안내
        _enqueue_tts("띵동! 알림이 왔습니다.")
        _enqueue_tts(_slot_intro(active))
        st.session_state["last_slot_key"] = current_key


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def user_page():
    render_topbar()

    st_autorefresh(AUTO_REFRESH_SEC * 1000, key="auto")

    data = _load_schedule()
    if not data:
        st.error("코디네이터가 오늘 일정을 아직 저장하지 않았어요.")
        return

    schedule, date_str = data
    now = datetime.now(KST)
    now_time = now.time()

    active, next_item = find_active_item(schedule, now_time)
    annotated = annotate_schedule_with_status(schedule, now_time)

    _auto_tts(now, date_str, active, next_item)

    st.markdown(f"## 오늘 날짜: {date_str}")
    st.markdown(f"### 현재 시간: {now.strftime('%H:%M')}")
    st.markdown("---")

    if not active:
        st.info("아직 시작된 일정이 없어요.")
    else:
        t = active.get("type", "GENERAL")
        task = (active.get("task") or "").strip()

        st.header(f"지금은 {_type_to_label(t)} 시간이에요")
        if task:
            st.subheader(task)

        # ✅ 타입 무관, video_url 있으면 무조건 표시
        if active.get("video_url"):
            st.markdown("### 안내 영상")
            st.video(active["video_url"])

        # COOKING
        if t == "COOKING":
            menus = active.get("menus", [])
            if menus:
                for m in menus:
                    if m.get("video_url"):
                        st.markdown(f"### 🍳 {m.get('name')}")
                        st.video(m["video_url"])

        # HEALTH
        if t == "HEALTH":
            routine = get_health_routine("sit")
            if routine:
                steps = routine.get("steps", [])
                if steps:
                    _enqueue_tts(" ".join(steps))
                    for s in steps:
                        st.markdown(f"- {s}")

    st.markdown("---")
    st.markdown("### 오늘 타임라인")
    for it in annotated:
        label = f"{it.get('time')} · {_type_to_label(it.get('type'))} · {it.get('task')}"
        if it["status"] == "active":
            st.markdown(f"- ✅ **{label}**")
        elif it["status"] == "past":
            st.markdown(f"- ⚪ {label}")
        else:
            st.markdown(f"- 🕒 {label}")

    _play_next_tts_if_any()


if __name__ == "__main__":
    user_page()
