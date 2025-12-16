# pages/2_사용자_오늘_따라하기.py
# -*- coding: utf-8 -*-
import base64
import json
import os
from datetime import datetime, date
from typing import Optional, List, Dict

from urllib.parse import quote as urlquote  # 메뉴 이름을 이미지 검색 쿼리로 쓰기 위해 인코딩

import streamlit as st
from streamlit_autorefresh import st_autorefresh  # 세션 유지 자동 새로고침

from utils.topbar import render_topbar
from utils.runtime import find_active_item, annotate_schedule_with_status
from utils.recipes import get_recipe, get_health_routine
from utils.tts import synthesize_tts  # TTS 유틸

# ─────────────────────────────────────────────
# 타임존 설정 (Asia/Seoul 고정)
# ─────────────────────────────────────────────
try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python 3.8 이하에서 backports 사용 가능
    from backports.zoneinfo import ZoneInfo  # type: ignore

KST = ZoneInfo("Asia/Seoul")

SCHEDULE_PATH = os.path.join("data", "schedule_today.json")
AUTO_REFRESH_SEC = 10  # 모바일에서 타이밍 정확도를 조금 더 높이려면 5~10 권장 (너무 낮추면 배터리/트래픽 증가)
PRE_NOTICE_MINUTES = 5

# 알람 사운드 파일(있으면 사용)
ALARM_SOUND_PATH = os.path.join("assets", "sounds", "alarm.mp3")


# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────
def _load_schedule():
    """data/schedule_today.json에서 스케줄과 날짜를 읽어온다."""
    if not os.path.exists(SCHEDULE_PATH):
        st.error("오늘 스케줄 파일이 없습니다. 코디네이터 페이지에서 먼저 저장해 주세요.")
        st.stop()

    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    date_str = data.get("date") or data.get("date_str") or ""
    schedule = data.get("schedule", [])
    if not isinstance(schedule, list):
        schedule = []

    # 시간 순 정렬
    def _key(item: Dict):
        return str(item.get("time", ""))

    schedule = sorted(schedule, key=_key)
    return schedule, date_str


def _make_slot_key(date_str: str, slot: Dict) -> str:
    """슬롯이 바뀌었는지 비교하기 위한 키."""
    return f"{date_str}_{slot.get('time','')}_{slot.get('type','')}_{slot.get('task','')}"


def _read_bytes(path: str) -> Optional[bytes]:
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


def _make_silence_wav(duration_sec: float = 0.2, sample_rate: int = 8000) -> bytes:
    """
    아주 짧은 무음 WAV(PCM 16bit mono).
    모바일 브라우저에서 '첫 사용자 터치 이후' 오디오 컨텍스트를 열어두는 용도.
    """
    import struct

    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    num_samples = int(sample_rate * duration_sec)
    data_size = num_samples * block_align

    # RIFF header
    riff = b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVE"
    # fmt chunk
    fmt = (
        b"fmt "
        + struct.pack("<I", 16)
        + struct.pack("<H", 1)  # PCM
        + struct.pack("<H", num_channels)
        + struct.pack("<I", sample_rate)
        + struct.pack("<I", byte_rate)
        + struct.pack("<H", block_align)
        + struct.pack("<H", bits_per_sample)
    )
    # data chunk
    data = b"data" + struct.pack("<I", data_size) + (b"\x00\x00" * num_samples)

    return riff + fmt + data


# ─────────────────────────────────────────────
# TTS 재생(자동/버튼) 유틸
# ─────────────────────────────────────────────
def _play_tts_auto(text: str):
    """
    자동재생 TTS (모바일에서는 사용자 제스처 없으면 막힐 수 있음).
    """
    audio_bytes = synthesize_tts(text)
    if not audio_bytes:
        return

    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    html = f"""
    <audio autoplay="true">
      <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
    </audio>
    """
    st.markdown(html, unsafe_allow_html=True)


def _tts_button(text: str, key: str, label: str = "🔊 듣기"):
    """
    버튼을 눌렀을 때 재생되는 TTS.
    """
    if st.button(label, key=key):
        audio_bytes = synthesize_tts(text)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mpeg")


def _play_alarm_then_tts(alarm_bytes: Optional[bytes], tts_bytes: bytes):
    """
    (가능하면) 알람 → TTS를 연속으로 한 번에 재생.
    Safari/iOS 계열에서 연속 autoplay가 까다로운 편이라,
    같은 HTML 블록에서 audio onended 체인으로 처리.
    """
    tts_b64 = base64.b64encode(tts_bytes).decode("utf-8")
    tts_src = f"data:audio/mpeg;base64,{tts_b64}"

    if alarm_bytes:
        alarm_b64 = base64.b64encode(alarm_bytes).decode("utf-8")
        alarm_src = f"data:audio/mpeg;base64,{alarm_b64}"

        html = f"""
        <div>
          <audio id="hibuddy_alarm" autoplay>
            <source src="{alarm_src}" type="audio/mpeg" />
          </audio>
          <audio id="hibuddy_tts">
            <source src="{tts_src}" type="audio/mpeg" />
          </audio>
          <script>
            (function() {{
              const a = document.getElementById("hibuddy_alarm");
              const t = document.getElementById("hibuddy_tts");
              if (!a || !t) return;

              a.onended = function() {{
                try {{ t.play(); }} catch (e) {{}}
              }};

              // 알람이 어떤 이유로 재생 실패하면, 짧게 기다렸다가 TTS라도 재생 시도
              setTimeout(function() {{
                try {{
                  if (a.paused) {{ t.play(); }}
                }} catch (e) {{}}
              }}, 800);
            }})();
          </script>
        </div>
        """
        st.components.v1.html(html, height=0)
    else:
        # 알람 파일 없으면 TTS만 autoplay
        html = f"""
        <audio autoplay="true">
          <source src="{tts_src}" type="audio/mpeg">
        </audio>
        """
        st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 슬롯 TTS 텍스트 구성
# ─────────────────────────────────────────────
def _build_slot_tts_text(slot: Dict) -> str:
    """슬롯의 '요약 안내' 문장을 만든다."""
    slot_type = (slot.get("type") or "").upper()
    task = (slot.get("task") or "").strip()

    if slot_type == "MORNING_BRIEFING":
        head = "지금은 아침 준비 시간이에요."
    elif slot_type == "COOKING":
        head = "지금은 요리하고 밥을 먹는 시간이에요."
    elif slot_type == "HEALTH":
        head = "지금은 운동하고 건강을 챙기는 시간이에요."
    elif slot_type == "CLOTHING":
        head = "지금은 옷 입기 연습 시간이에요."
    elif slot_type == "NIGHT_WRAPUP":
        head = "지금은 오늘 하루를 마무리하는 시간이에요."
    else:
        head = "지금은 활동 시간이에요."

    parts = [head]
    if task:
        parts.append(f"이번 활동은 {task} 입니다.")

    guide = slot.get("guide_script")
    if isinstance(guide, list) and len(guide) > 0:
        first = str(guide[0]).strip()
        if first:
            parts.append(first)

    return " ".join(parts).strip()


def _join_lines_for_tts(lines: List[str], prefix: str = "") -> str:
    """
    단계/안내 문장을 '한 번에 쭉' 읽기 좋게 합친다.
    """
    clean = []
    for i, line in enumerate(lines, start=1):
        s = str(line).strip()
        if not s:
            continue
        # 너무 길면 끊어 읽기 좋게 약간 가공(최소)
        clean.append(f"{i}단계. {s}")
    if not clean:
        return prefix.strip()
    if prefix.strip():
        return prefix.strip() + " " + " ".join(clean)
    return " ".join(clean)


def _build_full_narration_text(slot: Dict) -> str:
    """
    '알람 뒤에 한 번에 쭉 읽어줄' 전체 안내 텍스트를 만든다.
    - 요약 + 상세(guide_script 전체)
    - COOKING/HEALTH이면 가능한 범위에서 추가 상세(레시피/루틴)
    """
    slot_type = (slot.get("type") or "").upper()

    # 1) 요약
    summary = _build_slot_tts_text(slot)

    # 2) 상세(guide_script 전체)
    guide_lines: List[str] = []
    guide = slot.get("guide_script")
    if isinstance(guide, list):
        guide_lines = [str(x) for x in guide if str(x).strip()]

    detail = ""
    if guide_lines:
        detail = _join_lines_for_tts(guide_lines, prefix="자세한 안내를 드릴게요.")

    # 3) 타입별 추가 상세(선택적으로)
    extra = ""

    if slot_type == "COOKING":
        # 선택된 메뉴가 있으면 레시피를 '한 번에' 안내
        sel_key = f"selected_menu_{_make_slot_key(st.session_state.get('schedule_date_str', ''), slot)}"
        chosen = st.session_state.get(sel_key, "")
        if chosen:
            recipe = get_recipe(chosen)
            if recipe:
                steps = recipe.get("steps") or recipe.get("guide_script") or []
                tools = recipe.get("tools") or []
                ings = recipe.get("ingredients") or []
                parts = [f"선택한 메뉴는 {chosen} 입니다."]
                if tools:
                    parts.append("준비물은 " + ", ".join([str(x) for x in tools if str(x).strip()]) + " 입니다.")
                if ings:
                    parts.append("재료는 " + ", ".join([str(x) for x in ings if str(x).strip()]) + " 입니다.")
                if isinstance(steps, list) and steps:
                    parts.append(_join_lines_for_tts([str(x) for x in steps], prefix="이제 조리 방법을 안내할게요."))
                extra = " ".join(parts).strip()
        else:
            # 메뉴를 아직 안 골랐으면 안내만
            extra = "메뉴를 선택한 뒤에, 레시피 안내가 자동으로 더 자세히 나와요."

    if slot_type == "HEALTH":
        # 기본 루틴(앉아서)로 한 번에 안내 + 이후 단계별 다시 듣기 가능
        routine_id = st.session_state.get("health_routine_id", "seated")
        routine = get_health_routine(routine_id)
        if routine:
            steps = routine.get("steps") or []
            title = routine.get("title") or ("앉아서 하는 운동" if routine_id == "seated" else "서서 하는 운동")
            if isinstance(steps, list) and steps:
                extra = f"{title} 루틴으로 안내할게요. " + _join_lines_for_tts([str(x) for x in steps])

    # 최종 합치기
    parts_all = [summary]
    if detail:
        parts_all.append(detail)
    if extra:
        parts_all.append(extra)

    return " ".join([p for p in parts_all if p]).strip()


# ─────────────────────────────────────────────
# 오디오 언락(UI)
# ─────────────────────────────────────────────
def _render_audio_unlock_ui():
    """
    모바일 브라우저 자동재생 정책 대응:
    최초 1회 사용자가 '소리 켜기'를 눌러야 안정적으로 알람/TTS autoplay가 동작한다.
    """
    if "audio_unlocked" not in st.session_state:
        st.session_state["audio_unlocked"] = False

    if st.session_state["audio_unlocked"]:
        return

    st.info("모바일에서는 자동으로 소리가 안 나올 수 있어요. 아래 버튼을 한 번 눌러서 소리를 켜 주세요.")
    if st.button("소리 켜기", key="btn_unlock_audio"):
        st.session_state["audio_unlocked"] = True
        # 사용자 제스처(버튼 클릭) 타이밍에 무음 오디오를 1번 재생해서 컨텍스트를 열어둔다.
        st.audio(_make_silence_wav(), format="audio/wav")
        st.success("소리가 켜졌어요. 이제 일정 시간이 되면 알람과 안내 음성이 자동으로 나와요.")


# ─────────────────────────────────────────────
# 자동 알림/TTS 로직
# ─────────────────────────────────────────────
def _auto_tts_logic(now: datetime, date_str: str, active: Optional[Dict], next_item: Optional[Dict]):
    """
    자동 재생(알람+TTS) 관련 로직.
    - 오늘 날짜 스케줄일 때만 동작
    - audio_unlocked가 True일 때만 autoplay 시도
    - 슬롯 시작 시: 알람 → 전체 안내를 한 번에 '쭉' (1회)
    - 5분 전 예고: (원하면 유지)
    """
    # 스케줄 날짜 체크
    try:
        sched_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        # date_str 파싱 실패면 안전하게 자동재생 끔
        return

    if sched_date != now.date():
        return

    # 모바일 autoplay 대응: 오디오 언락 전에는 자동재생 시도하지 않음
    if not st.session_state.get("audio_unlocked", False):
        return

    # 세션 플래그 초기화
    if "greeting_tts_done" not in st.session_state:
        st.session_state["greeting_tts_done"] = False
    if "last_tts_slot_key" not in st.session_state:
        st.session_state["last_tts_slot_key"] = ""
    if "last_pre_notice_slot_key" not in st.session_state:
        st.session_state["last_pre_notice_slot_key"] = ""
    if "full_narrated_slot_key" not in st.session_state:
        st.session_state["full_narrated_slot_key"] = ""

    # 1) 첫 진입 인사(하루 1번) - 유지
    if not st.session_state["greeting_tts_done"]:
        hour = now.hour
        if hour < 12:
            greeting = "좋은 아침이에요."
        elif hour < 18:
            greeting = "좋은 오후예요."
        else:
            greeting = "좋은 저녁이에요."

        base = f"{greeting} 오늘도 하이버디랑 함께 해볼까요?"
        if active:
            base = base + " " + _build_slot_tts_text(active)

        # 인사는 알람 없이 TTS만
        _play_tts_auto(base)
        st.session_state["greeting_tts_done"] = True
        return

    # 2) 슬롯 시작(변경) 감지 → 알람 + 전체 안내(한 번에 쭉)
    if active:
        current_key = _make_slot_key(date_str, active)

        # 기존 "슬롯 변경 시 요약만"이 아니라,
        # 전체 안내를 '한 번에 쭉' 읽는 걸 우선으로 한다.
        if st.session_state["full_narrated_slot_key"] != current_key:
            # 알람 bytes (없으면 None)
            alarm_bytes = _read_bytes(ALARM_SOUND_PATH)

            # 전체 안내 텍스트 생성 → TTS 1회 생성
            full_text = "띵동! 알림이 왔습니다. " + _build_full_narration_text(active)
            tts_bytes = synthesize_tts(full_text)
            if tts_bytes:
                _play_alarm_then_tts(alarm_bytes, tts_bytes)

            st.session_state["full_narrated_slot_key"] = current_key
            st.session_state["last_tts_slot_key"] = current_key
            return

    # 3) 다음 활동 5분 전 예고(원하면 유지)
    if next_item:
        try:
            hhmm = str(next_item.get("time", "")).strip()
            next_dt = datetime.combine(now.date(), datetime.strptime(hhmm, "%H:%M").time()).replace(tzinfo=KST)
            diff_min = (next_dt - now).total_seconds() / 60.0
        except Exception:
            return

        next_key = _make_slot_key(date_str, next_item)
        if 0 < diff_min <= PRE_NOTICE_MINUTES and st.session_state["last_pre_notice_slot_key"] != next_key:
            pre_text = f"{next_item.get('time','')}에 시작하는 활동을 준비해 볼까요? " + _build_slot_tts_text(next_item)
            _play_tts_auto(pre_text)
            st.session_state["last_pre_notice_slot_key"] = next_key
            return


# ─────────────────────────────────────────────
# “단계 클릭 강제”를 줄인 상세 표시/재생 UI
# ─────────────────────────────────────────────
def _render_steps_with_listen(lines: List[str], base_key: str, title: str = "자세한 단계"):
    """
    단계들을 전부 보여주고, 각 단계별로 '다시 듣기' 버튼 제공.
    (사용자가 '다음'을 눌러야만 진행되는 구조를 최소화)
    """
    if not lines:
        st.info("표시할 단계가 없습니다.")
        return

    st.subheader(title)

    # 전체 다시 듣기
    all_text = _join_lines_for_tts(lines, prefix="전체 단계를 다시 안내할게요.")
    _tts_button(all_text, key=f"{base_key}_listen_all", label="🔊 전체 안내 다시 듣기")

    # 단계별 다시 듣기
    with st.expander("단계별 다시 듣기", expanded=True):
        for idx, line in enumerate(lines, start=1):
            s = str(line).strip()
            if not s:
                continue
            col1, col2 = st.columns([0.82, 0.18])
            with col1:
                st.markdown(f"**{idx}단계**  \n{s}")
            with col2:
                _tts_button(f"{idx}단계. {s}", key=f"{base_key}_step_{idx}", label="🔊")


# ─────────────────────────────────────────────
# 각 타입별 뷰
# ─────────────────────────────────────────────
def _get_menu_image_url(menu_name: str, slot: Dict) -> str:
    """
    메뉴 이미지 URL을 구한다.
    우선순위: slot 내 image_map/menu_images → 없으면 Unsplash fallback
    """
    image_map = slot.get("menu_images") or slot.get("image_map") or {}
    if isinstance(image_map, dict) and menu_name in image_map:
        return str(image_map[menu_name])

    # Unsplash fallback
    q = urlquote(menu_name)
    return f"https://source.unsplash.com/featured/?food,{q}"


def _render_cooking_view(slot: Dict, date_str: str):
    st.header("요리하기")

    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        _render_steps_with_listen([str(x) for x in guide], base_key=f"cook_{_make_slot_key(date_str, slot)}", title="오늘 요리 안내")

    # 메뉴 선택 UI
    menus = slot.get("menus") or slot.get("menu_candidates") or []
    if not isinstance(menus, list):
        menus = []

    slot_key = _make_slot_key(date_str, slot)
    sel_key = f"selected_menu_{slot_key}"

    if menus:
        st.subheader("메뉴 선택")
        cols = st.columns(min(3, len(menus)))
        for i, name in enumerate(menus[:9]):  # 메뉴 카드는 너무 많아지지 않게 제한
            with cols[i % len(cols)]:
                img = _get_menu_image_url(str(name), slot)
                st.image(img, use_container_width=True)
                if st.button(f"'{name}' 선택", key=f"btn_sel_menu_{slot_key}_{i}"):
                    st.session_state[sel_key] = str(name)

        chosen = st.session_state.get(sel_key, "")
        if chosen:
            st.success(f"선택된 메뉴: {chosen}")

            # 영상
            video_url = ""
            videos = slot.get("videos") or slot.get("video_urls") or {}
            if isinstance(videos, dict):
                video_url = str(videos.get(chosen, "")) if chosen in videos else ""
            if not video_url:
                video_url = str(slot.get("video_url", "") or "")

            if video_url:
                st.video(video_url)

            # 레시피 표시 + 단계별 듣기
            recipe = get_recipe(chosen)
            if recipe:
                tools = recipe.get("tools") or []
                ings = recipe.get("ingredients") or []
                steps = recipe.get("steps") or recipe.get("guide_script") or []

                if tools:
                    st.subheader("준비물")
                    st.write("• " + "\n• ".join([str(x) for x in tools if str(x).strip()]))

                if ings:
                    st.subheader("재료")
                    st.write("• " + "\n• ".join([str(x) for x in ings if str(x).strip()]))

                if isinstance(steps, list) and steps:
                    _render_steps_with_listen([str(x) for x in steps], base_key=f"recipe_{slot_key}", title="레시피 단계")
            else:
                st.info("이 메뉴의 상세 레시피가 등록되어 있지 않아요.")
    else:
        st.info("메뉴 후보가 없습니다.")


def _render_health_view(slot: Dict, date_str: str):
    st.header("운동하기")

    video_url = str(slot.get("video_url", "") or "")
    if video_url:
        st.video(video_url)

    # 루틴 선택(선택은 자유지만, '단계 클릭 강제'는 없음)
    st.subheader("운동 방식 선택")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("앉아서 하는 운동", key="health_choose_seated"):
            st.session_state["health_routine_id"] = "seated"
    with c2:
        if st.button("서서 하는 운동", key="health_choose_standing"):
            st.session_state["health_routine_id"] = "standing"

    routine_id = st.session_state.get("health_routine_id", "seated")
    routine = get_health_routine(routine_id)
    if routine:
        title = routine.get("title") or ("앉아서 하는 운동" if routine_id == "seated" else "서서 하는 운동")
        steps = routine.get("steps") or []
        if isinstance(steps, list) and steps:
            _render_steps_with_listen([str(x) for x in steps], base_key=f"health_{routine_id}_{_make_slot_key(date_str, slot)}", title=title)
    else:
        st.info("운동 루틴을 불러오지 못했습니다.")

    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        st.divider()
        _render_steps_with_listen([str(x) for x in guide], base_key=f"health_guide_{_make_slot_key(date_str, slot)}", title="추가 안내")


def _render_clothing_view(slot: Dict, date_str: str):
    st.header("옷 입기 연습")

    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        _render_steps_with_listen([str(x) for x in guide], base_key=f"cloth_{_make_slot_key(date_str, slot)}", title="옷 입기 안내")

    video_url = str(slot.get("video_url", "") or "")
    if video_url:
        st.video(video_url)
    else:
        st.info("추천 영상이 없어요.")


def _render_general_view(slot: Dict, date_str: str, title: str):
    st.header(title)
    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        _render_steps_with_listen([str(x) for x in guide], base_key=f"gen_{_make_slot_key(date_str, slot)}", title="안내")


# ─────────────────────────────────────────────
# 메인 페이지
# ─────────────────────────────────────────────
def user_page():
    st.set_page_config(
        page_title="HiBuddy · 사용자 오늘 따라하기",
        page_icon="🧩",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    render_topbar()

    # 자동 새로고침
    st_autorefresh(interval=AUTO_REFRESH_SEC * 1000, key="hibuddy_autorefresh")

    # 오디오 언락 UI (모바일 대응)
    _render_audio_unlock_ui()

    schedule, date_str = _load_schedule()
    st.session_state["schedule_date_str"] = date_str  # 다른 함수에서 참조용

    if not schedule:
        st.warning("오늘 일정이 비어있습니다. 코디네이터 페이지에서 일정을 추가해 주세요.")
        return

    now = datetime.now(KST)
    now_time = now.time()   # ✅ datetime.time 객체

    active, next_item = find_active_item(schedule, now_time)
    annotated = annotate_schedule_with_status(schedule, now_time)


    # 자동 알람 + 전체 안내(TTS)
    _auto_tts_logic(now, date_str, active, next_item)

    # ─────────────────────────────────────────────
    # 레이아웃
    # ─────────────────────────────────────────────
    main_col, side_col = st.columns([0.72, 0.28])

    with main_col:
        st.markdown(f"### 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        if not active:
            st.info("아직 첫 활동 전이에요.")
            if next_item:
                st.markdown(f"다음 활동은 **{next_item.get('time','')} · {next_item.get('task','')}** 입니다.")
                _tts_button(
                    f"다음 활동은 {next_item.get('time','')}에 시작하는 {next_item.get('task','')} 입니다.",
                    key="tts_next_preview",
                    label="🔊 다음 활동 듣기",
                )
            return

        slot_type = (active.get("type") or "").upper()
        task = str(active.get("task") or "").strip()

        # 상단 요약(버튼으로 다시 듣기 가능)
        header_text = {
            "MORNING_BRIEFING": "아침 준비",
            "COOKING": "요리/식사",
            "HEALTH": "운동",
            "CLOTHING": "옷 입기",
            "NIGHT_WRAPUP": "마무리",
        }.get(slot_type, "활동")

        st.markdown(f"## {header_text}")
        if task:
            st.markdown(f"**오늘 할 일:** {task}")

        today_task_text = f"{header_text} 시간이에요. 오늘 할 일은 {task} 입니다." if task else f"{header_text} 시간이에요."
        _tts_button(today_task_text, key="tts_today_task", label="🔊 현재 활동 요약 듣기")

        st.divider()

        # 타입별 화면
        if slot_type == "COOKING":
            _render_cooking_view(active, date_str)
        elif slot_type == "HEALTH":
            _render_health_view(active, date_str)
        elif slot_type == "CLOTHING":
            _render_clothing_view(active, date_str)
        elif slot_type == "MORNING_BRIEFING":
            _render_general_view(active, date_str, "아침 준비")
        elif slot_type == "NIGHT_WRAPUP":
            _render_general_view(active, date_str, "하루 마무리")
        else:
            _render_general_view(active, date_str, "활동")

        # 전체 안내 다시 듣기(현재 슬롯 기준)
        st.divider()
        if st.session_state.get("audio_unlocked", False):
            if st.button("🔊 (현재 슬롯) 전체 안내 다시 듣기", key="btn_repeat_full_narration"):
                full_text = "띵동! 알림이 왔습니다. " + _build_full_narration_text(active)
                audio_bytes = synthesize_tts(full_text)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mpeg")

    with side_col:
        st.markdown("### 다음 활동")
        if next_item:
            st.write(f"{next_item.get('time','')} · {next_item.get('task','')}")
        else:
            st.write("다음 활동이 없습니다.")

        st.divider()
        st.markdown("### 오늘 타임라인")
        for item in annotated:
            t = item.get("time", "")
            ty = item.get("type", "")
            tk = item.get("task", "")
            status = item.get("status", "")

            if status == "active":
                st.success(f"{t} · {tk} ({ty})")
            elif status == "past":
                st.caption(f"{t} · {tk} ({ty})")
            else:
                st.write(f"{t} · {tk} ({ty})")

        st.divider()
        if st.button("화면 수동 새로고침", key="btn_rerun"):
            st.rerun()


if __name__ == "__main__":
    user_page()
