# pages/2_사용자_오늘_따라하기.py
# -*- coding: utf-8 -*-

import base64
import json
import os
import re
from datetime import datetime
from typing import Optional, List, Dict

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from utils.topbar import render_topbar
from utils.runtime import find_active_item, annotate_schedule_with_status
from utils.recipes import get_recipe
from utils.tts import synthesize_tts  # bytes(mp3) 반환

# ─────────────────────────────────────────────
# 타임존 (Asia/Seoul)
# ─────────────────────────────────────────────
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

SCHEDULE_PATH = os.path.join("data", "schedule_today.json")
AUTO_REFRESH_SEC = 15
PRE_NOTICE_MINUTES = 5

# ─────────────────────────────────────────────
# 타입 영문 코드 숨기고, 한글 라벨만
# ─────────────────────────────────────────────
TYPE_KO = {
    "MORNING_BRIEFING": "아침 안내",
    "COOKING": "요리",
    "MEAL": "식사",
    "HEALTH": "운동",
    "CLOTHING": "옷 입기",
    "HOBBY": "취미/여가",
    "ROUTINE": "준비/위생",
    "NIGHT_WRAPUP": "하루 마무리",
    "GENERAL": "일정(기타)",
}

def _ko_type(type_code: str) -> str:
    t = (type_code or "").replace("[", "").replace("]", "").strip().upper()
    return TYPE_KO.get(t, "일정(기타)")

def _clean_text(s: str) -> str:
    """[MORNING_BRIEFING] 같은 내부 태그/코드가 보여주지 않게 제거"""
    s = (s or "").strip()
    s = re.sub(r"\[[A-Z0-9_]+\]\s*", "", s)
    return s

def _load_schedule():
    if not os.path.exists(SCHEDULE_PATH):
        return None
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    schedule = data.get("schedule", []) or []
    schedule_sorted = sorted(schedule, key=lambda it: (it.get("time") or "00:00"))
    return schedule_sorted, data.get("date")

def _make_slot_key(date_str: str, slot: Optional[dict]) -> Optional[str]:
    if not slot:
        return None
    t = (slot.get("type") or "").strip()
    time = (slot.get("time") or "").strip()
    task = _clean_text(slot.get("task") or "")
    return f"{date_str}::{time}::{t}::{task}"

# ─────────────────────────────────────────────
# 오디오 자동재생(성공률 높이기)
# autoplay + JS play 재시도 3회
# ─────────────────────────────────────────────
def _play_tts_auto_high_success(text: str, element_key: str):
    text = (text or "").strip()
    if not text:
        return
    audio_bytes = synthesize_tts(text)
    if not audio_bytes:
        return

    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_id = f"hibuddy_audio_{element_key}"

    html = f"""
    <audio id="{audio_id}" autoplay>
      <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
    </audio>
    <script>
      (function() {{
        const audio = document.getElementById("{audio_id}");
        if (!audio) return;
        let tries = 0;
        const tryPlay = () => {{
          tries += 1;
          const p = audio.play();
          if (p && p.catch) {{
            p.catch(() => {{
              if (tries < 4) {{
                setTimeout(tryPlay, tries * 400);
              }}
            }});
          }}
        }};
        setTimeout(tryPlay, 120);
      }})();
    </script>
    """
    st.components.v1.html(html, height=0)

def _tts_once_when_changed(text: str, change_key: str):
    """change_key가 바뀔 때만 자동 재생"""
    if not st.session_state.get("audio_unlocked", False):
        return
    prev = st.session_state.get("last_spoken_key")
    if change_key and change_key != prev:
        _play_tts_auto_high_success(text, element_key=change_key[-20:].replace(":", "_"))
        st.session_state["last_spoken_key"] = change_key

def _manual_replay_button(text: str, key: str, label: str = "🔁 다시 듣기"):
    if not text:
        return
    if st.button(label, type="primary", key=key):
        if st.session_state.get("audio_unlocked", False):
            _play_tts_auto_high_success(text, element_key=f"manual_{key}")
        else:
            st.warning("먼저 위에서 ✅ 소리 켜기를 한 번 눌러주세요.")

# ─────────────────────────────────────────────
# 슬롯 안내 문장(짧게)
# ─────────────────────────────────────────────
def _slot_intro_text(slot: dict) -> str:
    t = (slot.get("type") or "GENERAL").upper()
    task = _clean_text(slot.get("task") or "")
    head = {
        "MORNING_BRIEFING": "지금은 아침 안내 시간이에요.",
        "COOKING": "지금은 요리 시간이에요.",
        "MEAL": "지금은 식사 시간이에요.",
        "HEALTH": "지금은 운동 시간이에요.",
        "CLOTHING": "지금은 옷 입기 연습 시간이에요.",
        "HOBBY": "지금은 취미/여가 시간이에요.",
        "ROUTINE": "지금은 준비/위생 시간이에요.",
        "NIGHT_WRAPUP": "지금은 하루 마무리 시간이에요.",
        "GENERAL": "지금은 활동 시간이에요.",
    }.get(t, "지금은 활동 시간이에요.")
    return f"{head} 할 일은 {task} 입니다." if task else head

# ─────────────────────────────────────────────
# ✅ 오늘 일정 전체를 "한 번에 쭉" 읽어주는 텍스트 생성
# ─────────────────────────────────────────────
def _build_day_timeline_text(schedule: List[Dict], date_str: str) -> str:
    if not schedule:
        return "오늘 일정이 없어요."
    parts = [f"{date_str} 오늘 일정이에요."]
    for it in schedule:
        time_str = it.get("time", "").strip() or "시간 미정"
        task = _clean_text(it.get("task") or "")
        if task:
            parts.append(f"{time_str}에는 {task} 입니다.")
        else:
            parts.append(f"{time_str}에는 할 일이 있어요.")
    parts.append("이상입니다. 필요하면 다시 들을 수 있어요.")
    return " ".join(parts)

def _render_day_timeline_audio_panel(schedule: List[Dict], date_str: str):
    """
    - 소리 켠 직후: 오늘 일정 전체를 자동으로 1회 쭉 읽음
    - 버튼: 전체 다시 듣기 + 부분(항목별) 듣기
    """
    st.markdown("---")
    st.markdown("## 🗓 오늘 일정 전체 듣기")

    full_text = _build_day_timeline_text(schedule, date_str)

    # (자동) 오늘 일정 전체 1회 낭독
    # - 같은 날짜에서 1번만
    if st.session_state.get("audio_unlocked", False):
        if st.session_state.get("dayplan_read_date") != date_str:
            st.session_state["dayplan_read_date"] = date_str
            _tts_once_when_changed(full_text, change_key=f"dayplan::{date_str}")

    # (수동) 전체 다시 듣기
    _manual_replay_button(full_text, key=f"dayplan_replay_{date_str}", label="✅ 오늘 일정 전체 다시 듣기")

    # (수동) 부분 듣기(항목별)
    with st.expander("부분만 듣기(시간별)", expanded=False):
        for i, it in enumerate(schedule):
            time_str = it.get("time", "").strip() or "시간 미정"
            task = _clean_text(it.get("task") or "")
            line = f"{time_str}에는 {task} 입니다." if task else f"{time_str}에는 할 일이 있어요."
            # 버튼은 작게 여러 개
            if st.button(f"▶️ {time_str} 듣기", key=f"part_{date_str}_{i}"):
                if st.session_state.get("audio_unlocked", False):
                    _play_tts_auto_high_success(line, element_key=f"part_{date_str}_{i}")
                else:
                    st.warning("먼저 위에서 ✅ 소리 켜기를 한 번 눌러주세요.")

# ─────────────────────────────────────────────
# 단계 안내(스텝퍼)
# - 단계 바뀔 때 자동으로 읽음
# - 버튼은 '다시 듣기'만
# ─────────────────────────────────────────────
def _render_stepper(lines: List[str], state_key: str, title: str):
    lines = [(_clean_text(x) or "").strip() for x in (lines or []) if (_clean_text(x) or "").strip()]
    if not lines:
        lines = ["코디네이터에게 안내 문장을 추가해 달라고 부탁해 주세요."]

    if state_key not in st.session_state:
        st.session_state[state_key] = 0

    idx = max(0, min(st.session_state[state_key], len(lines) - 1))
    st.session_state[state_key] = idx
    current = lines[idx]

    st.markdown(f"### {title}")
    st.markdown(f"**{idx+1} / {len(lines)}**")

    # ✅ 자동 읽기(단계 바뀔 때)
    _tts_once_when_changed(current, change_key=f"step::{state_key}::{idx}")

    st.markdown(
        f"""
        <div style="padding:16px;border-radius:16px;border:1px solid #ddd;font-size:22px;line-height:1.5;">
          {current}
        </div>
        """,
        unsafe_allow_html=True
    )

    _manual_replay_button(current, key=f"{state_key}_replay")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("⏮ 처음", key=f"{state_key}_reset"):
            st.session_state[state_key] = 0
            st.rerun()
    with c2:
        if st.button("⬅ 이전", disabled=(idx == 0), key=f"{state_key}_prev"):
            st.session_state[state_key] = max(0, idx - 1)
            st.rerun()
    with c3:
        if st.button("다음 ➡", disabled=(idx == len(lines) - 1), key=f"{state_key}_next"):
            st.session_state[state_key] = min(len(lines) - 1, idx + 1)
            st.rerun()

# ─────────────────────────────────────────────
# 타입별 화면(간단화)
# ─────────────────────────────────────────────
def _render_cooking_view(slot: dict, slot_index: int):
    st.markdown("## 🍽 요리/식사")
    guide = slot.get("guide_script", []) or []
    if guide:
        _render_stepper(guide, f"cook_guide_{slot_index}", "안내")

    menus = slot.get("menus") or slot.get("menu_candidates") or []
    if not menus:
        st.info("아직 메뉴가 없어요. 코디네이터에게 메뉴를 넣어 달라고 부탁해 주세요.")
        return

    st.markdown("### 메뉴 고르기")
    st.caption("원하는 메뉴 버튼을 눌러주세요.")

    select_key = f"selected_menu_{slot_index}"
    if select_key not in st.session_state:
        st.session_state[select_key] = None

    cols = st.columns(min(3, len(menus)))
    for i, menu in enumerate(menus):
        name = _clean_text(menu.get("name") or f"메뉴 {i+1}")
        with cols[i % len(cols)]:
            if st.button(f"✅ {name}", type="primary", key=f"menu_btn_{slot_index}_{i}"):
                st.session_state[select_key] = name
                st.rerun()

    chosen = st.session_state.get(select_key)
    if not chosen:
        return

    st.markdown("---")
    st.markdown(f"### 선택한 메뉴: **{chosen}**")

    chosen_menu = next((m for m in menus if _clean_text(m.get("name") or "") == chosen), None)
    if chosen_menu and chosen_menu.get("video_url"):
        st.markdown("### ▶️ 영상 보기")
        st.video(chosen_menu["video_url"])

    recipe = get_recipe(chosen) or {}
    steps = recipe.get("steps") or []
    if steps:
        _render_stepper(steps, f"cook_steps_{slot_index}", "따라하기")
    else:
        st.info("이 메뉴는 따라하기 단계가 아직 없어요. 영상이 있으면 영상을 보고 따라 해요.")

def _render_health_view(slot: dict, slot_index: int):
    st.markdown("## 💪 운동")
    guide = slot.get("guide_script", []) or []
    if guide:
        _render_stepper(guide, f"health_guide_{slot_index}", "안내")

    v = slot.get("video_url")
    if v:
        st.markdown("### ▶️ 운동 영상")
        st.video(v)
    else:
        st.info("운동 영상이 아직 없어요. 코디네이터가 ‘영상’을 골라주면 여기서 바로 볼 수 있어요.")

def _render_clothing_view(slot: dict, slot_index: int):
    st.markdown("## 👕 옷 입기")
    guide = slot.get("guide_script", []) or []
    if guide:
        _render_stepper(guide, f"clothing_guide_{slot_index}", "안내")

    v = slot.get("video_url")
    if v:
        st.markdown("### ▶️ 옷 입기 영상")
        st.video(v)
    else:
        st.info("옷 입기 영상이 아직 없어요. 코디네이터가 ‘영상’을 골라주면 여기서 바로 볼 수 있어요.")

def _render_hobby_view(slot: dict, slot_index: int):
    st.markdown("## 🎬 취미/여가")
    guide = slot.get("guide_script", []) or []
    if guide:
        _render_stepper(guide, f"hobby_guide_{slot_index}", "안내")

    v = slot.get("video_url")
    if v:
        st.markdown("### ▶️ 영상 보기")
        st.video(v)
    else:
        st.info("여가 영상이 아직 없어요. 코디네이터가 ‘영상’을 골라주면 여기서 바로 볼 수 있어요.")

def _render_morning_view(slot: dict, slot_index: int):
    st.markdown("## ☀️ 아침 안내")
    guide = slot.get("guide_script", []) or []
    _render_stepper(guide, f"morning_guide_{slot_index}", "안내")

def _render_night_view(slot: dict, slot_index: int):
    st.markdown("## 🌙 하루 마무리")
    guide = slot.get("guide_script", []) or []
    _render_stepper(guide, f"night_guide_{slot_index}", "안내")

def _render_general_view(slot: dict, slot_index: int):
    st.markdown("## 🙂 지금 할 일")
    guide = slot.get("guide_script", []) or []
    if guide:
        _render_stepper(guide, f"general_guide_{slot_index}", "안내")
    else:
        st.info("안내 문장이 없어요. 코디네이터가 한두 줄만 넣어줘도 좋아요.")

# ─────────────────────────────────────────────
# 자동 TTS 로직(슬롯 변경/준비 알림)
# ─────────────────────────────────────────────
def _auto_tts_logic(now: datetime, date_str: str, active: Optional[dict], next_item: Optional[dict]):
    try:
        schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        schedule_date = now.date()

    if schedule_date != now.date():
        return

    if st.session_state.get("tts_date") != date_str:
        st.session_state["tts_date"] = date_str
        st.session_state["last_active_slot_key"] = None
        st.session_state["last_pre_notice_key"] = None
        st.session_state["last_spoken_key"] = None
        # dayplan_read_date는 “전체 읽기 1회” 제어
        st.session_state["dayplan_read_date"] = None

    if not st.session_state.get("audio_unlocked", False):
        return

    active_key = _make_slot_key(date_str, active)
    prev_active_key = st.session_state.get("last_active_slot_key")

    if active and active_key != prev_active_key:
        intro = _slot_intro_text(active)
        _tts_once_when_changed(intro, change_key=f"slot::{active_key}")
        st.session_state["last_active_slot_key"] = active_key
        return

    if next_item and next_item.get("time"):
        next_key = _make_slot_key(date_str, next_item)
        last_pre = st.session_state.get("last_pre_notice_key")

        try:
            slot_time = datetime.strptime(next_item["time"], "%H:%M").time()
            slot_dt = datetime.combine(schedule_date, slot_time).replace(tzinfo=KST)
            diff_min = (slot_dt - now).total_seconds() / 60.0
        except Exception:
            diff_min = None

        if diff_min is not None and 0 < diff_min <= PRE_NOTICE_MINUTES:
            if next_key and next_key != last_pre:
                msg = f"{next_item['time']}에 다음 할 일이 시작돼요. 미리 준비해요."
                _tts_once_when_changed(msg, change_key=f"prenotice::{next_key}")
                st.session_state["last_pre_notice_key"] = next_key

# ─────────────────────────────────────────────
# 최초 1회 소리 켜기 UI
# ─────────────────────────────────────────────
def _render_audio_unlock_panel():
    if "audio_unlocked" not in st.session_state:
        st.session_state["audio_unlocked"] = False

    if st.session_state["audio_unlocked"]:
        st.success("✅ 소리가 켜져 있어요. 이제부터는 자동으로 안내가 나옵니다.")
        return

    st.warning(
        "처음 이 화면에 들어오면, **꼭 한 번만** 아래 버튼을 눌러 주세요.\n\n"
        "- 이 버튼은 ‘소리 사용 허용’ 때문에 필요해요.\n"
        "- 한 번만 누르면, 이후에는 자동으로 말이 나옵니다.\n"
        "- 브라우저를 껐다 켜거나 새로고침하면 다시 필요할 수 있어요."
    )
    if st.button("✅ 소리 켜기 (한 번만 누르면 됩니다)", type="primary"):
        st.session_state["audio_unlocked"] = True
        _play_tts_auto_high_success("좋아요. 이제부터 자동으로 안내해 드릴게요.", element_key="unlock_ok")
        st.rerun()

# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def user_page():
    render_topbar()
    st_autorefresh(interval=AUTO_REFRESH_SEC * 1000, key="auto_refresh")

    data = _load_schedule()
    if not data:
        st.error("일정 파일이 없어요. 코디네이터가 먼저 ‘오늘 일정 저장’을 해주세요.")
        return

    schedule, date_str = data
    if not schedule:
        st.warning("오늘 일정이 비어 있어요. 코디네이터에게 확인해 달라고 부탁해 주세요.")
        return

    now = datetime.now(KST)
    now_time = now.time()

    active, next_item = find_active_item(schedule, now_time)
    annotated = annotate_schedule_with_status(schedule, now_time)

    st.markdown("# 👵 사용자 따라하기")
    st.caption("이 화면은 하루 동안 켜두고 사용해요. (자동으로 시간이 바뀝니다.)")

    # ✅ 최초 1회 “소리 켜기”
    _render_audio_unlock_panel()

    # ✅ 자동 음성: 슬롯 변경/준비 알림
    _auto_tts_logic(now, date_str, active, next_item)

    # ✅ 오늘 일정 전체 읽기 패널(자동 1회 + 다시듣기 + 부분듣기)
    _render_day_timeline_audio_panel(schedule, date_str)

    st.markdown("---")
    st.markdown(f"### 📅 오늘 날짜: **{date_str}**")
    st.markdown(f"### 🕒 지금 시간: **{now.strftime('%H:%M')}**")

    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.markdown("---")

        if not active:
            st.markdown("## 🙂 아직 첫 활동 전이에요")
            if next_item:
                nt = next_item.get("time", "??:??")
                task = _clean_text(next_item.get("task") or "")
                st.markdown(f"### ⏭ 다음 할 일: **{nt} · {task}**")
            return

        t = (active.get("type") or "GENERAL").upper()
        task = _clean_text(active.get("task") or "")
        header = f"지금 할 일: {task}"
        sub = f"종류: {_ko_type(t)}"

        st.markdown(
            f"""
            <div style="padding:18px;border-radius:18px;background:#f6f6f6;border:1px solid #e5e5e5;">
              <div style="font-size:26px;font-weight:700;">{header}</div>
              <div style="font-size:18px;margin-top:6px;">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 현재 슬롯 소개문: 자동은 _auto_tts_logic에서 처리됨
        # 여기서는 "다시 듣기" 버튼만 제공
        intro = _slot_intro_text(active)
        _manual_replay_button(intro, key=f"slot_replay_{date_str}_{active.get('time','')}_{task}")

        st.markdown("---")

        # 슬롯 인덱스(키 충돌 방지용)
        idx = 0
        for i, it in enumerate(schedule):
            if it.get("time") == active.get("time") and _clean_text(it.get("task") or "") == task:
                idx = i
                break

        if t == "COOKING":
            _render_cooking_view(active, idx)
        elif t == "MEAL":
            st.markdown("## 🍚 식사")
            guide = active.get("guide_script", []) or ["천천히 꼭꼭 씹어서 드세요.", "물도 한 번 마셔요."]
            _render_stepper(guide, f"meal_guide_{idx}", "안내")
        elif t == "HEALTH":
            _render_health_view(active, idx)
        elif t == "CLOTHING":
            _render_clothing_view(active, idx)
        elif t == "HOBBY":
            _render_hobby_view(active, idx)
        elif t == "MORNING_BRIEFING":
            _render_morning_view(active, idx)
        elif t == "NIGHT_WRAPUP":
            _render_night_view(active, idx)
        else:
            _render_general_view(active, idx)

    with col_side:
        st.markdown("### ⏭ 다음 할 일")
        if next_item:
            nt = next_item.get("time", "??:??")
            task = _clean_text(next_item.get("task") or "")
            st.markdown(f"**{nt} · {task}**")
        else:
            st.markdown("오늘 일정이 끝났어요.\n편안히 쉬어요.")

        st.markdown("---")
        st.markdown("### 🗓 오늘 타임라인")
        for item in annotated:
            time_str = item.get("time", "??:??")
            task = _clean_text(item.get("task") or "")
            status = item.get("status")

            if status == "active":
                st.markdown(f"- ✅ **{time_str} · {task}**")
            elif status == "past":
                st.markdown(f"- ⚪ {time_str} · {task}")
            else:
                st.markdown(f"- 🕒 {time_str} · {task}")

        st.markdown("---")
        if st.button("🔄 새로고침", key="manual_refresh"):
            st.rerun()

if __name__ == "__main__":
    user_page()
