# pages/1_코디네이터_오늘_일정_설계.py
# -*- coding: utf-8 -*-

import os
import json
import re
from datetime import date
from typing import Dict, List

import streamlit as st

from utils.weather_ai import analyze_weather_and_suggest_clothes
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
    search_cooking_videos_for_dd,
    search_exercise_videos_for_dd,
    search_clothing_videos_for_dd,
)

SCHEDULE_STATE_KEY = "hibuddy_schedule"


# ---- 내부 상태 초기화 ----
def _init_state():
    if SCHEDULE_STATE_KEY not in st.session_state:
        st.session_state[SCHEDULE_STATE_KEY] = []


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


# ---- 메인 화면 ----
def coordinator_page():
    _init_state()
    render_topbar()

    st.header("1. 오늘 일정 만들기 (코디네이터용)")

    example_text = (
        "아침 8시에 오늘 날씨와 일정 간단 안내,\n"
        "10시에 옷 입기 연습,\n"
        "12시에 라면 또는 카레 중 하나 먹기,\n"
        "15시에 쉬는 시간,\n"
        "18시에 앉아서 하는 운동,\n"
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
            schedule = _auto_attach_cooking_candidates(schedule)

        st.session_state[SCHEDULE_STATE_KEY] = schedule
        st.success("일정이 생성되었습니다. 아래에서 요리/운동/옷 입기 설정을 자세히 이어서 할 수 있습니다.")

    schedule: List[Dict] = st.session_state.get(SCHEDULE_STATE_KEY, [])
    schedule.sort(key=lambda it: parse_hhmm_to_time(it.get("time", "00:00")))

    st.markdown("---")
    st.header("2. 자동으로 만들어진 일정 확인하기")

    if not schedule:
        st.info("먼저 위에서 일정 내용을 입력한 뒤 '일정 자동 만들기' 버튼을 눌러주세요.")
        return

    for item in schedule:
        st.markdown(
            f"- **{item.get('time', '??:??')}** · [{item.get('type', '')}] {item.get('task', '')}"
        )

    st.markdown("---")
    st.header("3. 요리 / 운동 / 옷 입기 활동 자세히 꾸미기")

    all_recipe_names = get_all_recipe_names()
    all_health_modes = get_health_modes()
    health_name_map = {m["name"]: m for m in all_health_modes}

    changed = False

    # ---- 활동별 편집 화면 ----
    for idx, item in enumerate(schedule):
        time_str = item.get("time", "??:??")
        type_ = item.get("type", "")
        task = item.get("task", "")

        with st.expander(
            f"[{time_str}] {task} (활동 종류: {type_})",
            expanded=(type_ in ["COOKING", "HEALTH", "CLOTHING"]),
        ):
            st.write("**사용자에게 보여줄 안내 문장(guide_script)**")
            for line in item.get("guide_script", []):
                st.markdown(f"- {line}")

            # ---------------- COOKING ----------------
            if type_ == "COOKING":
                st.markdown("#### 요리 활동 설정")

                # 메뉴 기본값 보정
                current_menus = item.get("menus") or []
                if not current_menus:
                    names = _extract_menu_names_from_task(task) or [task]
                    current_menus = [
                        {"name": name, "image": "assets/images/default_food.png", "video_url": ""}
                        for name in names
                    ]
                    st.session_state[SCHEDULE_STATE_KEY][idx]["menus"] = current_menus

                # 메뉴 수동 입력
                st.markdown("##### 메뉴 이름 설정")
                st.caption("쉼표(,)로 구분하여 여러 메뉴를 적을 수 있습니다. 예: 라면, 카레")

                default_selected = [m.get("name") for m in current_menus]
                menu_text_default = ", ".join(default_selected)
                menu_text = st.text_input(
                    "이 시간에 가능한 메뉴들",
                    value=menu_text_default,
                    key=f"cooking_menu_text_{idx}",
                )

                with st.expander("참고: 등록된 요리 목록 보기", expanded=False):
                    st.write(", ".join(all_recipe_names))

                if st.button("입력한 메뉴 적용하기", key=f"apply_menus_{idx}"):
                    names = [n.strip() for n in menu_text.split(",") if n.strip()]
                    if not names:
                        st.warning("메뉴 이름을 한 개 이상 입력해 주세요.")
                    else:
                        new_menus = [
                            {"name": name, "image": "assets/images/default_food.png", "video_url": ""}
                            for name in names
                        ]
                        st.session_state[SCHEDULE_STATE_KEY][idx]["menus"] = new_menus
                        current_menus = new_menus
                        changed = True
                        st.success("메뉴가 반영되었습니다.")

                # 메뉴별 이미지 & 유튜브 설정
                menus = st.session_state[SCHEDULE_STATE_KEY][idx].get("menus", [])
                if menus:
                    st.markdown("##### 메뉴별 사진 및 설명 영상 선택")

                    for m_idx, menu in enumerate(menus):
                        menu_name = menu.get("name", f"메뉴 {m_idx+1}")
                        st.markdown(f"###### {menu_name}")
                        cols = st.columns([1, 2])

                        # 왼쪽: 현재 선택된 사진 + 영상
                        with cols[0]:
                            img_path = menu.get("image")
                            if isinstance(img_path, str) and (img_path.startswith("http") or os.path.exists(img_path)):
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
                            state_key_img = f"img_results_{idx}_{m_idx}"
                            state_key_yt = f"yt_cook_{idx}_{m_idx}"

                            # 이미지 추천
                            if st.button("음식 사진 자동 추천", key=f"search_img_{idx}_{m_idx}"):
                                with st.spinner("사진을 찾고 있습니다..."):
                                    try:
                                        results = search_and_filter_food_images(menu_name, max_results=6)
                                    except Exception as e:
                                        st.error(f"사진 검색 오류: {e}")
                                        results = []
                                    st.session_state[state_key_img] = results

                            img_results = st.session_state.get(state_key_img, [])
                            if img_results:
                                st.caption("추천 사진 중 하나를 골라주세요.")
                                cols_img = st.columns(3)
                                for r_idx, img_info in enumerate(img_results[:6]):
                                    col = cols_img[r_idx % 3]
                                    with col:
                                        thumb = img_info.get("thumbnail") or img_info.get("link")
                                        url = img_info.get("link")
                                        if thumb:
                                            st.image(thumb, use_container_width=True)

                                        if st.button("이 사진 사용", key=f"use_img_{idx}_{m_idx}_{r_idx}"):
                                            try:
                                                local_path = download_image_to_assets(url, menu_name)
                                                menu_obj = st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]
                                                menu_obj["image"] = local_path
                                                menu_obj["image_url"] = url
                                                changed = True
                                                st.success("사진이 적용되었습니다.")
                                            except Exception as e:
                                                st.error(f"사진 저장 오류: {e}")

                            st.markdown("---")

                            # 유튜브 검색어 입력
                            default_yt_query = menu.get(
                                "video_query",
                                f"발달장애인 쉬운 {menu_name} 만들기"
                            )
                            yt_query = st.text_input(
                                "요리 영상 유튜브 검색어",
                                value=default_yt_query,
                                key=f"yt_cook_query_{idx}_{m_idx}",
                            )
                            # 입력값을 메뉴 객체에도 저장 (다시 열었을 때 유지)
                            st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["video_query"] = yt_query

                            # 유튜브 요리 영상 추천
                            if st.button("요리 영상 추천 받기", key=f"search_yt_cook_{idx}_{m_idx}"):
                                with st.spinner("요리 영상을 찾는 중입니다..."):
                                    try:
                                        yt_results = search_cooking_videos_for_dd(yt_query, max_results=6)
                                    except Exception as e:
                                        st.error(f"영상 검색 오류: {e}")
                                        yt_results = []
                                    st.session_state[state_key_yt] = yt_results

                            yt_results = st.session_state.get(state_key_yt, [])
                            if yt_results:
                                st.caption("추천 요리 영상 목록입니다. 하나를 선택해주세요.")
                                for v_idx, v in enumerate(yt_results):
                                    st.markdown(f"- {v['title']}")
                                    if v.get("thumbnail"):
                                        st.image(v["thumbnail"], use_container_width=True)
                                    if st.button("이 영상 사용", key=f"use_yt_cook_{idx}_{m_idx}_{v_idx}"):
                                        st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["video_url"] = v["url"]
                                        changed = True
                                        st.success("영상이 적용되었습니다.")

            # ---------------- HEALTH ----------------
            elif type_ == "HEALTH":
                st.markdown("#### 운동 활동 설정")

                current_modes = item.get("health_modes") or []
                default_modes = (
                    [m["name"] for m in current_modes]
                    if current_modes
                    else [m["name"] for m in all_health_modes]
                )

                selected_modes = st.multiselect(
                    "이 시간에 가능한 운동 종류를 선택하세요.",
                    options=[m["name"] for m in all_health_modes],
                    default=default_modes,
                    key=f"health_select_{idx}",
                )

                if st.button("운동 종류 적용", key=f"apply_health_{idx}"):
                    new_modes = []
                    for name in selected_modes:
                        mode = health_name_map[name]
                        new_modes.append({"id": mode["id"], "name": mode["name"]})
                    st.session_state[SCHEDULE_STATE_KEY][idx]["health_modes"] = new_modes
                    changed = True
                    st.success("운동 종류가 적용되었습니다.")

                # 운동 영상 추천
                st.markdown("##### 운동 설명 영상 선택")
                yt_key = f"yt_health_{idx}"

                # 기본 검색어 (task 기반) + 저장된 값 우선
                default_health_query = item.get(
                    "video_query_health",
                    f"발달장애인 쉬운 {task} 운동 따라하기"
                    if task
                    else "발달장애인 쉬운 운동 따라하기"
                )
                health_yt_query = st.text_input(
                    "운동 영상 유튜브 검색어",
                    value=default_health_query,
                    key=f"yt_health_query_{idx}",
                )
                # 상태에 저장해서 유지
                st.session_state[SCHEDULE_STATE_KEY][idx]["video_query_health"] = health_yt_query

                if st.button("운동 영상 추천 받기", key=f"search_yt_health_{idx}"):
                    with st.spinner("운동 영상을 찾는 중입니다..."):
                        try:
                            yt_results = search_exercise_videos_for_dd(health_yt_query, max_results=6)
                        except Exception as e:
                            st.error(f"영상 검색 오류: {e}")
                            yt_results = []
                        st.session_state[yt_key] = yt_results

                yt_results = st.session_state.get(yt_key, [])
                current_video = item.get("video_url")
                if current_video:
                    st.caption("현재 선택된 운동 영상")
                    st.video(current_video)

                if yt_results:
                    st.caption("추천 운동 영상 목록입니다. 하나를 선택해주세요.")
                    for v_idx, v in enumerate(yt_results):
                        st.markdown(f"- {v['title']}")
                        if v.get("thumbnail"):
                            st.image(v["thumbnail"], use_container_width=True)
                        if st.button("이 영상 사용", key=f"use_yt_health_{idx}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][idx]["video_url"] = v["url"]
                            changed = True
                            st.success("영상이 적용되었습니다.")

            # ---------------- CLOTHING ----------------
            elif type_ == "CLOTHING":
                st.markdown("#### 옷 입기 활동 설정")

                # ---- 오늘 날씨 기반 옷차림 안내문 생성 ----
                st.markdown("##### 오늘 날씨 기반 옷차림 안내문 만들기")

                default_location = st.session_state.get("weather_location_default", "서울")
                location = st.text_input(
                    "날씨를 확인할 지역 (예: 서울, 서울시 강남구)",
                    value=default_location,
                    key=f"clothing_location_{idx}",
                )
                st.session_state["weather_location_default"] = location

                if st.button("오늘 날씨로 옷차림 안내문 생성", key=f"btn_weather_clothes_{idx}"):
                    if not location.strip():
                        st.warning("지역을 먼저 입력해 주세요.")
                    else:
                        with st.spinner("오늘 날씨를 확인하고, 옷차림 안내문을 만드는 중입니다..."):
                            try:
                                result = analyze_weather_and_suggest_clothes(location)
                                guide_script = result.get("guide_script") or []
                                st.session_state[SCHEDULE_STATE_KEY][idx]["guide_script"] = guide_script
                                changed = True

                                st.success("오늘 날씨를 반영한 옷차림 안내문을 guide_script에 저장했습니다.")
                                st.info("날씨 요약: " + result.get("weather_summary", ""))

                                clothes = result.get("clothes", [])
                                if clothes:
                                    st.write("추천 옷차림:")
                                    for c in clothes:
                                        st.markdown(f"- {c}")
                            except Exception as e:
                                st.error(f"날씨/옷차림 추천 중 오류가 발생했습니다: {e}")

                st.markdown("---")
                st.markdown("##### 옷 입기 연습 영상 선택")

                yt_key = f"yt_clothing_{idx}"

                # 기본 검색어 (task/날씨 기반) + 저장된 값 우선
                # 날씨 요약을 바로 쓰기에는 이 함수 안에서 result를 들고 있지 않으니, 일단 task 기반으로 둔다
                default_clothing_query = item.get(
                    "video_query_clothing",
                    f"발달장애인 {task} 옷 입기 연습"
                    if task
                    else "발달장애인 옷 입기 연습"
                )
                clothing_yt_query = st.text_input(
                    "옷 입기 영상 유튜브 검색어",
                    value=default_clothing_query,
                    key=f"yt_clothing_query_{idx}",
                )
                # 상태에 저장
                st.session_state[SCHEDULE_STATE_KEY][idx]["video_query_clothing"] = clothing_yt_query

                if st.button("옷 입기 영상 추천 받기", key=f"search_yt_clothing_{idx}"):
                    with st.spinner("관련 영상을 찾는 중입니다..."):
                        try:
                            yt_results = search_clothing_videos_for_dd(clothing_yt_query, max_results=6)
                        except Exception as e:
                            st.error(f"영상 검색 오류: {e}")
                            yt_results = []
                        st.session_state[yt_key] = yt_results

                yt_results = st.session_state.get(yt_key, [])
                current_video = item.get("video_url")
                if current_video:
                    st.caption("현재 선택된 옷 입기 영상")
                    st.video(current_video)

                if yt_results:
                    st.caption("추천된 영상 목록입니다. 하나를 선택해주세요.")
                    for v_idx, v in enumerate(yt_results):
                        st.markdown(f"- {v['title']}")
                        if v.get("thumbnail"):
                            st.image(v["thumbnail"], use_container_width=True)
                        if st.button("이 영상 사용", key=f"use_yt_clothing_{idx}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][idx]["video_url"] = v["url"]
                            changed = True
                            st.success("영상이 적용되었습니다.")

            else:
                st.caption("이 활동은 추가 설정이 필요하지 않습니다.")

    if changed:
        st.info("모든 변경 사항이 저장되었습니다. 아래에서 오늘 일정을 파일로 저장할 수 있습니다.")

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
