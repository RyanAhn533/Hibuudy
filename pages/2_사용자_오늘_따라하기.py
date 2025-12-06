# pages/2_사용자_오늘_따라하기.py
# -*- coding: utf-8 -*-
import base64
import json
import os
from datetime import datetime
from typing import Optional

from urllib.parse import quote as urlquote  # 메뉴 이름을 이미지 검색 쿼리로 쓰기 위해 인코딩

import streamlit as st
from streamlit_autorefresh import st_autorefresh  # 세션 유지 자동 새로고침

from utils.topbar import render_topbar
from utils.runtime import find_active_item, annotate_schedule_with_status
from utils.recipes import get_recipe, get_health_routine
from utils.tts import synthesize_tts  # TTS 유틸

SCHEDULE_PATH = os.path.join("data", "schedule_today.json")
AUTO_REFRESH_SEC = 30  # 몇 초마다 자동으로 화면 새로고침할지
PRE_NOTICE_MINUTES = 5  # 다음 활동 시작 몇 분 전에 준비 알림을 줄지


# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────
def _load_schedule():
    """data/schedule_today.json에서 스케줄과 날짜를 읽어온다."""
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


def _play_tts_auto(text: str):
    """
    자동으로 재생되는 TTS.
    (일부 브라우저는 첫 상호작용 전 자동 재생을 막을 수 있음)
    """
    text = (text or "").strip()
    if not text:
        print("[DEBUG] _play_tts_auto: empty text, skip")
        return

    print(f"[DEBUG] _play_tts_auto: text='{text[:50]}...'")
    audio_bytes = synthesize_tts(text)
    if not audio_bytes:
        print("[DEBUG] _play_tts_auto: synthesize_tts returned None/empty")
        return

    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
    <audio autoplay>
      <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
      브라우저에서 오디오를 지원하지 않습니다.
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)


def _tts_button(text: str, key: str, label: str = "🔊 듣기"):
    text = (text or "").strip()
    if not text:
        return
    if st.button(label, key=key):
        print(f"[DEBUG] _tts_button clicked: key={key}, text='{text[:50]}...'")
        audio_bytes = synthesize_tts(text)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")


def _build_slot_tts_text(slot: dict) -> str:
    t = slot.get("type", "GENERAL")
    task = slot.get("task", "")
    guide = slot.get("guide_script") or []
    first = guide[0] if guide else ""

    if t == "MORNING_BRIEFING":
        head = "지금은 아침 준비 시간이에요."
    elif t == "COOKING":
        head = "지금은 요리하고 밥을 먹는 시간이에요."
    elif t == "HEALTH":
        head = "지금은 운동하고 건강을 챙기는 시간이에요."
    elif t == "NIGHT_WRAPUP":
        head = "지금은 오늘 하루를 마무리하는 시간이에요."
    else:
        head = "지금은 활동 시간이에요."

    parts = [head]
    if task:
        parts.append(f"이번 활동은 {task} 입니다.")
    if first:
        parts.append(first)
    return " ".join(parts)


def _make_slot_key(date_str: str, slot: Optional[dict]) -> Optional[str]:
    if not slot:
        return None
    return f"{date_str}_{slot.get('time')}_{slot.get('type')}_{slot.get('task')}"


def _get_menu_image_url(menu: dict) -> Optional[str]:
    """
    COOKING 메뉴 하나에 대해 보여줄 이미지 URL을 결정한다.

    우선순위:
    1) 로컬 경로가 실제 존재하면 그걸 사용
    2) image_url(웹 URL)이 있으면 그걸 사용
    3) 메뉴 이름 기반 Unsplash 기본 이미지
    """
    # 1) 로컬 이미지 경로
    img_path = menu.get("image")
    if isinstance(img_path, str) and img_path.strip():
        if os.path.exists(img_path):
            return img_path
        alt_path = os.path.join(os.getcwd(), img_path)
        if os.path.exists(alt_path):
            return alt_path
        print(f"[DEBUG] _get_menu_image_url: local image not found -> {img_path}")

    # 2) 원본 웹 URL
    img_url = menu.get("image_url")
    if isinstance(img_url, str) and img_url.strip():
        return img_url

    # 3) 기본 이미지 (Unsplash)
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
# 단계 안내 컴포넌트
# ─────────────────────────────────────────────
def _render_stepper(lines, state_key: str, title: str):
    if state_key not in st.session_state:
        st.session_state[state_key] = 0

    if not lines:
        lines = ["코디네이터에게 멘트를 추가해 달라고 부탁해 주세요."]

    idx = st.session_state[state_key]
    idx = max(0, min(idx, len(lines) - 1))

    st.markdown(f"### {title}")
    st.markdown(f"**{idx+1} / {len(lines)} 단계**")

    current_text = lines[idx]
    st.write(current_text)

    _tts_button(
        current_text,
        key=state_key + "_tts_btn",
        label="🔊 이 문장 듣기",
    )

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
# COOKING 뷰 (사용자용 Agent 느낌 핵심)
# ─────────────────────────────────────────────
def _render_cooking_view(slot, slot_index: int):
    st.subheader("지금은 **요리·식사 시간**이에요 🍽")
    _tts_button(
        "지금은 요리하고 밥을 먹는 시간이에요.",
        key=f"cook_intro_{slot_index}",
        label="🔊 지금이 어떤 시간인지 듣기",
    )

    guide = slot.get("guide_script", [])
    if guide:
        _render_stepper(guide, f"guide_cooking_{slot_index}", "지금 안내")

    menus = slot.get("menus") or slot.get("menu_candidates") or []
    if not menus:
        st.info(
            "아직 메뉴가 준비되지 않았어요.\n"
            "코디네이터에게 메뉴를 설정해 달라고 부탁해 주세요."
        )
        return

    select_key = f"selected_menu_{slot_index}"
    step_key = f"cook_step_{slot_index}"

    st.markdown("### 먹고 싶은 메뉴를 골라요")
    _tts_button(
        "먹고 싶은 메뉴를 골라요. 아래 사진과 버튼 중에서 하나를 골라 주세요.",
        key=f"cook_choose_{slot_index}",
        label="🔊 메뉴 고르는 방법 듣기",
    )

    cols = st.columns(len(menus))
    for i, menu in enumerate(menus):
        name = menu.get("name", "").strip()
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

            # 메뉴 설명 TTS
            if name:
                menu_desc_text = f"{name} 메뉴예요. 이 버튼을 누르면 이 메뉴를 선택합니다."
            else:
                menu_desc_text = "이 버튼을 누르면 이 메뉴를 선택합니다."

            _tts_button(
                menu_desc_text,
                key=f"cook_menu_tts_{slot_index}_{i}",
                label="🔊 이 메뉴 설명 듣기",
            )

            # 선택 버튼
            button_label = f"{emoji} {name}" if name else f"{emoji} 메뉴 선택"
            if st.button(button_label, key=f"menu_btn_{slot_index}_{i}"):
                print(
                    f"[DEBUG] cooking menu selected: "
                    f"slot_index={slot_index}, menu={name}"
                )
                st.session_state[select_key] = name
                st.session_state[step_key] = 0

    chosen = st.session_state.get(select_key)
    if not chosen:
        return

    # 레시피가 없어도 동작하도록 fallback
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
    steps = recipe.get("steps", [])

    st.markdown("---")
    st.markdown(f"## {recipe['name']} 준비하기")
    _tts_button(
        f"{recipe['name']}을 준비해 볼게요. 먼저 도구와 재료를 확인하고, 순서대로 따라가면 됩니다.",
        key=f"cook_recipe_intro_{slot_index}",
        label="🔊 준비 설명 듣기",
    )

    if tools:
        st.markdown("### 준비 도구")
        for t in tools:
            st.markdown(f"- {t}")
        _tts_button(
            "준비 도구는 " + " , ".join(tools) + " 입니다.",
            key=f"cook_tools_{slot_index}",
            label="🔊 도구 목록 듣기",
        )

    if ingredients:
        st.markdown("### 준비 재료")
        for ing in ingredients:
            st.markdown(f"- {ing}")
        _tts_button(
            "준비 재료는 " + " , ".join(ingredients) + " 입니다.",
            key=f"cook_ingredients_{slot_index}",
            label="🔊 재료 목록 듣기",
        )

    if not steps:
        st.warning("레시피 단계 정보가 없습니다.")
        return

    if step_key not in st.session_state:
        st.session_state[step_key] = 0

    idx = st.session_state[step_key]
    idx = max(0, min(idx, len(steps) - 1))

    st.markdown("---")
    st.markdown(f"### 만들기 단계 ({idx+1} / {len(steps)} 단계)")
    current_step = steps[idx]
    st.write(current_step)

    _tts_button(
        current_step,
        key=step_key + "_tts_btn",
        label="🔊 이 단계 듣기",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("처음부터", key=step_key + "_reset"):
            st.session_state[step_key] = 0
    with col2:
        if st.button("⬅ 이전 단계", disabled=(idx == 0), key=step_key + "_prev"):
            st.session_state[step_key] = max(0, idx - 1)
    with col3:
        if st.button("다음 단계 ➡", disabled=(idx == len(steps) - 1), key=step_key + "_next"):
            st.session_state[step_key] = min(len(steps) - 1, idx + 1)


# ─────────────────────────────────────────────
# HEALTH / NIGHT / MORNING / GENERAL (기존과 동일 구조)
# ─────────────────────────────────────────────
def _render_health_view(slot, slot_index: int):
    st.subheader("지금은 **운동 / 건강 시간**이에요 💪")
    _tts_button(
        "지금은 운동하고 몸을 움직이는 시간이에요.",
        key=f"health_intro_{slot_index}",
        label="🔊 지금이 어떤 시간인지 듣기",
    )

    guide = slot.get("guide_script", [])
    if guide:
        _render_stepper(guide, f"guide_health_{slot_index}", "지금 안내")

    modes = slot.get("health_modes") or [
        {"id": "sit", "name": "앉아서 하는 운동"},
        {"id": "stand", "name": "서서 하는 운동"},
    ]

    select_key = f"selected_health_{slot_index}"
    step_key = f"health_step_{slot_index}"

    st.markdown("### 어떤 운동을 할까요?")
    _tts_button(
        "어떤 운동을 할지 고르세요. 아래 버튼 중에서 하나를 선택하면, 그 운동 방법을 알려줄게요.",
        key=f"health_choose_{slot_index}",
        label="🔊 운동 고르는 방법 듣기",
    )

    cols = st.columns(len(modes))
    for i, mode in enumerate(modes):
        with cols[i]:
            _tts_button(
                f"{mode['name']}을 선택하는 버튼입니다.",
                key=f"health_mode_tts_{slot_index}_{i}",
                label="🔊 이 운동 설명 듣기",
            )
            if st.button(mode["name"], key=f"health_btn_{slot_index}_{i}"):
                st.session_state[select_key] = mode["id"]
                st.session_state[step_key] = 0

    chosen = st.session_state.get(select_key)
    if not chosen:
        return

    routine = get_health_routine(chosen)
    if not routine:
        st.warning("이 운동에 대한 설명이 아직 준비되지 않았어요.")
        return

    steps = routine.get("steps", [])
    if not steps:
        st.warning("운동 단계 정보가 없습니다.")
        return

    _render_stepper(steps, step_key, routine["name"])


def _render_night_view(slot, slot_index: int):
    st.subheader("지금은 **하루 마무리 시간**이에요 🌙")
    _tts_button(
        "지금은 오늘 하루를 마무리하는 시간이에요.",
        key=f"night_intro_{slot_index}",
        label="🔊 지금이 어떤 시간인지 듣기",
    )
    guide = slot.get("guide_script", [])
    _render_stepper(guide, f"guide_night_{slot_index}", "마무리 안내")


def _render_morning_view(slot, slot_index: int):
    st.subheader("지금은 **아침 인사 시간**이에요 ☀️")
    _tts_button(
        "지금은 아침 인사 시간이에요.",
        key=f"morning_intro_{slot_index}",
        label="🔊 지금이 어떤 시간인지 듣기",
    )
    guide = slot.get("guide_script", [])
    _render_stepper(guide, f"guide_morning_{slot_index}", "아침 안내")


def _render_general_view(slot, slot_index: int):
    st.subheader("지금은 **일반 활동 시간**이에요.")
    task = slot.get("task", "")
    st.markdown(f"### 활동: {task}")
    _tts_button(
        f"지금은 일반 활동 시간이에요. 이번 활동은 {task} 입니다.",
        key=f"general_intro_{slot_index}",
        label="🔊 활동 설명 듣기",
    )
    guide = slot.get("guide_script", [])
    _render_stepper(guide, f"guide_general_{slot_index}", "활동 안내")


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
# 자동 TTS 상호작용 로직 (간단 버전)
# ─────────────────────────────────────────────
def _auto_tts_logic(
    now: datetime, date_str: str, active: Optional[dict], next_item: Optional[dict]
):
    try:
        schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        schedule_date = now.date()

    if schedule_date != now.date():
        print("[DEBUG] [_auto_tts_logic] schedule date != today, skip auto TTS")
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

    # 첫 진입
    if not greeting_done:
        if active:
            slot_text = _build_slot_tts_text(active)
            full = f"{base_greeting_text} {slot_text}"
        else:
            full = base_greeting_text

        _play_tts_auto(full)
        st.session_state["greeting_tts_done"] = True
        st.session_state["last_tts_slot_key"] = current_slot_key
        return

    # 슬롯 변경 시
    if active and current_slot_key != last_slot_key:
        slot_text = _build_slot_tts_text(active)
        _play_tts_auto(slot_text)
        st.session_state["last_tts_slot_key"] = current_slot_key
        return

    # 다음 활동 준비 알림
    if next_item and next_item.get("time"):
        try:
            slot_time = datetime.strptime(next_item["time"], "%H:%M").time()
            slot_dt = datetime.combine(schedule_date, slot_time)
            diff_min = (slot_dt - now).total_seconds() / 60.0
        except Exception:
            diff_min = None

        if diff_min is not None and 0 < diff_min <= PRE_NOTICE_MINUTES:
            if next_slot_key and next_slot_key != last_pre_notice_key:
                pre_text = _build_slot_tts_text(next_item)
                pre_text = (
                    f"{next_item['time']}에 시작하는 활동을 준비해 볼까요? {pre_text}"
                )
                _play_tts_auto(pre_text)
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
        st.warning(
            "스케줄이 비어 있습니다. 코디네이터에게 일정을 확인해 달라고 부탁해 주세요."
        )
        return

    now = datetime.now()
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
                st.write("곧 시작될 첫 활동:")
                st.write(
                    f"- {next_item.get('time')} · "
                    f"[{next_item.get('type')}] {next_item.get('task')}"
                )
        else:
            idx = _get_slot_index(schedule, active)
            t = active.get("type", "GENERAL")
            task = active.get("task", "")

            if t == "MORNING_BRIEFING":
                header_text = "지금은 아침 준비 시간이에요 ☀️"
            elif t == "COOKING":
                header_text = "지금은 맛있는 식사 시간이에요 🍽"
            elif t == "HEALTH":
                header_text = "지금은 내 몸을 돌보는 시간이에요 💪"
            elif t == "NIGHT_WRAPUP":
                header_text = "지금은 오늘을 마무리하는 시간이에요 🌙"
            else:
                header_text = "지금은 활동 시간이에요 🙂"

            st.header(header_text)
            st.markdown(f"#### 오늘 할 일: **{task}**")

            today_task_text = f"{header_text} 오늘 할 일은 {task} 입니다."
            _tts_button(
                today_task_text,
                key=f"slot_task_tts_{idx}",
                label="🔊 오늘 할 일 설명 듣기",
            )

            if t == "COOKING":
                _render_cooking_view(active, idx)
            elif t == "HEALTH":
                _render_health_view(active, idx)
            elif t == "MORNING_BRIEFING":
                _render_morning_view(active, idx)
            elif t == "NIGHT_WRAPUP":
                _render_night_view(active, idx)
            else:
                _render_general_view(active, idx)

    with col_side:
        st.markdown("### ⏭ 다음 활동")
        if next_item:
            st.markdown(
                f"**{next_item.get('time')}** · "
                f"[{next_item.get('type')}] {next_item.get('task')}"
            )
        else:
            st.write("오늘 일정은 모두 끝났어요.\n편안하게 쉬어요. 😌")

        st.markdown("---")
        st.markdown("### 🗓 오늘 타임라인")

        for item in annotated:
            label = (
                f"{item.get('time', '??:??')} · "
                f"[{item.get('type')}] {item.get('task')}"
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


if __name__ == "__main__":
    user_page()
