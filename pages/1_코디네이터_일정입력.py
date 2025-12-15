# pages/1_코디네이터_오늘_일정_설계.py
# -*- coding: utf-8 -*-

import os
import json
import re
import uuid
from copy import deepcopy
from datetime import date
from typing import Dict, List, Optional

import streamlit as st

try:
    # 이미지 자체를 클릭해서 선택하기 위해 사용
    from streamlit_clickable_images import clickable_images
except ImportError:
    clickable_images = None

from utils.topbar import render_topbar
from utils.schedule_ai import generate_schedule_from_text
from utils.runtime import parse_hhmm_to_time
from utils.recipes import (
    get_all_recipe_names,
    suggest_recipes_from_text,
    get_health_modes,
)
from utils.image_ai import search_and_filter_food_images, download_image_to_assets
from utils.youtube_ai import (
    search_cooking_videos_for_dd_raw,
    search_exercise_videos_for_dd_raw,
    search_clothing_videos_for_dd_raw,
)

# (옵션) 만약 utils.youtube_ai에 취미 전용 함수가 있으면 사용
try:
    from utils.youtube_ai import search_hobby_videos_for_dd_raw  # type: ignore
except Exception:
    search_hobby_videos_for_dd_raw = None  # fallback

SCHEDULE_STATE_KEY = "hibuddy_schedule"
USER_PROFILE_KEY = "hibuddy_user_profile"


# ---- 내부 상태 초기화 ----
def _init_state():
    if SCHEDULE_STATE_KEY not in st.session_state:
        st.session_state[SCHEDULE_STATE_KEY] = []
    if USER_PROFILE_KEY not in st.session_state:
        st.session_state[USER_PROFILE_KEY] = "기본"


# ---- 일정 파일 저장 ----
def _save_schedule_to_file(schedule: List[Dict]) -> str:
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", "schedule_today.json")
    payload = {
        "date": date.today().isoformat(),
        "schedule": schedule,
    }
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


# ---- 카테고리 1차 가드레일(규칙 기반 보정) ----
def _apply_type_guardrails(schedule: List[Dict]) -> List[Dict]:
    """
    1차 규칙 기반 보정(LLM 붙이기 전 안전장치)
    - 샤워/세수/양치 => ROUTINE
    - 식사/아침/점심/저녁/간식 => MEAL (요리 의도가 없으면)
    - COOKING은 '요리/만들기/끓이기/레시피' 등 의도 키워드가 있을 때만
    - 여가/드라마/드론/스포츠/영상/유튜브 => HOBBY
    """
    routine_kw = ["샤워", "세수", "양치", "씻기", "머리감기", "위생"]
    meal_kw = ["식사", "밥", "아침", "점심", "저녁", "간식", "먹기", "먹어요", "먹자"]
    cooking_intent_kw = ["요리", "만들", "끓이", "레시피", "조리", "준비해", "해먹"]
    hobby_kw = ["여가", "휴식", "드라마", "드론", "스포츠", "유튜브", "영상", "보기", "시청"]

    for it in schedule:
        task = (it.get("task") or "").strip()
        t = (it.get("type") or "").strip()

        # ROUTINE 강제
        if any(k in task for k in routine_kw):
            it["type"] = "ROUTINE"
            continue

        # HOBBY 강제(여가/영상)
        # 단, "운동 영상 보기" 같이 HEALTH로 가야 하는 케이스는 사용자가 type을 직접 수정 가능.
        if any(k in task for k in hobby_kw) and not any(k in task for k in ["운동", "스트레칭", "재활"]):
            it["type"] = "HOBBY"
            continue

        # MEAL/COOKING 분리
        if any(k in task for k in meal_kw):
            has_cooking_intent = any(k in task for k in cooking_intent_kw)
            it["type"] = "COOKING" if has_cooking_intent else "MEAL"
            continue

        # COOKING인데 의도 없으면 MEAL로 강등(예: '점심 먹기'가 COOKING으로 들어온 케이스)
        if t == "COOKING":
            has_cooking_intent = any(k in task for k in cooking_intent_kw)
            if not has_cooking_intent:
                it["type"] = "MEAL"

    return schedule


# ---- 활동 문장에서 음식 이름 뽑기 ----
def _extract_menu_names_from_task(task: str) -> List[str]:
    """
    예: "라면 또는 카레 중 하나 먹기"
    → ["라면", "카레"] 이렇게 음식 이름만 뽑아냅니다.
    """
    task = (task or "").strip()
    if not task:
        return []

    # 1차: AI 기반 추출
    names = suggest_recipes_from_text(task) or []
    if names:
        return names

    # 2차: 간단 규칙 기반 추출
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
    """
    요리 시간이 있을 경우,
    해당 활동 문장에서 음식 이름을 찾아 자동으로 메뉴 후보를 채워줍니다.
    """
    for item in schedule:
        if item.get("type") != "COOKING":
            continue
        if item.get("menus"):
            continue

        task_text = item.get("task", "")
        names = _extract_menu_names_from_task(task_text)

        if not names and task_text:
            names = [task_text]

        if not names:
            continue

        item["menus"] = [
            {
                "name": name,
                "image": "assets/images/default_food.png",
                "video_url": "",
            }
            for name in names
        ]
    return schedule


# ---- HOBBY 유튜브 검색 (전용 함수가 없으면 exercise search로 fallback) ----
def _search_hobby_videos(query: str, max_results: int = 4) -> List[Dict]:
    if search_hobby_videos_for_dd_raw is not None:
        return search_hobby_videos_for_dd_raw(query, max_results=max_results)  # type: ignore
    # fallback: raw 유튜브 검색을 대체로 수행(함수명은 exercise지만 검색 결과는 일반 영상도 잘 나옴)
    return search_exercise_videos_for_dd_raw(query, max_results=max_results)


# ---- 메인 화면 ----
def coordinator_page():
    _init_state()
    render_topbar()

    st.header("1. 오늘 일정 만들기 (코디네이터용)")

    # ---- 사용자 프로필(선호 기반 기본 검색어/추천용) ----
    st.session_state[USER_PROFILE_KEY] = st.selectbox(
        "대상 사용자 선택",
        options=["기본", "미화님", "용화님"],
        index=["기본", "미화님", "용화님"].index(st.session_state.get(USER_PROFILE_KEY, "기본")),
    )

    example_text = (
        "아침 8시에 오늘 일정 간단 안내,\n"
        "10시에 옷 입기 연습,\n"
        "12시에 점심 먹기,\n"
        "15시에 쉬는 시간,\n"
        "18시에 앉아서 하는 운동,\n"
        "19시에 드라마 보기,\n"
        "22시에 하루 마무리 인사"
    )

    raw = st.text_area(
        "오늘 해야 할 일들을 편하게 적어 주세요.\n(시간과 활동을 자연스럽게 써주면 됩니다.)",
        value=example_text,
        height=200,
    )

    if st.button("일정 자동 만들기", type="primary"):
        with st.spinner("입력하신 내용을 이해하기 쉬운 일정표로 바꾸는 중입니다..."):
            schedule = generate_schedule_from_text(raw)
            schedule = _ensure_item_ids(schedule)
            schedule = _apply_type_guardrails(schedule)
            schedule = _auto_attach_cooking_candidates(schedule)

        st.session_state[SCHEDULE_STATE_KEY] = schedule
        st.success("일정이 생성되었습니다. 아래에서 활동별로 수정/삭제/이동이 가능합니다.")

    # ---- 세션 원본은 건드리지 않고 view만 정렬 ----
    schedule: List[Dict] = st.session_state.get(SCHEDULE_STATE_KEY, [])
    schedule = _ensure_item_ids(schedule)
    st.session_state[SCHEDULE_STATE_KEY] = schedule

    schedule_view = sorted(
        schedule,
        key=lambda it: parse_hhmm_to_time(it.get("time", "00:00"))
    )

    st.markdown("---")
    st.header("2. 오늘의 할 일")

    if not schedule_view:
        st.info("먼저 위에서 일정 내용을 입력한 뒤 '일정 자동 만들기' 버튼을 눌러주세요.")
        return

    for item in schedule_view:
        st.markdown(
            f"- **{item.get('time', '??:??')}** · [{item.get('type', '')}] {item.get('task', '')}"
        )

    st.markdown("---")
    st.header("3. 활동별 수정/설정")

    all_recipe_names = get_all_recipe_names()
    all_health_modes = get_health_modes()
    health_name_map = {m["name"]: m for m in all_health_modes}

    # ---- 활동별 편집 화면 ----
    for view_idx, item in enumerate(schedule_view):
        item_id = item.get("id")
        if not item_id:
            continue

        # 원본 인덱스 찾기(세션 원본 수정은 여기로만)
        orig_idx = _find_index_by_id(st.session_state[SCHEDULE_STATE_KEY], item_id)
        if orig_idx < 0:
            st.error("일정 항목을 찾을 수 없습니다. (id 매칭 실패)")
            continue

        time_str = item.get("time", "??:??")
        type_ = item.get("type", "")
        task = item.get("task", "")

        with st.expander(
            f"[{time_str}] {task} (활동 종류: {type_})",
            expanded=(type_ in ["COOKING", "HEALTH", "CLOTHING", "HOBBY", "MEAL", "ROUTINE"]),
        ):
            # ---------------- 공통: 항목 단위 수정/이동/삭제 ----------------
            st.markdown("#### 일정 항목 편집(최소 필수)")

            colA, colB, colC = st.columns([1, 1, 2])
            with colA:
                new_time = st.text_input(
                    "시간(HH:MM)",
                    value=st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("time", "00:00"),
                    key=f"edit_time_{item_id}",
                )
            with colB:
                type_options = ["TIMELINE", "ROUTINE", "MEAL", "COOKING", "HEALTH", "CLOTHING", "HOBBY", "GENERAL"]
                current_type = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("type", "GENERAL")
                new_type = st.selectbox(
                    "종류",
                    options=type_options,
                    index=type_options.index(current_type) if current_type in type_options else type_options.index("GENERAL"),
                    key=f"edit_type_{item_id}",
                )
            with colC:
                new_task = st.text_input(
                    "할 일",
                    value=st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("task", ""),
                    key=f"edit_task_{item_id}",
                )

            colD, colE, colF, colG = st.columns([1, 1, 1, 1])
            with colD:
                if st.button("수정 저장", key=f"save_{item_id}"):
                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["time"] = (new_time.strip() or "00:00")
                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["task"] = new_task.strip()
                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["type"] = new_type

                    # 저장 직후 가드레일 재적용 + 요리 후보 자동부착
                    st.session_state[SCHEDULE_STATE_KEY] = _apply_type_guardrails(st.session_state[SCHEDULE_STATE_KEY])
                    st.session_state[SCHEDULE_STATE_KEY] = _auto_attach_cooking_candidates(st.session_state[SCHEDULE_STATE_KEY])

                    st.success("수정이 저장되었습니다.")
                    st.rerun()

            with colE:
                if st.button("위로 이동", key=f"up_{item_id}"):
                    s = st.session_state[SCHEDULE_STATE_KEY]
                    if orig_idx > 0:
                        s[orig_idx - 1], s[orig_idx] = s[orig_idx], s[orig_idx - 1]
                        st.session_state[SCHEDULE_STATE_KEY] = s
                        st.rerun()

            with colF:
                if st.button("아래로 이동", key=f"down_{item_id}"):
                    s = st.session_state[SCHEDULE_STATE_KEY]
                    if orig_idx < len(s) - 1:
                        s[orig_idx + 1], s[orig_idx] = s[orig_idx], s[orig_idx + 1]
                        st.session_state[SCHEDULE_STATE_KEY] = s
                        st.rerun()

            with colG:
                if st.button("삭제", key=f"del_{item_id}"):
                    s = st.session_state[SCHEDULE_STATE_KEY]
                    s.pop(orig_idx)
                    st.session_state[SCHEDULE_STATE_KEY] = s
                    st.success("삭제되었습니다.")
                    st.rerun()

            st.markdown("---")

            # 가이드 스크립트 표시
            guide_lines = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("guide_script", []) or []
            if guide_lines:
                st.write("**사용자에게 보여줄 안내 문장(guide_script)**")
                for line in guide_lines:
                    st.markdown(f"- {line}")

            # ---------------- MEAL ----------------
            if new_type == "MEAL" or type_ == "MEAL":
                st.markdown("#### 식사(일반) 활동")
                st.caption("요리 기능을 쓰지 않는 일반 식사입니다. 필요하면 할 일 문장만 깔끔히 적어주세요.")
                # (원하면 여기서도 유튜브 '식사 예절/간단 안내' 같은 HOBBY 스타일 추천을 붙일 수 있음)

            # ---------------- ROUTINE ----------------
            elif new_type == "ROUTINE" or type_ == "ROUTINE":
                st.markdown("#### 루틴(위생/준비) 활동")
                st.caption("샤워/세수/양치 등은 ROUTINE으로 분리합니다. 영상이 필요하면 아래에서 추가하세요.")

                yt_key = f"yt_routine_{item_id}"
                default_query = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get(
                    "video_query_routine",
                    f"발달장애인 쉬운 {new_task} 따라하기" if new_task else "발달장애인 쉬운 루틴 따라하기",
                )
                routine_query = st.text_input(
                    "루틴 영상 유튜브 검색어",
                    value=default_query,
                    key=f"yt_routine_query_{item_id}",
                )
                st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_query_routine"] = routine_query

                if st.button("루틴 영상 추천 받기", key=f"search_yt_routine_{item_id}"):
                    with st.spinner("관련 영상을 찾는 중입니다..."):
                        try:
                            yt_results = search_exercise_videos_for_dd_raw(routine_query, max_results=4)
                        except Exception as e:
                            st.error(f"영상 검색 오류: {e}")
                            yt_results = []
                        st.session_state[yt_key] = yt_results

                yt_results = st.session_state.get(yt_key, [])
                current_video = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("video_url", "")
                if current_video:
                    st.caption("현재 선택된 영상")
                    st.video(current_video)

                if yt_results:
                    st.caption("추천 영상(최대 4개) 중 하나를 선택해주세요.")
                    for v_idx, v in enumerate(yt_results):
                        st.markdown(f"- {v.get('title','(제목 없음)')}")
                        if v.get("thumbnail"):
                            st.image(v["thumbnail"], use_container_width=True)
                        if st.button("이 영상 사용", key=f"use_yt_routine_{item_id}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_url"] = v["url"]
                            st.success("영상이 적용되었습니다.")
                            st.rerun()

            # ---------------- COOKING ----------------
            elif new_type == "COOKING" or type_ == "COOKING":
                st.markdown("#### 요리 활동 설정(최소)")

                # 메뉴 기본값 보정
                current_menus = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("menus") or []
                if not current_menus:
                    names = _extract_menu_names_from_task(new_task) or [new_task]
                    current_menus = [
                        {"name": name, "image": "assets/images/default_food.png", "video_url": ""}
                        for name in names
                    ]
                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["menus"] = current_menus

                st.markdown("##### 메뉴 이름 설정")
                st.caption("쉼표(,)로 여러 메뉴 입력 가능. 예: 라면, 주먹밥")
                default_selected = [m.get("name") for m in current_menus]
                menu_text_default = ", ".join([x for x in default_selected if x])
                menu_text = st.text_input(
                    "이 시간에 가능한 메뉴들",
                    value=menu_text_default,
                    key=f"cooking_menu_text_{item_id}",
                )

                if st.button("입력한 메뉴 적용하기", key=f"apply_menus_{item_id}"):
                    names = [n.strip() for n in menu_text.split(",") if n.strip()]
                    if not names:
                        st.warning("메뉴 이름을 한 개 이상 입력해 주세요.")
                    else:
                        new_menus = [
                            {"name": name, "image": "assets/images/default_food.png", "video_url": ""}
                            for name in names
                        ]
                        st.session_state[SCHEDULE_STATE_KEY][orig_idx]["menus"] = new_menus
                        st.success("메뉴가 반영되었습니다.")
                        st.rerun()

                with st.expander("참고: 등록된 요리 목록 보기", expanded=False):
                    st.write(", ".join(all_recipe_names))

                # 옵션: 사진/영상 설정(기본 접기)
                with st.expander("옵션: 메뉴 사진/영상 설정", expanded=False):
                    menus = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("menus", [])
                    if menus:
                        st.markdown("##### 메뉴별 사진 및 설명 영상 선택")

                        for m_idx, menu in enumerate(menus):
                            menu_name = menu.get("name", f"메뉴 {m_idx+1}")
                            st.markdown(f"###### {menu_name}")
                            cols = st.columns([1, 2])

                            # 왼쪽: 현재 선택된 사진 + 영상
                            with cols[0]:
                                img_path = menu.get("image")
                                if isinstance(img_path, str) and (
                                    img_path.startswith("http") or os.path.exists(img_path)
                                ):
                                    st.image(img_path, use_container_width=True)
                                elif os.path.exists("assets/images/default_food.png"):
                                    st.image("assets/images/default_food.png", use_container_width=True)
                                else:
                                    st.write("아직 사진이 없습니다.")

                                video_url = menu.get("video_url")
                                if video_url:
                                    st.caption("선택된 요리 영상")
                                    st.video(video_url)

                            # 오른쪽: 사진 찾기 + 영상 찾기
                            with cols[1]:
                                state_key_img = f"img_results_{item_id}_{m_idx}"
                                state_key_yt = f"yt_cook_{item_id}_{m_idx}"

                                # 이미지 추천(최대 6~9개면 과함 → 6개 정도로 제한)
                                if st.button("음식 사진 자동 추천", key=f"search_img_{item_id}_{m_idx}"):
                                    with st.spinner("사진을 찾고 있습니다..."):
                                        try:
                                            results = search_and_filter_food_images(menu_name, max_results=6)
                                        except Exception as e:
                                            st.error(f"사진 검색 오류: {e}")
                                            results = []
                                        st.session_state[state_key_img] = results

                                img_results = st.session_state.get(state_key_img, [])
                                if img_results:
                                    st.caption("추천 사진 중 하나를 골라주세요. (이미지를 클릭하세요)")

                                    # 클릭 방식(설치되어 있으면)
                                    if clickable_images is not None:
                                        thumbs = []
                                        valid_indices = []
                                        for r_idx, img_info in enumerate(img_results[:9]):
                                            thumb = img_info.get("thumbnail") or img_info.get("link")
                                            url = img_info.get("link")
                                            if not (thumb or url):
                                                continue
                                            thumbs.append(thumb or url)
                                            valid_indices.append(r_idx)

                                        if thumbs:
                                            clicked = clickable_images(
                                                thumbs,
                                                titles=[f"이미지 {i+1}" for i in range(len(thumbs))],
                                                div_style={
                                                    "display": "flex",
                                                    "flex-wrap": "wrap",
                                                    "justify-content": "center",
                                                },
                                                img_style={"margin": "5px", "height": "150px"},
                                                key=f"clickable_imgs_{item_id}_{m_idx}",
                                            )
                                            if clicked > -1:
                                                original_idx = valid_indices[clicked]
                                                img_info = img_results[original_idx]
                                                url = img_info.get("link")
                                                try:
                                                    local_path = download_image_to_assets(url, menu_name)
                                                    menu_obj = st.session_state[SCHEDULE_STATE_KEY][orig_idx]["menus"][m_idx]
                                                    menu_obj["image"] = local_path
                                                    menu_obj["image_url"] = url
                                                    st.success("사진이 적용되었습니다.")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"사진 저장 오류: {e}")
                                    else:
                                        st.info(
                                            "이미지를 직접 클릭해서 선택하려면 "
                                            "`streamlit-clickable-images` 설치가 필요합니다.\n"
                                            "현재는 버튼으로 선택합니다."
                                        )
                                        cols_img = st.columns(3)
                                        for r_idx, img_info in enumerate(img_results[:6]):
                                            col = cols_img[r_idx % 3]
                                            with col:
                                                thumb = img_info.get("thumbnail") or img_info.get("link")
                                                url = img_info.get("link")
                                                if thumb:
                                                    st.image(thumb, use_container_width=True)
                                                if st.button("이 사진 사용", key=f"use_img_{item_id}_{m_idx}_{r_idx}"):
                                                    try:
                                                        local_path = download_image_to_assets(url, menu_name)
                                                        menu_obj = st.session_state[SCHEDULE_STATE_KEY][orig_idx]["menus"][m_idx]
                                                        menu_obj["image"] = local_path
                                                        menu_obj["image_url"] = url
                                                        st.success("사진이 적용되었습니다.")
                                                        st.rerun()
                                                    except Exception as e:
                                                        st.error(f"사진 저장 오류: {e}")

                                st.markdown("---")

                                # 유튜브 검색어 입력
                                default_yt_query = menu.get("video_query", f"발달장애인 쉬운 {menu_name} 만들기")
                                yt_query = st.text_input(
                                    "요리 영상 유튜브 검색어",
                                    value=default_yt_query,
                                    key=f"yt_cook_query_{item_id}_{m_idx}",
                                )
                                st.session_state[SCHEDULE_STATE_KEY][orig_idx]["menus"][m_idx]["video_query"] = yt_query

                                # 유튜브 요리 영상 추천(최대 4개)
                                if st.button("요리 영상 추천 받기", key=f"search_yt_cook_{item_id}_{m_idx}"):
                                    with st.spinner("요리 영상을 찾는 중입니다..."):
                                        try:
                                            yt_results = search_cooking_videos_for_dd_raw(yt_query, max_results=4)
                                        except Exception as e:
                                            st.error(f"영상 검색 오류: {e}")
                                            yt_results = []
                                        st.session_state[state_key_yt] = yt_results

                                yt_results = st.session_state.get(state_key_yt, [])
                                if yt_results:
                                    st.caption("추천 요리 영상(최대 4개) 중 하나를 선택해주세요.")
                                    for v_idx, v in enumerate(yt_results):
                                        st.markdown(f"- {v.get('title','(제목 없음)')}")
                                        if v.get("thumbnail"):
                                            st.image(v["thumbnail"], use_container_width=True)
                                        if st.button("이 영상 사용", key=f"use_yt_cook_{item_id}_{m_idx}_{v_idx}"):
                                            st.session_state[SCHEDULE_STATE_KEY][orig_idx]["menus"][m_idx]["video_url"] = v["url"]
                                            st.success("영상이 적용되었습니다.")
                                            st.rerun()

            # ---------------- HEALTH ----------------
            elif new_type == "HEALTH" or type_ == "HEALTH":
                st.markdown("#### 운동/건강 활동 설정")

                current_modes = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("health_modes") or []
                default_modes = (
                    [m["name"] for m in current_modes]
                    if current_modes
                    else [m["name"] for m in all_health_modes]
                )

                selected_modes = st.multiselect(
                    "이 시간에 가능한 운동 종류를 선택하세요.",
                    options=[m["name"] for m in all_health_modes],
                    default=default_modes,
                    key=f"health_select_{item_id}",
                )

                if st.button("운동 종류 적용", key=f"apply_health_{item_id}"):
                    new_modes = []
                    for name in selected_modes:
                        mode = health_name_map[name]
                        new_modes.append({"id": mode["id"], "name": mode["name"]})
                    st.session_state[SCHEDULE_STATE_KEY][orig_idx]["health_modes"] = new_modes
                    st.success("운동 종류가 적용되었습니다.")
                    st.rerun()

                st.markdown("##### 운동 설명 영상 선택")
                yt_key = f"yt_health_{item_id}"

                default_health_query = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get(
                    "video_query_health",
                    f"발달장애인 쉬운 {new_task} 운동 따라하기" if new_task else "발달장애인 쉬운 운동 따라하기",
                )
                health_yt_query = st.text_input(
                    "운동 영상 유튜브 검색어",
                    value=default_health_query,
                    key=f"yt_health_query_{item_id}",
                )
                st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_query_health"] = health_yt_query

                if st.button("운동 영상 추천 받기", key=f"search_yt_health_{item_id}"):
                    with st.spinner("운동 영상을 찾는 중입니다..."):
                        try:
                            yt_results = search_exercise_videos_for_dd_raw(health_yt_query, max_results=4)
                        except Exception as e:
                            st.error(f"영상 검색 오류: {e}")
                            yt_results = []
                        st.session_state[yt_key] = yt_results

                yt_results = st.session_state.get(yt_key, [])
                current_video = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("video_url", "")
                if current_video:
                    st.caption("현재 선택된 운동 영상")
                    st.video(current_video)

                if yt_results:
                    st.caption("추천 운동 영상(최대 4개) 중 하나를 선택해주세요.")
                    for v_idx, v in enumerate(yt_results):
                        st.markdown(f"- {v.get('title','(제목 없음)')}")
                        if v.get("thumbnail"):
                            st.image(v["thumbnail"], use_container_width=True)
                        if st.button("이 영상 사용", key=f"use_yt_health_{item_id}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_url"] = v["url"]
                            st.success("영상이 적용되었습니다.")
                            st.rerun()

            # ---------------- CLOTHING ----------------
            elif new_type == "CLOTHING" or type_ == "CLOTHING":
                st.markdown("#### 옷 입기 활동 설정(날씨 기능 제외)")

                st.caption("날씨는 일단 제외하고, 옷 입기 연습 영상만 설정합니다.")

                yt_key = f"yt_clothing_{item_id}"

                default_clothing_query = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get(
                    "video_query_clothing",
                    f"발달장애인 {new_task} 옷 입기 연습" if new_task else "발달장애인 옷 입기 연습",
                )
                clothing_yt_query = st.text_input(
                    "옷 입기 영상 유튜브 검색어",
                    value=default_clothing_query,
                    key=f"yt_clothing_query_{item_id}",
                )
                st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_query_clothing"] = clothing_yt_query

                if st.button("옷 입기 영상 추천 받기", key=f"search_yt_clothing_{item_id}"):
                    with st.spinner("관련 영상을 찾는 중입니다..."):
                        try:
                            yt_results = search_clothing_videos_for_dd_raw(clothing_yt_query, max_results=4)
                        except Exception as e:
                            st.error(f"영상 검색 오류: {e}")
                            yt_results = []
                        st.session_state[yt_key] = yt_results

                yt_results = st.session_state.get(yt_key, [])
                current_video = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("video_url", "")
                if current_video:
                    st.caption("현재 선택된 옷 입기 영상")
                    st.video(current_video)

                if yt_results:
                    st.caption("추천된 영상(최대 4개) 중 하나를 선택해주세요.")
                    for v_idx, v in enumerate(yt_results):
                        st.markdown(f"- {v.get('title','(제목 없음)')}")
                        if v.get("thumbnail"):
                            st.image(v["thumbnail"], use_container_width=True)
                        if st.button("이 영상 사용", key=f"use_yt_clothing_{item_id}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_url"] = v["url"]
                            st.success("영상이 적용되었습니다.")
                            st.rerun()

            # ---------------- HOBBY ----------------
            elif new_type == "HOBBY" or type_ == "HOBBY":
                st.markdown("#### 취미/여가 활동 설정(유튜브 영상)")

                profile = st.session_state.get(USER_PROFILE_KEY, "기본")
                yt_key = f"yt_hobby_{item_id}"

                # 사용자 선호 기반 기본 검색어
                if profile == "미화님":
                    base_pref = "드라마"
                elif profile == "용화님":
                    # 용화님은 드론/스포츠가 많으니 task에 따라 갈리되 기본은 드론
                    base_pref = "드론"
                else:
                    base_pref = "취미"

                default_hobby_query = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get(
                    "video_query_hobby",
                    f"{base_pref} 다시보기" if not new_task else f"{new_task} 영상",
                )

                hobby_query = st.text_input(
                    "취미/여가 영상 유튜브 검색어",
                    value=default_hobby_query,
                    key=f"yt_hobby_query_{item_id}",
                )
                st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_query_hobby"] = hobby_query

                # (선호 빠른 버튼) 미화=드라마, 용화=드론/스포츠
                colH1, colH2, colH3 = st.columns([1, 1, 1])
                with colH1:
                    if st.button("드라마 추천", key=f"hobby_drama_{item_id}"):
                        st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_query_hobby"] = "드라마 다시보기"
                        st.rerun()
                with colH2:
                    if st.button("드론 추천", key=f"hobby_drone_{item_id}"):
                        st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_query_hobby"] = "드론 날리기 영상"
                        st.rerun()
                with colH3:
                    if st.button("스포츠 추천", key=f"hobby_sports_{item_id}"):
                        st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_query_hobby"] = "스포츠 하이라이트"
                        st.rerun()

                if st.button("취미 영상 추천 받기", key=f"search_yt_hobby_{item_id}"):
                    with st.spinner("취미/여가 영상을 찾는 중입니다..."):
                        try:
                            q = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("video_query_hobby", hobby_query)
                            yt_results = _search_hobby_videos(q, max_results=4)
                        except Exception as e:
                            st.error(f"영상 검색 오류: {e}")
                            yt_results = []
                        st.session_state[yt_key] = yt_results

                yt_results = st.session_state.get(yt_key, [])
                current_video = st.session_state[SCHEDULE_STATE_KEY][orig_idx].get("video_url", "")
                if current_video:
                    st.caption("현재 선택된 취미/여가 영상")
                    st.video(current_video)

                if yt_results:
                    st.caption("추천 취미/여가 영상(최대 4개) 중 하나를 선택해주세요.")
                    for v_idx, v in enumerate(yt_results):
                        st.markdown(f"- {v.get('title','(제목 없음)')}")
                        if v.get("thumbnail"):
                            st.image(v["thumbnail"], use_container_width=True)
                        if st.button("이 영상 사용", key=f"use_yt_hobby_{item_id}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][orig_idx]["video_url"] = v["url"]
                            st.success("영상이 적용되었습니다.")
                            st.rerun()

            else:
                st.caption("이 활동은 추가 설정이 필요하지 않습니다.")

    st.markdown("---")
    st.header("4. 오늘 일정 저장하기")

    if st.button("일정 저장 (schedule_today.json)", type="primary"):
        try:
            path = _save_schedule_to_file(st.session_state[SCHEDULE_STATE_KEY])
            st.success(f"저장 완료! 저장 위치: {path}")
        except Exception as e:
            st.error(f"저장 중 오류: {e}")


if __name__ == "__main__":
    coordinator_page()
