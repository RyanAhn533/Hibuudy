# pages/1_코디네이터_오늘_일정_설계.py
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import os
import json
import re
from datetime import date, datetime
from typing import Dict, List

import streamlit as st
import streamlit.components.v1 as components

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
    search_clothing_videos_for_dd_raw,  # 유지(혹시 다른 곳에서 쓸 수도 있어 import는 남겨둠)
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


def _normalize_type_by_task(schedule: List[Dict]) -> List[Dict]:
    def has(text: str, keys) -> bool:
        t = (text or "").strip()
        return any(k in t for k in keys)

    for it in schedule:
        task = (it.get("task") or "").strip()
        ty = (it.get("type") or "").strip().upper()

        # 쉬는/휴식 → REST
        if has(task, ["쉬", "휴식", "잠깐", "물", "화장실"]):
            it["type"] = "REST"
            continue

        # 옷 입기 → CLOTHING
        if has(task, ["옷", "갈아", "입기", "코디", "외출 준비"]):
            it["type"] = "CLOTHING"
            continue

        # MEAL → COOKING (사용자 페이지 호환)
        if ty == "MEAL":
            it["type"] = "COOKING"

    return schedule


def _extract_menu_names_from_task(task: str) -> List[str]:
    """
    예: "라면 또는 카레 중 하나 먹기" → ["라면", "3분카레"]
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


# -------------------------------
# GPT(안내문/일정 수정) 유틸
#   - OPENAI_API_KEY 또는 st.secrets["OPENAI_API_KEY"] 필요
#   - openai 패키지(공식 클라이언트) 설치 필요: pip install openai
# -------------------------------
def _get_openai_client():
    try:
        from openai import OpenAI  # 공식 파이썬 SDK
    except Exception:
        return None, "openai 패키지가 없습니다. (pip install openai)"

    api_key = None
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")  # Streamlit secrets 우선
    except Exception:
        api_key = None

    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "OPENAI_API_KEY가 설정되지 않았습니다. (환경변수 또는 st.secrets)"

    try:
        client = OpenAI(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"OpenAI 클라이언트 초기화 실패: {e}"


def _safe_json_loads(s: str):
    try:
        return json.loads(s)
    except Exception:
        return None


def _call_gpt_json(system: str, user: str, model: str = None) -> Dict:
    client, err = _get_openai_client()
    if err:
        raise RuntimeError(err)

    model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  # 가벼운 기본값(원하면 env로 교체)

    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )
    content = (resp.choices[0].message.content or "").strip()
    data = _safe_json_loads(content) or {}
    return data


def _is_valid_hhmm(s: str) -> bool:
    s = (s or "").strip()
    if not re.match(r"^\d{2}:\d{2}$", s):
        return False
    try:
        datetime.strptime(s, "%H:%M")
        return True
    except Exception:
        return False


def _gpt_make_guide_script(task: str, type_label: str, extra_request: str = "") -> List[str]:
    system = (
        "너는 발달장애인/노인 사용자에게 안내할 짧고 쉬운 문장을 만드는 도우미다. "
        "출력은 반드시 JSON만. 한국어만. 과장 금지. 문장은 1~5개. "
        "각 문장은 20자~45자 정도로 짧게. 숫자는 가능하면 한글로 풀어쓴다."
    )
    user = (
        f"활동 종류: {type_label}\n"
        f"할 일: {task}\n"
        f"추가 요청: {extra_request}\n\n"
        "JSON 스키마:\n"
        '{ "guide_script": ["문장1", "문장2"] }'
    )
    data = _call_gpt_json(system, user)
    lines = data.get("guide_script") or []
    if not isinstance(lines, list):
        return []
    cleaned = [str(x).strip() for x in lines if str(x).strip()]
    return cleaned[:5]


def _gpt_edit_item(item: Dict, request: str) -> Dict:
    """item(time/type/task/guide_script)를 요청에 맞게 수정한 JSON을 반환"""
    system = (
        "너는 일정표를 수정하는 코디네이터 도우미다. "
        "사용자 요청에 따라 time(HH:MM), task(문장), type(내부 코드), guide_script(문장 리스트)를 수정한다. "
        "반드시 JSON만 출력한다. 한국어만. 기존 의미를 최대한 유지한다. "
        "type은 아래 중 하나만 허용: MORNING_BRIEFING, NIGHT_WRAPUP, GENERAL, ROUTINE, COOKING, MEAL, HEALTH, CLOTHING, LEISURE, REST"
    )
    current = {
        "time": item.get("time", ""),
        "type": item.get("type", ""),
        "task": item.get("task", ""),
        "guide_script": item.get("guide_script") or [],
    }
    user = (
        f"현재 항목 JSON:\n{json.dumps(current, ensure_ascii=False)}\n\n"
        f"수정 요청: {request}\n\n"
        "출력 JSON 스키마(필요한 키만 포함 가능):\n"
        '{ "time": "HH:MM", "type": "GENERAL", "task": "…", "guide_script": ["…","…"] }'
    )
    data = _call_gpt_json(system, user)
    if not isinstance(data, dict):
        return {}
    # 허용키만
    allowed = {"time", "type", "task", "guide_script"}
    return {k: v for k, v in data.items() if k in allowed}


def _edit_guide_script(idx: int):
    """guide_script 수동 수정 + (선택) GPT로 자동 생성"""
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



# -------------------------------
# 영상 렌더링: 작게 고정(유튜브)
# -------------------------------
def _to_youtube_embed(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""

    # https://www.youtube.com/watch?v=VIDEO_ID
    if "watch?v=" in url:
        vid = url.split("watch?v=")[1].split("&")[0]
        return f"https://www.youtube.com/embed/{vid}"

    # https://youtu.be/VIDEO_ID
    if "youtu.be/" in url:
        vid = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
        return f"https://www.youtube.com/embed/{vid}"

    # 이미 embed 형식이면 그대로
    if "youtube.com/embed/" in url:
        return url

    return ""


def render_video_small(url: str, width: int = 360, height: int = 220):
    url = (url or "").strip()
    if not url:
        return

    embed = _to_youtube_embed(url)
    if embed:
        components.iframe(embed, width=width, height=height)
    else:
        # 유튜브가 아닌 URL이거나 파싱 실패 시 fallback
        # (그래도 너무 크게 나오는 st.video는 피하고 iframe로 처리)
        components.iframe(url, width=width, height=height)


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
        "08:00 ·  오늘 일정 간단 안내\n"
        "10:00 ·  옷 입기 연습하기\n"
        "12:00 ·  라면 또는 카레 중 하나 먹기\n"
        "15:00 ·  쉬는 시간 갖기\n"
        "18:00 ·  열심히 운동하기\n"
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
    health_name_map = {m["name"]: m for m in all_health_modes}  # (유지) 데이터 호환 목적

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
            # ✅ 코디네이터가 시간/할 일을 직접 수정할 수 있도록 입력창 제공
            col_a, col_b = st.columns([1, 3])
            with col_a:
                new_time = st.text_input(
                    "시간(HH:MM)",
                    value=str(time_str),
                    key=f"edit_time_{idx}",
                ).strip()
            with col_b:
                new_task = st.text_input(
                    "할 일(문장)",
                    value=str(task),
                    key=f"edit_task_{idx}",
                ).strip()

            if new_time and new_time != time_str:
                if _is_valid_hhmm(new_time):
                    st.session_state[SCHEDULE_STATE_KEY][idx]["time"] = new_time
                    changed = True
                else:
                    st.warning("시간 형식이 올바르지 않습니다. 예: 08:30")

            if new_task != task:
                st.session_state[SCHEDULE_STATE_KEY][idx]["task"] = new_task
                task = new_task
                changed = True

            # (선택) GPT로 이 항목(time/task/guide_script 등) 한 번에 수정
            with st.expander("GPT로 이 일정 수정(선택)", expanded=False):
                gpt_req = st.text_input(
                    "수정 요청",
                    value="",
                    key=f"gpt_edit_req_{idx}",
                    placeholder="예: 시간을 19:30으로 바꾸고 안내문을 더 짧게",
                )
                if st.button("GPT로 수정 적용", key=f"btn_gpt_edit_{idx}"):
                    try:
                        patch = _gpt_edit_item(st.session_state[SCHEDULE_STATE_KEY][idx], gpt_req)
                        if "time" in patch:
                            if _is_valid_hhmm(str(patch["time"])):
                                st.session_state[SCHEDULE_STATE_KEY][idx]["time"] = str(patch["time"])
                                changed = True
                            else:
                                st.warning("GPT가 준 시간이 HH:MM 형식이 아닙니다. (적용 안 함)")
                        if "task" in patch:
                            st.session_state[SCHEDULE_STATE_KEY][idx]["task"] = str(patch["task"]).strip()
                            changed = True
                        if "type" in patch:
                            st.session_state[SCHEDULE_STATE_KEY][idx]["type"] = str(patch["type"]).strip()
                            changed = True
                        if "guide_script" in patch and isinstance(patch["guide_script"], list):
                            gs = [str(x).strip() for x in patch["guide_script"] if str(x).strip()]
                            st.session_state[SCHEDULE_STATE_KEY][idx]["guide_script"] = gs[:5]
                            changed = True

                        st.success("GPT 수정이 적용되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"GPT 일정 수정 오류: {e}")

            _edit_guide_script(idx)
            st.markdown("---")
            # ---------------- COOKING ----------------
            if type_ == "COOKING":
                st.markdown("#### 요리 활동 설정")

                current_menus = item.get("menus") or []
                if not current_menus:
                    names = _extract_menu_names_from_task(task) or [task]
                    current_menus = [
                        {"name": name, "image": "assets/images/default_food.png", "video_url": ""}
                        for name in names
                    ]
                    st.session_state[SCHEDULE_STATE_KEY][idx]["menus"] = current_menus

                st.markdown("##### 만들 요리(메뉴) 이름 설정")
                st.caption("쉼표(,)로 구분하여 여러 메뉴를 적을 수 있습니다. 예: 라면, 카레")

                default_selected = [m.get("name") for m in current_menus]
                menu_text_default = ", ".join([x for x in default_selected if x])
                menu_text = st.text_input(
                    "이 시간에 만들 수 있는 요리들",
                    value=menu_text_default,
                    key=f"cook_menu_text_{idx}",
                )

                with st.expander("참고: 등록된 요리 목록 보기", expanded=False):
                    st.write(", ".join(all_recipe_names))

                if st.button("요리 메뉴 적용하기", key=f"apply_cook_menus_{idx}"):
                    names = [n.strip() for n in menu_text.split(",") if n.strip()]
                    if names:
                        new_menus = [{"name": name, "image": "assets/images/default_food.png", "video_url": ""} for name in names]
                        st.session_state[SCHEDULE_STATE_KEY][idx]["menus"] = new_menus
                        current_menus = new_menus
                        changed = True
                    else:
                        st.warning("요리 이름을 한 개 이상 입력해 주세요.")

                menus = st.session_state[SCHEDULE_STATE_KEY][idx].get("menus", [])
                if menus:
                    st.markdown("##### 요리별 사진 및 설명 영상 선택")
                    for m_idx, menu in enumerate(menus):
                        menu_name = menu.get("name", f"요리 {m_idx+1}")
                        st.markdown(f"###### {menu_name}")
                        cols = st.columns([1, 2])

                        with cols[0]:
                            img_path = menu.get("image")
                            if isinstance(img_path, str) and (img_path.startswith("http") or os.path.exists(img_path)):
                                st.image(img_path, use_container_width=True)
                            else:
                                st.image("assets/images/default_food.png", use_container_width=True)

                            if menu.get("video_url"):
                                st.caption("현재 선택된 요리 영상")
                                render_video_small(menu["video_url"], width=360, height=220)

                        with cols[1]:
                            st.caption("사진을 추천받아 선택할 수 있습니다.")
                            img_key = f"img_results_cook_{idx}_{m_idx}"
                            default_img_query = menu.get("img_query") or f"{menu_name} 음식"
                            img_query = st.text_input(
                                "이미지 검색어",
                                value=default_img_query,
                                key=f"img_query_cook_{idx}_{m_idx}",
                            )
                            st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["img_query"] = img_query

                            if st.button("사진 추천 받기", key=f"search_img_cook_{idx}_{m_idx}"):
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
                                # (아래 선택 로직은 너 기존 그대로 복붙하면 됨)
                                # clickable_images / fallback 버튼 부분은 기존 코드 그대로 사용

                            st.markdown("---")

                            yt_key = f"yt_cook_{idx}_{m_idx}"
                            default_yt_query = menu.get("video_query") or f"발달장애인 쉬운 {menu_name} 만들기"
                            yt_query = st.text_input(
                                "요리 영상 유튜브 검색어",
                                value=default_yt_query,
                                key=f"yt_query_cook_{idx}_{m_idx}",
                            )
                            st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["video_query"] = yt_query

                            if st.button("요리 영상 추천 받기", key=f"search_yt_cook_{idx}_{m_idx}"):
                                with st.spinner("관련 영상을 찾는 중입니다."):
                                    try:
                                        yt_results = search_cooking_videos_for_dd_raw(yt_query, max_results=rec_n)
                                    except Exception as e:
                                        st.error(f"영상 추천 오류: {e}")
                                        yt_results = []
                                    st.session_state[yt_key] = yt_results

                            yt_results = st.session_state.get(yt_key, [])
                            if yt_results:
                                st.caption("추천된 요리 영상입니다. 하나를 선택해주세요.")
                                for v_idx, v in enumerate(yt_results[:rec_n]):
                                    st.markdown(f"- {v.get('title','')}")
                                    if v.get("thumbnail"):
                                        st.image(v["thumbnail"], width=240)
                                    if st.button("이 영상 사용", key=f"use_yt_cook_{idx}_{m_idx}_{v_idx}"):
                                        st.session_state[SCHEDULE_STATE_KEY][idx]["menus"][m_idx]["video_url"] = v.get("url", "")
                                        changed = True
                                        st.success("영상이 적용되었습니다.")


            # ---------------- MEAL ----------------
            elif type_ == "MEAL":
                st.markdown("#### 식사 활동 설정")

                # 식사는 '메뉴 1개' 기본으로 두는 게 관리가 편함(원하면 여러 개도 가능)
                meal_name_default = item.get("meal_name") or (task.strip() if task.strip() else "식사")
                meal_name = st.text_input("식사 이름", value=meal_name_default, key=f"meal_name_{idx}")
                st.session_state[SCHEDULE_STATE_KEY][idx]["meal_name"] = meal_name

                # 식사 사진(선택)
                st.caption("식사 사진(선택)")
                meal_img_key = f"img_results_meal_{idx}"
                default_img_query = item.get("meal_img_query") or f"{meal_name} 음식"
                meal_img_query = st.text_input("이미지 검색어", value=default_img_query, key=f"meal_img_query_{idx}")
                st.session_state[SCHEDULE_STATE_KEY][idx]["meal_img_query"] = meal_img_query

                current_meal_img = item.get("meal_image") or ""
                if current_meal_img:
                    st.image(current_meal_img, use_container_width=True)

                if st.button("식사 사진 추천 받기", key=f"search_img_meal_{idx}"):
                    with st.spinner("사진을 찾는 중입니다."):
                        try:
                            img_results = search_and_filter_food_images(meal_img_query, max_results=rec_n)
                        except Exception as e:
                            st.error(f"사진 추천 오류: {e}")
                            img_results = []
                        st.session_state[meal_img_key] = img_results

                img_results = st.session_state.get(meal_img_key, [])
                if img_results:
                    st.caption("추천 사진 중 하나를 골라주세요.")
                    # ✅ 여기 선택 로직도 너 기존 clickable_images/fallback 그대로 복붙
                    # 선택 시: st.session_state[SCHEDULE_STATE_KEY][idx]["meal_image"] = local_path

                st.markdown("---")

                # 식사 영상: 요리처럼 "만들기"가 아니라 "먹기/식사 예절/천천히 먹기" 쿼리가 더 맞음
                meal_yt_key = f"yt_meal_{idx}"
                default_meal_yt_query = item.get("meal_video_query") or f"발달장애인 쉬운 식사 먹기 {meal_name}"
                meal_yt_query = st.text_input("식사 영상 유튜브 검색어", value=default_meal_yt_query, key=f"meal_yt_query_{idx}")
                st.session_state[SCHEDULE_STATE_KEY][idx]["meal_video_query"] = meal_yt_query

                current_meal_video = item.get("meal_video_url") or ""
                if current_meal_video:
                    st.caption("현재 선택된 식사 영상")
                    render_video_small(current_meal_video, width=360, height=220)

                if st.button("식사 영상 추천 받기", key=f"search_yt_meal_{idx}"):
                    with st.spinner("관련 영상을 찾는 중입니다."):
                        try:
                            # ✅ 너 유튜브 유틸이 cooking 검색만 있으면 일단 재사용 가능
                            yt_results = search_cooking_videos_for_dd_raw(meal_yt_query, max_results=rec_n)
                        except Exception as e:
                            st.error(f"영상 추천 오류: {e}")
                            yt_results = []
                        st.session_state[meal_yt_key] = yt_results

                yt_results = st.session_state.get(meal_yt_key, [])
                if yt_results:
                    st.caption("추천된 식사 영상입니다. 하나를 선택해주세요.")
                    for v_idx, v in enumerate(yt_results[:rec_n]):
                        st.markdown(f"- {v.get('title','')}")
                        if v.get("thumbnail"):
                            st.image(v["thumbnail"], width=240)
                        if st.button("이 영상 사용", key=f"use_yt_meal_{idx}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][idx]["meal_video_url"] = v.get("url", "")
                            changed = True
                            st.success("영상이 적용되었습니다.")

            # ---------------- HEALTH ----------------
            elif type_ == "HEALTH":
                st.markdown("#### 운동 활동 설정")

                # (요청 반영) 운동 방식 선택 UI는 제거했습니다.

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
                    render_video_small(current_video, width=360, height=220)

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
                            st.image(v["thumbnail"], width=240)  # ✅ 썸네일 크기 축소
                        if st.button("이 영상 사용", key=f"use_yt_health_{idx}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][idx]["video_url"] = v.get("url", "")
                            changed = True
                            st.success("영상이 적용되었습니다.")

            # ---------------- LEISURE ----------------
            elif type_ == "LEISURE":
                st.markdown("#### 여가 활동 설정")
                st.caption("여가 활동은 '검색해서 고르기' 또는 'URL 직접 입력' 둘 다 가능합니다.")

                # 1) 검색 UI
                yt_key = f"yt_leisure_{idx}"
                default_leisure_query = item.get(
                    "video_query_leisure",
                    f"발달장애인 쉬운 {task} 여가 활동" if task else "발달장애인 쉬운 여가 활동",
                )
                leisure_query = st.text_input(
                    "여가 영상 유튜브 검색어",
                    value=default_leisure_query,
                    key=f"yt_leisure_query_{idx}",
                )
                st.session_state[SCHEDULE_STATE_KEY][idx]["video_query_leisure"] = leisure_query

                if st.button("여가 영상 추천 받기", key=f"search_yt_leisure_{idx}"):
                    with st.spinner("관련 여가 영상을 찾는 중입니다."):
                        try:
                            # ✅ 현재 utils.youtube_ai에 여가 전용 함수가 없으니,
                            #    일단 범용적으로 잘 동작하는 exercise 검색 함수를 재사용합니다.
                            yt_results = search_exercise_videos_for_dd_raw(leisure_query, max_results=rec_n)
                        except Exception as e:
                            st.error(f"영상 추천 오류: {e}")
                            yt_results = []
                        st.session_state[yt_key] = yt_results

                yt_results = st.session_state.get(yt_key, [])
                if yt_results:
                    st.caption("추천 여가 영상 목록입니다. 하나를 선택해주세요.")
                    for v_idx, v in enumerate(yt_results[:rec_n]):
                        st.markdown(f"- {v.get('title','')}")
                        if v.get("thumbnail"):
                            st.image(v["thumbnail"], width=240)  # ✅ 썸네일 크기 축소
                        if st.button("이 영상 사용", key=f"use_yt_leisure_{idx}_{v_idx}"):
                            st.session_state[SCHEDULE_STATE_KEY][idx]["video_url"] = v.get("url", "")
                            changed = True
                            st.success("영상이 적용되었습니다.")

                st.markdown("---")

    st.markdown("---")
    st.header("4. 오늘 일정 저장하기")

    if st.button("일정 저장 (schedule_today.json)", type="primary"):
        try:
            sched = st.session_state[SCHEDULE_STATE_KEY]
            sched = _normalize_type_by_task(sched)  # ✅ 이 줄 추가
            path = _save_schedule_to_file(sched)    # ✅ sched로 저장
            st.success(f"저장 완료! 저장 위치: {path}")
        except Exception as e:
            st.error(f"저장 중 오류: {e}")


if __name__ == "__main__":
    coordinator_page()
