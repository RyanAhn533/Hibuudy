# pages/1_코디네이터_오늘_일정_설계.py
# -*- coding: utf-8 -*-

import os
import json
import re
from datetime import date
from typing import Dict, List

import streamlit as st

try:
    # 이미지 자체를 클릭해서 선택하기 위해 사용
    from streamlit_clickable_images import clickable_images
except ImportError:
    clickable_images = None

# ✅ 날씨 기능은 "있으면 쓰고, 없으면 비활성화" (API키/설정 너가 나중에 붙일 수 있게)
try:
    from utils.weather_ai import analyze_weather_and_suggest_clothes  # type: ignore
except Exception:
    analyze_weather_and_suggest_clothes = None

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

SCHEDULE_STATE_KEY = "hibuddy_schedule"

# ---- 내부 타입 → 화면용 한글 라벨 ----
TYPE_LABEL = {
    "MORNING_BRIEFING": "아침 안내",
    "NIGHT_WRAPUP": "마무리 안내",
    "GENERAL": "일정",
    "ROUTINE": "준비/위생",
    "COOKING": "요리",
    "MEAL": "식사",
    "HEALTH": "운동",
    "CLOTHING": "옷 입기",
    "LEISURE": "여가",
}


def _label_type(type_: str) -> str:
    type_ = (type_ or "").strip()
    return TYPE_LABEL.get(type_, type_ if type_ else "일정")


def _init_state():
    if SCHEDULE_STATE_KEY not in st.session_state:
        st.session_state[SCHEDULE_STATE_KEY] = []


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


def _extract_menu_names_from_task(task: str) -> List[str]:
    """
    예: "라면 또는 카레 중 하나 먹기" → ["라면", "카레"]
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


def _auto_attach_food_candidates(schedule: List[Dict]) -> List[Dict]:
    """
    COOKING / MEAL 타입에서 task를 보고 메뉴 후보(menus)를 자동으로 채움
    """
    for it in schedule:
        type_ = (it.get("type") or "").strip()
        if type_ not in ["COOKING", "MEAL"]:
            continue

        menus = it.get("menus") or []
        if menus:
            continue

        task = (it.get("task") or "").strip()
        names = _extract_menu_names_from_task(task) or ([task] if task else [])
        it["menus"] = [
            {
                "name": name,
                "image": "assets/images/default_food.png",
                "video_url": "",
            }
            for name in names
        ]
    return schedule


def _edit_guide_script(idx: int):
    """
    guide_script를 사용자가 저장 전 수정 가능하도록 text_area로 제공
    """
    item = st.session_state[SCHEDULE_STATE_KEY][idx]
    current_lines = item.get("guide_script") or []
    default_text = "\n".join([str(x) for x in current_lines if str(x).strip()])

    new_text = st.text_area(
        "사용자 안내 문장(guide_script)을 수정할 수 있습니다",
        value=default_text,
        height=120,
        key=f"guide_script_editor_{idx}",
        help="한 줄에 한 문장씩 작성하세요",
    )
    lines = [ln.strip() for ln in new_text.splitlines() if ln.strip()]
    st.session_state[SCHEDULE_STATE_KEY][idx]["guide_script"] = lines


def coordinator_page():
    render_topbar()
    st.title("코디네이터 · 오늘 일정 설계")
    _init_state()

    # ✅ 추천 개수 옵션 (3~4개 제한)
    with st.container():
        st.caption("추천 개수 옵션 (이미지/영상은 최대 3~4개까지만 표시됩니다)")
        rec_n = st.radio(
            "추천 개수",
            options=[3, 4],
            index=1,
            horizontal=True,
            key="hibuddy_rec_n",
        )

    st.header("1. 일정 내용 입력")
    example_text = (
        "08:00 ·  오늘 날씨와 일정 간단 안내\n"
        "10:00 ·  옷 입기 연습하기\n"
        "12:00 ·  라면 또는 카레 중 하나 먹기\n"
        "15:00 ·  쉬는 시간 갖기\n"
        "18:00 ·  앉아서 하는 운동하기\n"
        "22:00 ·  하루 마무리 인사하기\n"
    )
    raw = st.text_area(
        "예시처럼 시간 · [타입] 할 일을 입력하세요",
        value=example_text,
        height=200,
    )

    if st.button("일정 자동 만들기", type="primary"):
        with st.spinner("입력하신 내용을 이해하기 쉬운 일정표로 바꾸는 중입니다..."):
            schedule = generate_schedule_from_text(raw)
            schedule = _auto_attach_food_candidates(schedule)
        st.session_state[SCHEDULE_STATE_KEY] = schedule

    schedule: List[Dict] = st.session_state.get(SCHEDULE_STATE_KEY, [])
    schedule.sort(key=lambda it: parse_hhmm_to_time(it.get("time", "00:00")))

    st.markdown("---")
    st.header("2. 자동으로 만들어진 일정 확인하기")

    if not schedule:
        st.info("먼저 위에서 일정 내용을 입력한 뒤 '일정 자동 만들기' 버튼을 눌러주세요.")
        return

    # 영어 토큰 노출 제거: 화면은 한글 라벨로만
    for item in schedule:
        time_str = item.get("time", "??:??")
        type_ = item.get("type", "")
        task = item.get("task", "")
        st.markdown(f"- **{time_str}** · {_label_type(type_)} · {task}")

    st.markdown("---")
    st.header("3. 활동 자세히 설정하기")

    all_recipe_names = get_all_recipe_names()
    all_health_modes = get_health_modes()
    health_name_map = {m["name"]: m for m in all_health_modes}

    changed = False

    for idx, item in enumerate(schedule):
        time_str = item.get("time", "??:??")
        type_ = (item.get("type") or "").strip()
        task = item.get("task", "")

        expand_types = ["COOKING", "MEAL", "HEALTH", "CLOTHING", "LEISURE"]
        with st.expander(
            f"[{time_str}] {_label_type(type_)} · {task}",
            expanded=(type_ in expand_types),
        ):
            _edit_guide_script(idx)
            st.markdown("---")

            # ---------------- FOOD (COOKING / MEAL) ----------------
            if type_ in ["COOKING", "MEAL"]:
                st.markdown("#### 식사/요리 활동 설정")

                current_menus = item.get("menus") or []
                if not current_menus:
                    names = _extract_menu_names_from_task(task) or [task]
                    current_menus = [
                        {
                            "name": name,
                            "image": "assets/images/default_food.png",
                            "video_url": "",
                        }
                        for name in names
                    ]
                    st.session_state[SCHEDULE_STATE_KEY][idx]["menus"] = current_menus

                st.markdown("##### 메뉴 이름 설정")
                st.caption("쉼표(,)로 구분하여 여러 메뉴를 적을 수 있습니다. 예: 라면, 카레")

                default_selected = [m.get("name") for m in current_menus]
                menu_text_default = ", ".join([x for x in default_selected if x])
                menu_text = st.text_input(
                    "이 시간에 가능한 메뉴들",
                    value=menu_text_default,
                    key=f"food_menu_text_{idx}",
                )

                with st.expander("참고: 등록된 요리 목록 보기", expanded=False):
                    st.write(", ".join(all_recipe_names))

                if st.button("입력한 메뉴 적용하기", key=f"apply_food_menus_{idx}"):
                    names = [n.strip() for n in menu_text.split(",") if n.strip()]
                    if names:
                        new_menus = [
                            {
                                "name": name,
                                "image": "assets/images/default_food.png",
                                "video_url": "",
                            }
                            for name in names
                        ]
                        st.session_state[SCHEDULE_STATE_KEY][idx]["menus"] = new_menus
                        current_menus = new_menus
                        changed = True
                    else:
                        st.warning("메뉴 이름을 한 개 이상 입력해 주세요.")

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
                            if isinstance(img_path, str) and (
                                img_path.startswith("http") or os.path.exists(img_path)
                            ):
                                st.image(img_path, use_container_width=True)
                            else:
                                st.image("assets/images/default_food.png", use_container_width=True)

                            if menu.get("video_url"):
                                st.caption("현재 선택된 요리/식사 영상")
                                st.video(menu["video_url"])

                        # 오른쪽: 이미지 추천 + 영상 추천
                        with cols[1]:
                            st.caption("사진을 추천받아 선택할 수 있습니다.")
                            img_key = f"img_results_{idx}_{m_idx}"

                            default_img_query = menu.get("img_query") or f"{menu_name} 음식"
                            img_query = st.text_input(
                                "이미지 검색어",
                                value=default_img_query,
                                key=f"img_query_{idx}_{m_idx}",
                            )
                            st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["img_query"] = img_query

                            # ✅ image_ai.py 시그니처에 맞춤: max_results / link / download(menu_name)
                            if st.button("사진 추천 받기", key=f"search_img_{idx}_{m_idx}"):
                                with st.spinner("사진을 찾는 중입니다."):
                                    try:
                                        img_results = search_and_filter_food_images(img_query, max_results=rec_n)
                                    except Exception as e:
                                        st.error(f"사진 추천 오류: {e}")
                                        img_results = []
                                    st.session_state[img_key] = img_results

                            img_results = st.session_state.get(img_key, [])

                            if img_results:
                                st.caption("추천 사진 중 하나를 골라주세요.")

                                # clickable_images가 없으면 버튼 선택 fallback
                                if clickable_images is None:
                                    for r_idx, img_info in enumerate(img_results[:rec_n]):
                                        thumb = img_info.get("thumbnail") or img_info.get("link")
                                        url = img_info.get("link")
                                        if thumb:
                                            st.image(thumb, use_container_width=True)
                                        if st.button("이 사진 사용", key=f"use_img_{idx}_{m_idx}_{r_idx}"):
                                            try:
                                                local_path = download_image_to_assets(url, menu_name)
                                                st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["image"] = local_path
                                                st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["image_url"] = url
                                                changed = True
                                                st.success("사진이 적용되었습니다.")
                                            except Exception as e:
                                                st.error(f"사진 저장 오류: {e}")
                                else:
                                    thumbs = []
                                    valid_indices = []
                                    for r_idx, img_info in enumerate(img_results[:rec_n]):
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
                                            div_style={"display": "flex", "flex-wrap": "wrap", "gap": "6px"},
                                            img_style={"height": "90px"},
                                            key=f"click_imgs_{idx}_{m_idx}",
                                        )
                                        if clicked is not None and clicked > -1:
                                            original_idx = valid_indices[clicked]
                                            img_info = img_results[original_idx]
                                            url = img_info.get("link")
                                            try:
                                                local_path = download_image_to_assets(url, menu_name)
                                                st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["image"] = local_path
                                                st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["image_url"] = url
                                                changed = True
                                                st.success("사진이 적용되었습니다.")
                                            except Exception as e:
                                                st.error(f"사진 저장 오류: {e}")

                            st.markdown("---")

                            # ---- 유튜브 영상 검색 (3~4개 제한) ----
                            yt_key = f"yt_food_{idx}_{m_idx}"
                            default_yt_query = menu.get("video_query") or f"발달장애인 쉬운 {menu_name} 만들기"
                            yt_query = st.text_input(
                                "요리/식사 영상 유튜브 검색어",
                                value=default_yt_query,
                                key=f"yt_food_query_{idx}_{m_idx}",
                            )
                            st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["video_query"] = yt_query

                            if st.button("요리/식사 영상 추천 받기", key=f"search_yt_food_{idx}_{m_idx}"):
                                with st.spinner("관련 영상을 찾는 중입니다."):
                                    try:
                                        yt_results = search_cooking_videos_for_dd_raw(yt_query, max_results=rec_n)
                                    except Exception as e:
                                        st.error(f"영상 추천 오류: {e}")
                                        yt_results = []
                                    st.session_state[yt_key] = yt_results

                            yt_results = st.session_state.get(yt_key, [])
                            if yt_results:
                                st.caption("추천된 영상 목록입니다. 하나를 선택해주세요.")
                                for v_idx, v in enumerate(yt_results[:rec_n]):
                                    st.markdown(f"- {v.get('title','')}")
                                    if v.get("thumbnail"):
                                        st.image(v["thumbnail"], use_container_width=True)
                                    if st.button("이 영상 사용", key=f"use_yt_food_{idx}_{m_idx}_{v_idx}"):
                                        st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["video_url"] = v.get("url", "")
                                        changed = True
                                        st.success("영상이 적용되었습니다.")

            # ---------------- HEALTH ----------------
            elif type_ == "HEALTH":
                st.markdown("#### 운동 활동 설정")

                mode_names = [m["name"] for m in all_health_modes]
                current_mode = item.get("health_mode_name") or (mode_names[0] if mode_names else "")

                selected = st.radio(
                    "이 시간에 가능한 운동 종류를 선택하세요",
                    options=mode_names,
                    index=mode_names.index(current_mode) if current_mode in mode_names else 0,
                    key=f"health_mode_{idx}",
                )
                st.session_state[SCHEDULE_STATE_KEY][idx]["health_mode_name"] = selected
                mode_obj = health_name_map.get(selected, {})
                st.session_state[SCHEDULE_STATE_KEY][idx]["health_mode"] = mode_obj

                yt_key = f"yt_health_{idx}"
                default_health_query = item.get(
                    "video_query_health",
                    f"발달장애인 쉬운 {task} 운동 따라하기" if task else "발달장애인 쉬운 운동 따라하기",
                )
                health_yt_query = st.text_input(
                    "운동 영상 유튜브 검색어",
                    value=default_health_query,
                    key=f"yt_health_query_{idx}",
                )
                st.session_state[SCHEDULE_STATE_KEY][idx]["video_query_health"] = health_yt_query

                current_video = item.get("video_url")
                if current_video:
                    st.caption("현재 선택된 운동 영상")
                    st.video(current_video)

                if st.button("운동 영상 추천 받기", key=f"search_yt_health_{idx}"):
                    with st.spinner("운동 영상을 찾는 중입니다."):
                        try:
                            yt_results = search_exercise_videos_for_dd_raw(health_yt_query, max_results=rec_n)
                        except Exception as e:
                            st.error(f"영상 추천 오류: {e}")
                            yt_results = []
                        st.session_state[yt_key] = yt_results

                yt_results = st.session_state.get(yt_key, [])
                if yt_results:
                    st.caption("추천 운동 영상 목록입니다. 하나를 선택해주세요.")
                    for v_idx, v in enumerate(yt_results[:rec_n]):
                        st.markdown(f"- {v.get('title','')}")
                        if v.get("thumbnail"):
                            st.image(v["thumbnail"], use_container_width=True)
                        if st.button("이 영상 사용", key=f"use_yt_health_{idx}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][idx]["video_url"] = v.get("url", "")
                            changed = True
                            st.success("영상이 적용되었습니다.")

            # ---------------- CLOTHING ----------------
            elif type_ == "CLOTHING":
                st.markdown("#### 옷 입기 활동 설정")

                st.markdown("##### 오늘 날씨 기반 옷차림 안내문 만들기")
                if analyze_weather_and_suggest_clothes is None:
                    st.info(
                        "날씨/옷차림 기능은 아직 비활성화 상태입니다.\n"
                        "- utils/weather_ai.py 및 config(날씨 API 키) 설정 후 활성화하세요."
                    )
                else:
                    default_location = st.session_state.get("weather_location_default", "서울")
                    location = st.text_input(
                        "날씨를 확인할 지역 (예: 서울, 서울시 강남구)",
                        value=default_location,
                        key=f"clothing_location_{idx}",
                    )
                    st.session_state["weather_location_default"] = location

                    if st.button("오늘 날씨로 옷차림 안내문 생성", key=f"btn_weather_clothes_{idx}"):
                        if location.strip():
                            with st.spinner("날씨를 확인하고 옷차림 안내문을 만드는 중입니다."):
                                try:
                                    guide_lines = analyze_weather_and_suggest_clothes(location)
                                except Exception as e:
                                    st.error(f"날씨/옷차림 오류: {e}")
                                    guide_lines = []
                            if guide_lines:
                                st.session_state[SCHEDULE_STATE_KEY][idx]["guide_script"] = guide_lines
                                changed = True
                                st.success("guide_script에 반영되었습니다.")
                        else:
                            st.warning("지역을 먼저 입력해 주세요.")

                st.markdown("---")
                st.markdown("##### 옷 입기 연습 영상 선택")

                yt_key = f"yt_clothing_{idx}"
                default_clothing_query = item.get(
                    "video_query_clothing",
                    f"발달장애인 {task} 옷 입기 연습" if task else "발달장애인 옷 입기 연습",
                )
                clothing_yt_query = st.text_input(
                    "옷 입기 영상 유튜브 검색어",
                    value=default_clothing_query,
                    key=f"yt_clothing_query_{idx}",
                )
                st.session_state[SCHEDULE_STATE_KEY][idx]["video_query_clothing"] = clothing_yt_query

                current_video = item.get("video_url")
                if current_video:
                    st.caption("현재 선택된 옷 입기 영상")
                    st.video(current_video)

                if st.button("옷 입기 영상 추천 받기", key=f"search_yt_clothing_{idx}"):
                    with st.spinner("관련 영상을 찾는 중입니다."):
                        try:
                            yt_results = search_clothing_videos_for_dd_raw(clothing_yt_query, max_results=rec_n)
                        except Exception as e:
                            st.error(f"영상 추천 오류: {e}")
                            yt_results = []
                        st.session_state[yt_key] = yt_results

                yt_results = st.session_state.get(yt_key, [])
                if yt_results:
                    st.caption("추천된 영상 목록입니다. 하나를 선택해주세요.")
                    for v_idx, v in enumerate(yt_results[:rec_n]):
                        st.markdown(f"- {v.get('title','')}")
                        if v.get("thumbnail"):
                            st.image(v["thumbnail"], use_container_width=True)
                        if st.button("이 영상 사용", key=f"use_yt_clothing_{idx}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][idx]["video_url"] = v.get("url", "")
                            changed = True
                            st.success("영상이 적용되었습니다.")

            # ---------------- LEISURE ----------------
            elif type_ == "LEISURE":
                st.markdown("#### 여가 활동 설정")
                st.caption("여가 활동은 영상 URL을 직접 넣어도 됩니다. (예: 유튜브 링크)")

                current_video = item.get("video_url", "")
                url = st.text_input(
                    "여가 영상 URL",
                    value=current_video,
                    key=f"leisure_video_url_{idx}",
                    placeholder="https://www.youtube.com/watch?v=...",
                )
                st.session_state[SCHEDULE_STATE_KEY][idx]["video_url"] = url.strip()
                if url.strip():
                    st.caption("현재 선택된 여가 영상")
                    st.video(url.strip())
                    changed = True

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
