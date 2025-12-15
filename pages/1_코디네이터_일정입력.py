# pages/1_코디네이터_일정입력.py
# -*- coding: utf-8 -*-

import os
import json
import re
import uuid
from datetime import date
from typing import Dict, List

import streamlit as st

try:
    from streamlit_clickable_images import clickable_images
except ImportError:
    clickable_images = None

from utils.topbar import render_topbar
from utils.schedule_ai import generate_schedule_from_text
from utils.runtime import parse_hhmm_to_time
from utils.recipes import get_all_recipe_names, suggest_recipes_from_text
from utils.image_ai import search_and_filter_food_images, download_image_to_assets
from utils.youtube_ai import (
    search_cooking_videos_for_dd_raw,
    search_exercise_videos_for_dd_raw,
    search_clothing_videos_for_dd_raw,
)

SCHEDULE_STATE_KEY = "hibuddy_schedule"


# -------------------------------
# 노인층 UX용: 타입 한글만 노출
# -------------------------------
TYPE_LABEL = {
    "GENERAL": "일정(기타)",
    "ROUTINE": "준비/위생",
    "MEAL": "식사",
    "COOKING": "요리",
    "HEALTH": "운동",
    "CLOTHING": "옷 입기",
    "HOBBY": "취미/여가",
}
LABEL_TYPE = {v: k for k, v in TYPE_LABEL.items()}


def to_label(type_code: str) -> str:
    t = (type_code or "").replace("[", "").replace("]", "").strip().upper()
    return TYPE_LABEL.get(t, "일정(기타)")


def to_code(type_label: str) -> str:
    return LABEL_TYPE.get(type_label, "GENERAL")


def _clean_task(text: str) -> str:
    """[MORNING_BRIEFING] 같은 내부 태그가 task에 섞여도 화면에 안 보이게 제거"""
    s = (text or "").strip()
    s = re.sub(r"\[[A-Z0-9_]+\]\s*", "", s)
    return s


# ---- 내부 상태 초기화 ----
def _init_state():
    if SCHEDULE_STATE_KEY not in st.session_state:
        st.session_state[SCHEDULE_STATE_KEY] = []


# ---- 일정 파일 저장 ----
def _save_schedule_to_file(schedule: List[Dict]) -> str:
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", "schedule_today.json")
    payload = {"date": date.today().isoformat(), "schedule": schedule}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


# ---- 일정 항목 id 보장 ----
def _ensure_item_ids(schedule: List[Dict]) -> List[Dict]:
    for it in schedule:
        if not it.get("id"):
            it["id"] = uuid.uuid4().hex
    return schedule


def _find_index_by_id(schedule: List[Dict], item_id: str) -> int:
    for i, it in enumerate(schedule):
        if it.get("id") == item_id:
            return i
    return -1


# ---- 카테고리 가드레일(규칙 기반 보정) ----
def _apply_type_guardrails(schedule: List[Dict]) -> List[Dict]:
    routine_kw = ["샤워", "세수", "양치", "씻기", "머리감기", "위생", "준비"]
    clothing_kw = ["옷", "옷 입기", "갈아입", "외출 준비"]
    meal_kw = ["식사", "밥", "아침", "점심", "저녁", "간식", "먹기", "먹어요", "먹자"]
    cooking_intent_kw = ["요리", "만들", "끓이", "레시피", "조리", "해먹", "직접 만들"]
    health_kw = ["운동", "체조", "스트레칭", "산책", "걷기", "헬스"]
    hobby_kw = ["여가", "휴식", "드라마", "유튜브", "영상", "보기", "시청", "취미"]

    for it in schedule:
        task = _clean_task(it.get("task") or "")
        t = (it.get("type") or "").strip().upper()

        # 옷 입기 우선
        if any(k in task for k in clothing_kw):
            it["type"] = "CLOTHING"
            continue

        # 준비/위생
        if any(k in task for k in routine_kw):
            it["type"] = "ROUTINE"
            continue

        # 운동
        if any(k in task for k in health_kw):
            it["type"] = "HEALTH"
            continue

        # 취미/여가
        if any(k in task for k in hobby_kw):
            it["type"] = "HOBBY"
            continue

        # 식사 vs 요리 분리
        if any(k in task for k in meal_kw):
            has_cooking = any(k in task for k in cooking_intent_kw)
            it["type"] = "COOKING" if has_cooking else "MEAL"
            continue

        # 기본
        if not it.get("type"):
            it["type"] = "GENERAL"
        else:
            # 혹시 이상한 타입이면 GENERAL로
            if t not in TYPE_LABEL:
                it["type"] = "GENERAL"

    return schedule


# ---- 활동 문장에서 음식 이름 뽑기 ----
def _extract_menu_names_from_task(task: str) -> List[str]:
    task = _clean_task(task)
    if not task:
        return []

    names = suggest_recipes_from_text(task) or []
    if names:
        return names

    rough = re.split(r"[,/]| 또는 | 혹은 ", task)
    cleaned = []
    for part in rough:
        name = part.strip()
        if not name:
            continue

        for suffix in ["중 하나 먹기", "먹기", "먹어요", "하기", "훈련", "연습"]:
            if name.endswith(suffix):
                name = name[: -len(suffix)].strip()

        if len(name) > 10 and " " in name:
            name = name.split()[0]

        if name and name not in cleaned:
            cleaned.append(name)

    return cleaned


# ---- COOKING 슬롯에 자동으로 메뉴 후보 붙이기 ----
def _auto_attach_cooking_candidates(schedule: List[Dict]) -> List[Dict]:
    for item in schedule:
        if item.get("type") != "COOKING":
            continue
        if item.get("menus"):
            continue

        task_text = item.get("task", "")
        names = _extract_menu_names_from_task(task_text)

        if not names and task_text:
            names = [_clean_task(task_text)]

        if not names:
            continue

        item["menus"] = [
            {"name": name, "image": "assets/images/default_food.png", "video_url": ""}
            for name in names
        ]
    return schedule


# ---- 메인 화면 ----
def coordinator_page():
    _init_state()
    render_topbar()

    st.markdown("# 🧑‍🏫 코디네이터 일정 입력")
    st.caption("시간과 할 일만 적어도 됩니다. 아래에서 쉽게 고칠 수 있어요.")

    example_text = (
        "08:00 오늘 일정 간단 안내\n"
        "10:00 옷 입기 연습\n"
        "12:00 점심 먹기\n"
        "15:00 쉬는 시간\n"
        "18:00 운동하기\n"
        "19:00 영상 보기\n"
        "22:00 하루 마무리 인사"
    )

    raw = st.text_area("오늘 해야 할 일", value=example_text, height=200)

    if st.button("✅ 일정 만들기", type="primary"):
        with st.spinner("일정을 만들고 있습니다..."):
            schedule = generate_schedule_from_text(raw)
            schedule = _ensure_item_ids(schedule)
            schedule = _apply_type_guardrails(schedule)
            schedule = _auto_attach_cooking_candidates(schedule)
        st.session_state[SCHEDULE_STATE_KEY] = schedule
        st.success("완료! 아래에서 확인하고 고칠 수 있어요.")

    schedule: List[Dict] = st.session_state.get(SCHEDULE_STATE_KEY, [])
    schedule = _ensure_item_ids(schedule)
    st.session_state[SCHEDULE_STATE_KEY] = schedule

    schedule_view = sorted(
        schedule,
        key=lambda it: parse_hhmm_to_time(it.get("time", "00:00"))
    )

    st.markdown("---")
    st.markdown("## 2. 오늘의 할 일")

    if not schedule_view:
        st.info("위에서 ‘✅ 일정 만들기’를 눌러주세요.")
        return

    # ✅ 여기서 타입 코드([GENERAL] 등) 완전 숨김
    for item in schedule_view:
        time_str = item.get("time", "??:??")
        task = _clean_task(item.get("task", ""))
        st.markdown(f"- **{time_str}** · {task}")

    st.markdown("---")
    st.markdown("## 3. 일정 고치기 (눌러서 펼치기)")

    all_recipe_names = get_all_recipe_names()

    for item in schedule_view:
        item_id = item.get("id")
        if not item_id:
            continue

        orig_idx = _find_index_by_id(st.session_state[SCHEDULE_STATE_KEY], item_id)
        if orig_idx < 0:
            continue

        time_str = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("time", "??:??")
        type_code = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("type", "GENERAL")
        task = _clean_task(st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("task", ""))

        # ✅ expander 제목도 영문 코드 안 보이게: 한글 라벨만
        with st.expander(f"⏰ {time_str} · {to_label(type_code)} · {task}", expanded=False):
            st.markdown("### 1) 시간 / 종류 / 할 일")

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                new_time = st.text_input("시간(HH:MM)", value=time_str, key=f"time_{item_id}")

            with col2:
                # 노인층용: 한글만, 선택지 최소
                label_options = ["일정(기타)", "준비/위생", "식사", "요리", "운동", "옷 입기", "취미/여가"]
                current_label = to_label(type_code)
                new_label = st.selectbox(
                    "종류(한글)",
                    options=label_options,
                    index=label_options.index(current_label) if current_label in label_options else 0,
                    key=f"type_{item_id}",
                )
                new_type = to_code(new_label)

            with col3:
                new_task = st.text_input("할 일", value=task, key=f"task_{item_id}")

            b1, b2, b3, b4 = st.columns([1, 1, 1, 1])

            with b1:
                if st.button("✅ 저장하기", type="primary", key=f"save_{item_id}"):
                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["time"] = (new_time.strip() or "00:00")
                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["task"] = new_task.strip()
                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["type"] = new_type

                    st.session_state[SCHEDULE_STATE_KEY] = _apply_type_guardrails(st.session_state[SCHEDULE_STATE_KEY])
                    st.session_state[SCHEDULE_STATE_KEY] = _auto_attach_cooking_candidates(st.session_state[SCHEDULE_STATE_KEY])

                    st.success("저장했습니다.")
                    st.rerun()

            with b2:
                if st.button("⬆️ 위로", key=f"up_{item_id}"):
                    s = st.session_state[SCHEDULE_STATE_KEY]
                    if orig_idx > 0:
                        s[orig_idx - 1], s[orig_idx] = s[orig_idx], s[orig_idx - 1]
                        st.session_state[SCHEDULE_STATE_KEY] = s
                        st.rerun()

            with b3:
                if st.button("⬇️ 아래로", key=f"down_{item_id}"):
                    s = st.session_state[SCHEDULE_STATE_KEY]
                    if orig_idx < len(s) - 1:
                        s[orig_idx + 1], s[orig_idx] = s[orig_idx], s[orig_idx + 1]
                        st.session_state[SCHEDULE_STATE_KEY] = s
                        st.rerun()

            with b4:
                if st.button("🗑️ 삭제하기", key=f"del_{item_id}"):
                    s = st.session_state[SCHEDULE_STATE_KEY]
                    s.pop(orig_idx)
                    st.session_state[SCHEDULE_STATE_KEY] = s
                    st.success("삭제했습니다.")
                    st.rerun()

            st.markdown("---")

            # 타입별 추가 설정: 노인층은 "필수만" 노출
            type_code_now = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("type", "GENERAL")

            # ---------------- COOKING ----------------
            if type_code_now == "COOKING":
                st.markdown("### 2) 요리 설정 (필요할 때만)")

                current_menus = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("menus") or []
                if not current_menus:
                    names = _extract_menu_names_from_task(new_task) or [new_task]
                    current_menus = [{"name": n, "image": "assets/images/default_food.png", "video_url": ""} for n in names]
                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["menus"] = current_menus

                st.caption("메뉴 이름만 적어도 됩니다. 영상은 선택입니다.")
                menu_names = [m.get("name", "") for m in current_menus if m.get("name")]
                menu_text = st.text_input("메뉴(쉼표로 여러 개)", value=", ".join(menu_names), key=f"menu_{item_id}")

                if st.button("✅ 메뉴 저장", type="primary", key=f"save_menu_{item_id}"):
                    names = [n.strip() for n in menu_text.split(",") if n.strip()]
                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["menus"] = [
                        {"name": n, "image": "assets/images/default_food.png", "video_url": ""} for n in names
                    ]
                    st.success("메뉴 저장 완료")
                    st.rerun()

                with st.expander("참고: 등록된 요리 목록 보기", expanded=False):
                    st.write(", ".join(all_recipe_names))

                with st.expander("옵션: 요리 영상(필요할 때만)", expanded=False):
                    menus = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("menus", [])
                    for m_idx, menu in enumerate(menus):
                        menu_name = menu.get("name", f"메뉴 {m_idx+1}")
                        st.markdown(f"#### 🍳 {menu_name}")

                        default_q = menu.get("video_query", f"{menu_name} 만들기")
                        q = st.text_input("유튜브 검색어", value=default_q, key=f"cook_q_{item_id}_{m_idx}")
                        st.session_state[SCHEDULE_STATE_KEY][orig_idx]["menus"][m_idx]["video_query"] = q

                        if st.button("▶️ 영상 추천받기", type="primary", key=f"cook_rec_{item_id}_{m_idx}"):
                            with st.spinner("영상을 찾고 있습니다..."):
                                try:
                                    yt_results = search_cooking_videos_for_dd_raw(q, max_results=4)
                                except Exception as e:
                                    st.error(f"검색 오류: {e}")
                                    yt_results = []
                                st.session_state[f"cook_res_{item_id}_{m_idx}"] = yt_results

                        yt_results = st.session_state.get(f"cook_res_{item_id}_{m_idx}", [])
                        if yt_results:
                            for v_idx, v in enumerate(yt_results):
                                st.markdown(f"- {v.get('title', '(제목 없음)')}")
                                if st.button("✅ 이 영상 사용", type="primary", key=f"use_cook_{item_id}_{m_idx}_{v_idx}"):
                                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["menus"][m_idx]["video_url"] = v["url"]
                                    st.success("적용했습니다.")
                                    st.rerun()

            # ---------------- HEALTH ----------------
            elif type_code_now == "HEALTH":
                st.markdown("### 2) 운동 영상")
                st.caption("복잡한 선택은 없애고, 영상만 고를 수 있게 했습니다.")

                default_q = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get(
                    "video_query_health",
                    f"{new_task} 따라하기" if new_task else "쉬운 운동 따라하기",
                )
                q = st.text_input("유튜브 검색어", value=default_q, key=f"health_q_{item_id}")
                st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_query_health"] = q

                if st.button("▶️ 영상 추천받기", type="primary", key=f"health_rec_{item_id}"):
                    with st.spinner("영상을 찾고 있습니다..."):
                        try:
                            yt_results = search_exercise_videos_for_dd_raw(q, max_results=4)
                        except Exception as e:
                            st.error(f"검색 오류: {e}")
                            yt_results = []
                        st.session_state[f"health_res_{item_id}"] = yt_results

                yt_results = st.session_state.get(f"health_res_{item_id}", [])
                if yt_results:
                    for v_idx, v in enumerate(yt_results):
                        st.markdown(f"- {v.get('title', '(제목 없음)')}")
                        if st.button("✅ 이 영상 사용", type="primary", key=f"use_health_{item_id}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_url"] = v["url"]
                            st.success("적용했습니다.")
                            st.rerun()

            # ---------------- CLOTHING ----------------
            elif type_code_now == "CLOTHING":
                st.markdown("### 2) 옷 입기 영상")

                default_q = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get(
                    "video_query_clothing",
                    f"{new_task} 연습" if new_task else "옷 입기 연습",
                )
                q = st.text_input("유튜브 검색어", value=default_q, key=f"cloth_q_{item_id}")
                st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_query_clothing"] = q

                if st.button("▶️ 영상 추천받기", type="primary", key=f"cloth_rec_{item_id}"):
                    with st.spinner("관련 영상을 찾고 있습니다..."):
                        try:
                            yt_results = search_clothing_videos_for_dd_raw(q, max_results=4)
                        except Exception as e:
                            st.error(f"검색 오류: {e}")
                            yt_results = []
                        st.session_state[f"cloth_res_{item_id}"] = yt_results

                yt_results = st.session_state.get(f"cloth_res_{item_id}", [])
                if yt_results:
                    for v_idx, v in enumerate(yt_results):
                        st.markdown(f"- {v.get('title', '(제목 없음)')}")
                        if st.button("✅ 이 영상 사용", type="primary", key=f"use_cloth_{item_id}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_url"] = v["url"]
                            st.success("적용했습니다.")
                            st.rerun()

            # ---------------- HOBBY ----------------
            elif type_code_now == "HOBBY":
                st.markdown("### 2) 취미/여가 영상")
                st.caption("드론/스포츠 같은 복잡한 선택은 빼고, 영상만 추천받습니다.")

                default_q = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get(
                    "video_query_hobby",
                    f"{new_task} 영상" if new_task else "재미있는 영상",
                )
                q = st.text_input("유튜브 검색어", value=default_q, key=f"hobby_q_{item_id}")
                st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_query_hobby"] = q

                if st.button("▶️ 영상 추천받기", type="primary", key=f"hobby_rec_{item_id}"):
                    with st.spinner("영상을 찾고 있습니다..."):
                        try:
                            # 취미용 전용 함수가 없으면 일단 exercise 검색 함수로 fallback(검색어 기반이라 동작은 함)
                            yt_results = search_exercise_videos_for_dd_raw(q, max_results=4)
                        except Exception as e:
                            st.error(f"검색 오류: {e}")
                            yt_results = []
                        st.session_state[f"hobby_res_{item_id}"] = yt_results

                yt_results = st.session_state.get(f"hobby_res_{item_id}", [])
                if yt_results:
                    for v_idx, v in enumerate(yt_results):
                        st.markdown(f"- {v.get('title', '(제목 없음)')}")
                        if st.button("✅ 이 영상 사용", type="primary", key=f"use_hobby_{item_id}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_url"] = v["url"]
                            st.success("적용했습니다.")
                            st.rerun()

            else:
                st.caption("추가 설정이 필요 없습니다.")

    st.markdown("---")
    st.markdown("## 4. 저장")

    if st.button("✅ 오늘 일정 저장하기", type="primary"):
        try:
            path = _save_schedule_to_file(st.session_state[SCHEDULE_STATE_KEY])
            st.success(f"저장 완료! 저장 위치: {path}")
        except Exception as e:
            st.error(f"저장 중 오류: {e}")


if __name__ == "__main__":
    coordinator_page()
