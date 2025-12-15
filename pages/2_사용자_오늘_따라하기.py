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
# 타임존 설정 (Asia/Seoul 고정)
# ─────────────────────────────────────────────
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

SCHEDULE_PATH = os.path.join("data", "schedule_today.json")
AUTO_REFRESH_SEC = 30
PRE_NOTICE_MINUTES = 5

# ─────────────────────────────────────────────
# 타입 라벨(원시 타입 코드 노출 금지)
# ─────────────────────────────────────────────
TYPE_LABEL = {
    "GENERAL": "일정(기타)",
    "ROUTINE": "준비/위생",
    "MEAL": "식사",
    "COOKING": "요리/식사",
    "HEALTH": "운동/건강",
    "CLOTHING": "옷 입기",
    "MORNING_BRIEFING": "아침 준비",
    "NIGHT_WRAPUP": "하루 마무리",
}


def _type_to_label(t: str) -> str:
    t = (t or "GENERAL").strip()
    return TYPE_LABEL.get(t, "일정(기타)")


# ─────────────────────────────────────────────
# TTS Queue Keys (버튼 없이 자동 재생용)
# ─────────────────────────────────────────────
TTS_QUEUE_KEY = "tts_queue"
TTS_LAST_MSG_KEY = "tts_last_msg_id"


# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────
def _load_schedule():
    if not os.path.exists(SCHEDULE_PATH):
        print(f"[DEBUG] SCHEDULE_PATH not found: {SCHEDULE_PATH}")
        return None
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    schedule = data.get("schedule", []) or []
    schedule_sorted = sorted(schedule, key=lambda it: (it.get("time") or "00:00"))

    print(
        f"[DEBUG] Loaded schedule: date={data.get('date')}, "
        f"items={len(schedule_sorted)}"
    )
    return schedule_sorted, data.get("date")


def _enqueue_tts(text: str):
    """TTS를 즉시 재생하지 않고 큐에 적재(중복 방지 포함)."""
    text = (text or "").strip()
    if not text:
        return

    if TTS_QUEUE_KEY not in st.session_state:
        st.session_state[TTS_QUEUE_KEY] = []

    msg_id = hashlib.md5(text.encode("utf-8")).hexdigest()

    # 직전 재생과 동일하면 스킵
    if st.session_state.get(TTS_LAST_MSG_KEY) == msg_id:
        return

    # 큐 마지막이 동일하면 스킵
    q = st.session_state[TTS_QUEUE_KEY]
    if q and q[-1].get("id") == msg_id:
        return

    q.append({"id": msg_id, "text": text})
    st.session_state[TTS_QUEUE_KEY] = q


def _play_next_tts_if_any():
    """rerun마다 큐에서 1개만 꺼내 autoplay 시도."""
    q = st.session_state.get(TTS_QUEUE_KEY, [])
    if not q:
        return

    item = q.pop(0)
    st.session_state[TTS_QUEUE_KEY] = q
    st.session_state[TTS_LAST_MSG_KEY] = item["id"]

    audio_bytes = synthesize_tts(item["text"])
    if not audio_bytes:
        return

    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
    <audio autoplay>
      <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
      브라우저에서 오디오를 지원하지 않습니다.
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)


def _make_slot_key(date_str: str, slot: Optional[dict]) -> Optional[str]:
    if not slot:
        return None
    return f"{date_str}_{slot.get('time')}_{slot.get('type')}_{slot.get('task')}"


def _normalize_lines(lines) -> list:
    if not lines:
        return []
    out = []
    for x in lines:
        s = (x or "").strip()
        if s:
            out.append(s)
    return out


def _join_lines_for_tts(lines: list) -> str:
    """단계/문장들을 '통으로' 이어서 한 번에 말하기용 텍스트로 만든다."""
    lines = _normalize_lines(lines)
    if not lines:
        return ""
    return " ".join(lines)


def _speak_once_per_slot(slot_key: str, text: str):
    """
    같은 슬롯에서 같은 멘트는 1번만 말하게 한다.
    슬롯이 바뀌면 slot_key가 바뀌므로 다시 말할 수 있다.
    """
    text = (text or "").strip()
    if not text or not slot_key:
        return

    spoken_key = f"spoken::{slot_key}"
    if st.session_state.get(spoken_key):
        return

    _enqueue_tts(text)
    st.session_state[spoken_key] = True


def _build_slot_intro_text(slot: dict) -> str:
    t = slot.get("type", "GENERAL")
    task = (slot.get("task") or "").strip()

    if t == "MORNING_BRIEFING":
        head = "지금은 아침 준비 시간이에요."
    elif t == "COOKING":
        head = "지금은 요리하고 밥을 먹는 시간이에요."
    elif t == "HEALTH":
        head = "지금은 운동하고 건강을 챙기는 시간이에요."
    elif t == "CLOTHING":
        head = "지금은 옷 입기 연습 시간이에요."
    elif t == "NIGHT_WRAPUP":
        head = "지금은 오늘 하루를 마무리하는 시간이에요."
    else:
        head = "지금은 활동 시간이에요."

    if task:
        return f"{head} 이번 활동은 {task} 입니다."
    return head


def _get_menu_image_url(menu: dict) -> Optional[str]:
    img_path = menu.get("image")
    if isinstance(img_path, str) and img_path.strip():
        if os.path.exists(img_path):
            return img_path
        alt_path = os.path.join(os.getcwd(), img_path)
        if os.path.exists(alt_path):
            return alt_path
        print(f"[DEBUG] _get_menu_image_url: local image not found -> {img_path}")

    img_url = menu.get("image_url")
    if isinstance(img_url, str) and img_url.strip():
        return img_url

    name = (menu.get("name") or "").strip()
    if not name:
        return None

    cache_key = f"menu_img_cache::{name}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    query = urlquote(name)
    url = f"https://source.unsplash.com/featured/?{query}"
    st.session_state[cache_key] = url
    print(f"[DEBUG] _get_menu_image_url: name={name}, url={url}")
    return url


# ─────────────────────────────────────────────
# 화면용 Stepper (TTS 없음)
# ─────────────────────────────────────────────
def _render_stepper_ui(lines, state_key: str, title: str):
    """
    화면에서 단계별로 보기 좋게 보여주기만 함.
    TTS는 여기서 절대 하지 않음.
    """
    if state_key not in st.session_state:
        st.session_state[state_key] = 0

    lines = _normalize_lines(lines)
    if not lines:
        lines = ["코디네이터에게 멘트를 추가해 달라고 부탁해 주세요."]

    idx = st.session_state[state_key]
    idx = max(0, min(idx, len(lines) - 1))

    st.markdown(f"### {title}")
    st.markdown(f"**{idx+1} / {len(lines)} 단계**")
    st.write(lines[idx])

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("처음부터", key=state_key + "_reset"):
            st.session_state[state_key] = 0
    with col2:
        if st.button("⬅ 이전", disabled=(idx == 0), key=state_key + "_prev"):
            st.session_state[state_key] = max(0, idx - 1)
    with col3:
        if st.button("다음 ➡", disabled=(idx == len(lines) - 1), key=state_key + "_next"):
            st.session_state[state_key] = min(len(lines) - 1, idx + 1)


# ─────────────────────────────────────────────
# COOKING 뷰 (영상은 항상 보이게 + TTS는 통합으로)
# ─────────────────────────────────────────────
def _render_cooking_view(slot, slot_index: int, slot_key: str):
    st.subheader("지금은 **요리·식사 시간**이에요 🍽")

    # 1) 슬롯 공통 안내 영상(video_url) — 항상 표시
    common_video = slot.get("video_url")
    if common_video:
        st.markdown("### 요리 안내 영상")
        st.video(common_video)

    guide = _normalize_lines(slot.get("guide_script", []))
    if guide:
        # TTS는 통합해서 1번만
        _speak_once_per_slot(slot_key + "::guide", _join_lines_for_tts(guide))
        # 화면은 단계별 UI
        _render_stepper_ui(guide, f"guide_cooking_{slot_index}", "지금 안내")

    menus = slot.get("menus") or slot.get("menu_candidates") or []
    if not menus:
        st.info(
            "아직 메뉴가 준비되지 않았어요.\n"
            "코디네이터에게 메뉴를 설정해 달라고 부탁해 주세요."
        )
        return

    select_key = f"selected_menu_{slot_index}"

    # 2) 메뉴가 1개면 자동 선택
    if len(menus) == 1 and not st.session_state.get(select_key):
        only_name = (menus[0].get("name") or "").strip()
        st.session_state[select_key] = only_name
        if only_name:
            _enqueue_tts(f"{only_name} 메뉴로 진행할게요.")

    st.markdown("### 먹고 싶은 메뉴를 골라요")
    st.caption("※ 메뉴가 1개면 자동으로 선택됩니다.")

    cols = st.columns(len(menus))
    for i, menu in enumerate(menus):
        name = (menu.get("name") or "").strip()
        recipe = get_recipe(name) or {}
        emoji = recipe.get("emoji", "🍽")

        with cols[i]:
            img_url = _get_menu_image_url(menu)
            if img_url:
                st.image(img_url, caption=name or "메뉴", use_container_width=True)
            else:
                if os.path.exists("assets/images/default_food.png"):
                    st.image(
                        "assets/images/default_food.png",
                        caption=name or "메뉴",
                        use_container_width=True,
                    )
                else:
                    st.write("이미지가 아직 준비되지 않았어요.")

            button_label = f"{emoji} {name}" if name else f"{emoji} 메뉴 선택"
            if st.button(button_label, key=f"menu_btn_{slot_index}_{i}"):
                st.session_state[select_key] = name
                if name:
                    _enqueue_tts(f"{name} 메뉴를 선택했어요.")

    chosen = (st.session_state.get(select_key) or "").strip()
    if not chosen:
        return

    chosen_menu = next((m for m in menus if (m.get("name") or "").strip() == chosen), None)

    # 3) 선택된 메뉴의 영상은 항상 표시
    if chosen_menu:
        vurl = chosen_menu.get("video_url")
        if vurl:
            st.markdown("---")
            st.markdown("### 요리 방법 영상")
            st.video(vurl)

    recipe = get_recipe(chosen)
    if not recipe:
        recipe = {
            "name": chosen,
            "tools": [],
            "ingredients": [],
            "steps": [
                "식사 전에는 손을 깨끗이 씻어요.",
                "천천히, 꼭꼭 씹으면서 먹어요.",
                "다 먹으면 그릇을 싱크대로 가져다 놓아요.",
            ],
        }

    tools = recipe.get("tools", [])
    ingredients = recipe.get("ingredients", [])
    steps = _normalize_lines(recipe.get("steps", []))

    st.markdown("---")
    st.markdown(f"## {recipe['name']} 준비하기")

    if tools:
        st.markdown("### 준비 도구")
        for t in tools:
            st.markdown(f"- {t}")

    if ingredients:
        st.markdown("### 준비 재료")
        for ing in ingredients:
            st.markdown(f"- {ing}")

    if steps:
        # 레시피 단계도 TTS는 통합해서 1번만
        _speak_once_per_slot(slot_key + f"::recipe::{chosen}", _join_lines_for_tts(steps))
        st.markdown("---")
        _render_stepper_ui(steps, f"cook_steps_{slot_index}", "만들기 단계")
    else:
        st.warning("레시피 단계 정보가 없습니다.")


# ─────────────────────────────────────────────
# HEALTH / NIGHT / MORNING / GENERAL / CLOTHING
# ─────────────────────────────────────────────
def _render_health_view(slot, slot_index: int, slot_key: str):
    st.subheader("지금은 **운동 / 건강 시간**이에요 💪")

    guide = _normalize_lines(slot.get("guide_script", []))
    if guide:
        _speak_once_per_slot(slot_key + "::guide", _join_lines_for_tts(guide))
        _render_stepper_ui(guide, f"guide_health_{slot_index}", "지금 안내")

    current_video = slot.get("video_url")
    if current_video:
        st.markdown("### 운동 설명 영상")
        st.video(current_video)

    modes = slot.get("health_modes") or [
        {"id": "sit", "name": "앉아서 하는 운동"},
        {"id": "stand", "name": "서서 하는 운동"},
    ]

    select_key = f"selected_health_{slot_index}"

    if len(modes) == 1 and not st.session_state.get(select_key):
        st.session_state[select_key] = modes[0]["id"]
        _enqueue_tts(f"{modes[0]['name']}으로 진행할게요.")

    st.markdown("### 어떤 운동을 할까요?")
    cols = st.columns(len(modes))
    for i, mode in enumerate(modes):
        with cols[i]:
            if st.button(mode["name"], key=f"health_btn_{slot_index}_{i}"):
                st.session_state[select_key] = mode["id"]
                _enqueue_tts(f"{mode['name']}을 선택했어요.")

    chosen = st.session_state.get(select_key)
    if not chosen:
        return

    routine = get_health_routine(chosen)
    if not routine:
        st.warning("이 운동에 대한 설명이 아직 준비되지 않았어요.")
        return

    steps = _normalize_lines(routine.get("steps", []))
    if not steps:
        st.warning("운동 단계 정보가 없습니다.")
        return

    _speak_once_per_slot(slot_key + f"::routine::{chosen}", _join_lines_for_tts(steps))
    _render_stepper_ui(steps, f"health_steps_{slot_index}", routine.get("name", "운동 안내"))


def _render_night_view(slot, slot_index: int, slot_key: str):
    st.subheader("지금은 **하루 마무리 시간**이에요 🌙")
    guide = _normalize_lines(slot.get("guide_script", []))
    if guide:
        _speak_once_per_slot(slot_key + "::guide", _join_lines_for_tts(guide))
        _render_stepper_ui(guide, f"guide_night_{slot_index}", "마무리 안내")
    else:
        st.info("마무리 안내가 아직 준비되지 않았어요.")


def _render_morning_view(slot, slot_index: int, slot_key: str):
    st.subheader("지금은 **아침 준비 시간**이에요 ☀️")
    guide = _normalize_lines(slot.get("guide_script", []))
    if guide:
        _speak_once_per_slot(slot_key + "::guide", _join_lines_for_tts(guide))
        _render_stepper_ui(guide, f"guide_morning_{slot_index}", "아침 안내")
    else:
        st.info("아침 안내가 아직 준비되지 않았어요.")


def _render_clothing_view(slot, slot_index: int, slot_key: str):
    st.subheader("지금은 **옷 입기 연습 시간**이에요 👕")

    guide = _normalize_lines(slot.get("guide_script", []))
    if guide:
        _speak_once_per_slot(slot_key + "::guide", _join_lines_for_tts(guide))
        _render_stepper_ui(guide, f"guide_clothing_{slot_index}", "옷 입기 안내")

    current_video = slot.get("video_url")
    if current_video:
        st.markdown("### 옷 입기 설명 영상")
        st.video(current_video)
    else:
        st.info("코디네이터에게 옷 입기 설명 영상을 설정해 달라고 부탁해 주세요.")


def _render_general_view(slot, slot_index: int, slot_key: str):
    st.subheader("지금은 **일반 활동 시간**이에요.")
    task = (slot.get("task") or "").strip()
    if task:
        st.markdown(f"### 활동: {task}")

    guide = _normalize_lines(slot.get("guide_script", []))
    if guide:
        _speak_once_per_slot(slot_key + "::guide", _join_lines_for_tts(guide))
        _render_stepper_ui(guide, f"guide_general_{slot_index}", "활동 안내")
    else:
        st.info("활동 안내가 아직 준비되지 않았어요.")


# ─────────────────────────────────────────────
# 기타 유틸
# ─────────────────────────────────────────────
def _get_slot_index(schedule, target_slot):
    for i, item in enumerate(schedule):
        if (
            item.get("time") == target_slot.get("time")
            and item.get("type") == target_slot.get("type")
            and item.get("task") == target_slot.get("task")
        ):
            return i
    return 0


# ─────────────────────────────────────────────
# 자동 TTS 로직 (슬롯 진입/변경 시 통합 멘트 1회)
# ─────────────────────────────────────────────
def _auto_tts_logic(now: datetime, date_str: str, active: Optional[dict], next_item: Optional[dict]):
    try:
        schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        schedule_date = now.date()

    if schedule_date != now.date():
        return

    if st.session_state.get("greeting_date") != date_str:
        st.session_state["greeting_tts_done"] = False
        st.session_state["greeting_date"] = date_str
        st.session_state["last_tts_slot_key"] = None
        st.session_state["last_pre_notice_slot_key"] = None

    if "greeting_tts_done" not in st.session_state:
        st.session_state["greeting_tts_done"] = False
    if "last_tts_slot_key" not in st.session_state:
        st.session_state["last_tts_slot_key"] = None
    if "last_pre_notice_slot_key" not in st.session_state:
        st.session_state["last_pre_notice_slot_key"] = None

    greeting_done = st.session_state["greeting_tts_done"]
    last_slot_key = st.session_state["last_tts_slot_key"]
    last_pre_notice_key = st.session_state["last_pre_notice_slot_key"]

    current_slot_key = _make_slot_key(date_str, active)
    next_slot_key = _make_slot_key(date_str, next_item)

    hour = now.hour
    if hour < 12:
        greeting = "좋은 아침이에요."
    elif hour < 18:
        greeting = "좋은 오후예요."
    else:
        greeting = "좋은 저녁이에요."

    base_greeting_text = f"{greeting} 오늘도 하이버디랑 함께 해볼까요?"

    if not greeting_done:
        if active:
            slot_intro = _build_slot_intro_text(active)
            _enqueue_tts(f"{base_greeting_text} {slot_intro}")
        else:
            _enqueue_tts(base_greeting_text)
        st.session_state["greeting_tts_done"] = True
        st.session_state["last_tts_slot_key"] = current_slot_key
        return

    # 슬롯 변경 시: 슬롯 소개 멘트 1회
    if active and current_slot_key != last_slot_key:
        slot_intro = _build_slot_intro_text(active)
        _enqueue_tts(slot_intro)
        st.session_state["last_tts_slot_key"] = current_slot_key
        return

    # 다음 활동 준비 알림
    if next_item and next_item.get("time"):
        try:
            slot_time = datetime.strptime(next_item["time"], "%H:%M").time()
            slot_dt = datetime.combine(schedule_date, slot_time).replace(tzinfo=KST)
            diff_min = (slot_dt - now).total_seconds() / 60.0
        except Exception:
            diff_min = None

        if diff_min is not None and 0 < diff_min <= PRE_NOTICE_MINUTES:
            if next_slot_key and next_slot_key != last_pre_notice_key:
                label = _type_to_label(next_item.get("type"))
                task = (next_item.get("task") or "").strip()
                pre_text = f"{next_item['time']}에 {label} 활동이 시작돼요. {task} 준비를 해볼까요?"
                _enqueue_tts(pre_text)
                st.session_state["last_pre_notice_slot_key"] = next_slot_key
                return


# ─────────────────────────────────────────────
# 메인 엔트리
# ─────────────────────────────────────────────
def user_page():
    render_topbar()

    st_autorefresh(
        interval=AUTO_REFRESH_SEC * 1000,
        key="auto_refresh",
    )

    data = _load_schedule()
    if not data:
        st.error(
            "data/schedule_today.json 파일을 찾을 수 없습니다.\n"
            "코디네이터 페이지에서 먼저 일정을 저장해 주세요."
        )
        return

    schedule, date_str = data
    if not schedule:
        st.warning("스케줄이 비어 있습니다. 코디네이터에게 일정을 확인해 달라고 부탁해 주세요.")
        return

    now = datetime.now(KST)
    now_time = now.time()

    active, next_item = find_active_item(schedule, now_time)
    annotated = annotate_schedule_with_status(schedule, now_time)

    _auto_tts_logic(now, date_str, active, next_item)

    hour = now.hour
    if hour < 12:
        greeting = "좋은 아침이에요 ☀️"
    elif hour < 18:
        greeting = "좋은 오후예요 😊"
    else:
        greeting = "좋은 저녁이에요 🌙"

    base_greeting_text = f"{greeting} 오늘도 하이버디랑 함께 해볼까요?"
    st.markdown(f"## {base_greeting_text}")
    st.caption("※ 이 화면은 발달장애인 사용자가 하루 동안 켜두는 화면입니다.")

    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.markdown(f"### 오늘 날짜: **{date_str}**")
        st.markdown(f"### 지금 시간: **{now.strftime('%H:%M')}**")
        st.markdown("---")

        if not active:
            st.header("아직 첫 활동 전이에요 🙂")
            if next_item:
                label = _type_to_label(next_item.get("type"))
                task = (next_item.get("task") or "").strip()
                st.write("곧 시작될 첫 활동:")
                st.write(f"- {next_item.get('time')} · {label} · {task}")
        else:
            idx = _get_slot_index(schedule, active)
            t = active.get("type", "GENERAL")
            task = (active.get("task") or "").strip()

            if t == "MORNING_BRIEFING":
                header_text = "지금은 아침 준비 시간이에요 ☀️"
            elif t == "COOKING":
                header_text = "지금은 맛있는 식사 시간이에요 🍽"
            elif t == "HEALTH":
                header_text = "지금은 내 몸을 돌보는 시간이에요 💪"
            elif t == "CLOTHING":
                header_text = "지금은 옷 입기 연습 시간이에요 👕"
            elif t == "NIGHT_WRAPUP":
                header_text = "지금은 오늘을 마무리하는 시간이에요 🌙"
            else:
                header_text = "지금은 활동 시간이에요 🙂"

            st.header(header_text)
            if task:
                st.markdown(f"#### 오늘 할 일: **{task}**")

            slot_key = _make_slot_key(date_str, active) or f"{date_str}::{idx}"

            if t == "COOKING":
                _render_cooking_view(active, idx, slot_key)
            elif t == "HEALTH":
                _render_health_view(active, idx, slot_key)
            elif t == "CLOTHING":
                _render_clothing_view(active, idx, slot_key)
            elif t == "MORNING_BRIEFING":
                _render_morning_view(active, idx, slot_key)
            elif t == "NIGHT_WRAPUP":
                _render_night_view(active, idx, slot_key)
            else:
                _render_general_view(active, idx, slot_key)

    with col_side:
        st.markdown("### ⏭ 다음 활동")
        if next_item:
            label = _type_to_label(next_item.get("type"))
            task = (next_item.get("task") or "").strip()
            st.markdown(f"**{next_item.get('time')}** · {label} · {task}")
        else:
            st.write("오늘 일정은 모두 끝났어요.\n편안하게 쉬어요.")

        st.markdown("---")
        st.markdown("### 🗓 오늘 타임라인")

        for item in annotated:
            label = (
                f"{item.get('time', '??:??')} · "
                f"{_type_to_label(item.get('type'))} · "
                f"{(item.get('task') or '').strip()}"
            )
            status = item.get("status")
            if status == "active":
                st.markdown(f"- ✅ **{label}**")
            elif status == "past":
                st.markdown(f"- ⚪ {label}")
            else:
                st.markdown(f"- 🕒 {label}")

        st.markdown("---")
        if st.button("화면 수동 새로고침"):
            st.rerun()

    # 화면 렌더링 끝나고, 큐에서 1개만 재생 시도
    _play_next_tts_if_any()


if __name__ == "__main__":
    user_page()
