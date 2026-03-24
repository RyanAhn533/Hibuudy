# pages/2_사용자_오늘_따라하기.py
# -*- coding: utf-8 -*-
import base64
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

from urllib.parse import quote as urlquote

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from utils.topbar import render_topbar
from utils.runtime import find_active_item, annotate_schedule_with_status
from utils.recipes import get_recipe, get_health_routine
from utils.tts import synthesize_tts
from utils.styles import get_activity_css_class, get_activity_emoji, COLORS

# ─────────────────────────────────────────────
# 타임존 설정 (Asia/Seoul 고정)
# ─────────────────────────────────────────────
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

KST = ZoneInfo("Asia/Seoul")

SCHEDULE_PATH = os.path.join("data", "schedule_today.json")

AUTO_REFRESH_SEC = 30
PRE_NOTICE_MINUTES = 5

ALARM_SOUND_PATH = os.path.join("assets", "sounds", "alarm.mp3")

# 타입별 한글 헤더
HEADER_TEXT_MAP = {
    "MORNING_BRIEFING": "아침 준비",
    "COOKING": "요리/식사",
    "MEAL": "요리/식사",
    "HEALTH": "운동",
    "REST": "쉬는 시간",
    "LEISURE": "여가",
    "CLOTHING": "옷 입기",
    "NIGHT_WRAPUP": "마무리",
}


# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────
def _load_schedule() -> Tuple[List[Dict], str]:
    if not os.path.exists(SCHEDULE_PATH):
        st.error("오늘 스케줄 파일이 없습니다. 일정 만들기 페이지에서 먼저 저장해 주세요.")
        st.stop()

    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    date_str = data.get("date") or data.get("date_str") or ""
    schedule = data.get("schedule", [])
    if not isinstance(schedule, list):
        schedule = []

    schedule = sorted(schedule, key=lambda it: str(it.get("time", "00:00")))
    return schedule, date_str


def _read_bytes(path: str) -> Optional[bytes]:
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


def _make_silence_wav(duration_sec: float = 0.2, sample_rate: int = 8000) -> bytes:
    import struct

    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    num_samples = int(sample_rate * duration_sec)
    data_size = num_samples * block_align

    riff = b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVE"
    fmt = (
        b"fmt "
        + struct.pack("<I", 16)
        + struct.pack("<H", 1)
        + struct.pack("<H", num_channels)
        + struct.pack("<I", sample_rate)
        + struct.pack("<I", byte_rate)
        + struct.pack("<H", block_align)
        + struct.pack("<H", bits_per_sample)
    )
    data = b"data" + struct.pack("<I", data_size) + (b"\x00\x00" * num_samples)
    return riff + fmt + data


def _tts_button(text: str, key: str, label: str = "🔊 듣기"):
    if st.button(label, key=key):
        audio_bytes = synthesize_tts(text)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mpeg")


def _join_lines_for_tts(lines: List[str], prefix: str = "") -> str:
    clean = []
    for i, line in enumerate(lines, start=1):
        s = str(line).strip()
        if not s:
            continue
        clean.append(f"{i}단계. {s}")
    if not clean:
        return prefix.strip()
    if prefix.strip():
        return prefix.strip() + " " + " ".join(clean)
    return " ".join(clean)


def _build_slot_tts_text(slot: Dict) -> str:
    slot_type = (slot.get("type") or "").upper()
    task = (slot.get("task") or "").strip()

    head_map = {
        "MORNING_BRIEFING": "지금은 아침 준비 시간이에요.",
        "COOKING": "지금은 요리하고 밥을 먹는 시간이에요.",
        "HEALTH": "지금은 운동하고 건강을 챙기는 시간이에요.",
        "CLOTHING": "지금은 옷 입기 연습 시간이에요.",
        "NIGHT_WRAPUP": "지금은 오늘 하루를 마무리하는 시간이에요.",
    }
    head = head_map.get(slot_type, "지금은 활동 시간이에요.")

    parts = [head]
    if task:
        parts.append(f"이번 활동은 {task} 입니다.")

    guide = slot.get("guide_script")
    if isinstance(guide, list) and guide:
        first = str(guide[0]).strip()
        if first:
            parts.append(first)

    return " ".join(parts).strip()


def _build_full_narration_text(slot: Dict) -> str:
    slot_type = (slot.get("type") or "").upper()
    summary = _build_slot_tts_text(slot)

    guide_lines: List[str] = []
    guide = slot.get("guide_script")
    if isinstance(guide, list):
        guide_lines = [str(x) for x in guide if str(x).strip()]

    detail = ""
    if guide_lines:
        detail = _join_lines_for_tts(guide_lines, prefix="자세한 안내를 드릴게요.")

    extra = ""
    if slot_type == "COOKING":
        chosen = st.session_state.get("selected_menu_for_js", "")
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

    if slot_type == "HEALTH":
        routine_id = st.session_state.get("health_routine_id", "seated")
        routine = get_health_routine(routine_id)
        if routine:
            steps = routine.get("steps") or []
            title = routine.get("title") or ("앉아서 하는 운동" if routine_id == "seated" else "서서 하는 운동")
            if isinstance(steps, list) and steps:
                extra = f"{title} 루틴으로 안내할게요. " + _join_lines_for_tts([str(x) for x in steps])

    parts_all = [summary]
    if detail:
        parts_all.append(detail)
    if extra:
        parts_all.append(extra)

    return " ".join([p for p in parts_all if p]).strip()


# ─────────────────────────────────────────────
# 오디오 언락(UI) - 모바일 autoplay 대응
# ─────────────────────────────────────────────
def _render_audio_unlock_ui():
    if "audio_unlocked" not in st.session_state:
        st.session_state["audio_unlocked"] = False

    if st.session_state["audio_unlocked"]:
        return

    st.markdown(
        f"""
        <div class="hb-card" style="border-left: 5px solid {COLORS['warning']}; background: #FFFBEB;">
            <strong>🔔 모바일에서 소리 켜기</strong><br>
            모바일에서는 자동으로 소리가 안 나올 수 있어요.<br>
            아래 버튼을 한 번 눌러서 소리를 켜 주세요.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🔊 소리 켜기", key="btn_unlock_audio"):
        st.session_state["audio_unlocked"] = True
        st.audio(_make_silence_wav(), format="audio/wav")
        st.success("소리가 켜졌어요!")


# ─────────────────────────────────────────────
# JS 스케줄러를 위한 "오디오 맵" 생성
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _prepare_audio_payloads(schedule: List[Dict], date_str: str) -> Dict:
    alarm_bytes = _read_bytes(ALARM_SOUND_PATH)
    alarm_b64 = base64.b64encode(alarm_bytes).decode("utf-8") if alarm_bytes else ""

    items: Dict[str, Dict[str, str]] = {}

    for slot in schedule:
        hhmm = str(slot.get("time", "")).strip()
        if not hhmm:
            continue

        full_text = "띵동! 알림이 왔습니다. " + _build_full_narration_text(slot)
        tts_bytes = synthesize_tts(full_text) or b""
        if tts_bytes:
            items[hhmm] = {
                "tts_b64": base64.b64encode(tts_bytes).decode("utf-8"),
                "text": full_text,
            }

    if PRE_NOTICE_MINUTES and PRE_NOTICE_MINUTES > 0:
        for slot in schedule:
            hhmm = str(slot.get("time", "")).strip()
            if not hhmm:
                continue
            try:
                dt = datetime.strptime(f"{date_str} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=KST)
            except Exception:
                continue
            pre_dt = dt - timedelta(minutes=PRE_NOTICE_MINUTES)
            pre_key = pre_dt.strftime("%H:%M") + "_PRE"
            pre_text = f"{hhmm}에 시작하는 활동을 준비해 볼까요? " + _build_slot_tts_text(slot)
            tts_bytes = synthesize_tts(pre_text) or b""
            if tts_bytes:
                items[pre_key] = {
                    "tts_b64": base64.b64encode(tts_bytes).decode("utf-8"),
                    "text": pre_text,
                }

    return {"date": date_str, "alarm_b64": alarm_b64, "items": items}


def _render_js_alarm_scheduler(payload: Dict):
    data_json = json.dumps(payload, ensure_ascii=False)
    enabled = "true" if st.session_state.get("audio_unlocked", False) else "false"

    html = f"""
    <script>
    (function() {{
      const ENABLED = {enabled};
      if (!ENABLED) return;

      const payload = {data_json};
      const items = payload.items || {{}};
      const dateStr = payload.date || "";

      function nowKST() {{
        const d = new Date();
        const hh = String(d.getHours()).padStart(2, '0');
        const mm = String(d.getMinutes()).padStart(2, '0');
        return hh + ":" + mm;
      }}

      function todayKeyBase() {{
        return "hibuddy_played_" + dateStr + "_";
      }}

      function wasPlayed(key) {{
        try {{ return localStorage.getItem(todayKeyBase() + key) === "1"; }}
        catch (e) {{ return false; }}
      }}

      function markPlayed(key) {{
        try {{ localStorage.setItem(todayKeyBase() + key, "1"); }}
        catch (e) {{}}
      }}

      function b64ToUrl(b64, mime) {{
        return "data:" + mime + ";base64," + b64;
      }}

      const alarmB64 = payload.alarm_b64 || "";
      const alarmUrl = alarmB64 ? b64ToUrl(alarmB64, "audio/mpeg") : "";

      function playSequence(alarmUrl, ttsUrl) {{
        return new Promise((resolve) => {{
          function playTts() {{
            const t = new Audio(ttsUrl);
            t.onended = () => resolve(true);
            t.onerror = () => resolve(false);
            t.play().catch(() => resolve(false));
          }}

          if (!alarmUrl) {{ playTts(); return; }}

          const a = new Audio(alarmUrl);
          a.onended = () => playTts();
          a.onerror = () => playTts();
          a.play().catch(() => playTts());
        }});
      }}

      async function tick() {{
        const hhmm = nowKST();

        if (items[hhmm] && !wasPlayed(hhmm)) {{
          const ttsB64 = items[hhmm].tts_b64 || "";
          if (ttsB64) {{
            markPlayed(hhmm);
            await playSequence(alarmUrl, b64ToUrl(ttsB64, "audio/mpeg"));
          }}
        }}

        const preKey = hhmm + "_PRE";
        if (items[preKey] && !wasPlayed(preKey)) {{
          const ttsB64 = items[preKey].tts_b64 || "";
          if (ttsB64) {{
            markPlayed(preKey);
            await playSequence("", b64ToUrl(ttsB64, "audio/mpeg"));
          }}
        }}
      }}

      tick();
      setInterval(tick, 1000);
    }})();
    </script>
    """
    st.components.v1.html(html, height=0)


# ─────────────────────────────────────────────
# 단계 렌더링 (리디자인)
# ─────────────────────────────────────────────
def _render_steps_with_listen(lines: List[str], base_key: str, title: str = "자세한 단계", color: str = ""):
    if not lines:
        st.info("표시할 단계가 없습니다.")
        return

    step_color = color or COLORS["primary"]

    st.subheader(title)

    all_text = _join_lines_for_tts(lines, prefix="전체 단계를 다시 안내할게요.")
    _tts_button(all_text, key=f"{base_key}_listen_all", label="🔊 전체 안내 다시 듣기")

    with st.expander("단계별 다시 듣기", expanded=True):
        for idx, line in enumerate(lines, start=1):
            s = str(line).strip()
            if not s:
                continue
            st.markdown(
                f"""
                <div class="hb-recipe-step">
                    <div class="hb-recipe-step-num" style="background: {step_color};">{idx}</div>
                    <div style="flex:1; color: {COLORS['text']};">{s}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            _tts_button(f"{idx}단계. {s}", key=f"{base_key}_step_{idx}", label="🔊")


def _get_menu_image_url(menu_name: str, slot: Dict) -> str:
    image_map = slot.get("menu_images") or slot.get("image_map") or {}
    if isinstance(image_map, dict) and menu_name in image_map:
        return str(image_map[menu_name])
    q = urlquote(menu_name)
    return f"https://source.unsplash.com/featured/?food,{q}"


def _normalize_menus(slot: Dict) -> List[Dict]:
    menus = slot.get("menus") or slot.get("menu_candidates") or []
    out: List[Dict] = []

    if not isinstance(menus, list):
        return out

    for m in menus:
        if isinstance(m, dict):
            name = str(m.get("name", "")).strip()
            image = str(m.get("image", "")).strip()
            video_url = str(m.get("video_url", "")).strip()
            if name:
                out.append({"name": name, "image": image, "video_url": video_url})
        else:
            name = str(m).strip()
            if name:
                out.append({"name": name, "image": "", "video_url": ""})

    return out


# ─────────────────────────────────────────────
# 활동 헤더 (색상 카드)
# ─────────────────────────────────────────────
def _render_activity_header(slot_type: str, task: str):
    css_class = get_activity_css_class(slot_type)
    emoji = get_activity_emoji(slot_type)
    header = HEADER_TEXT_MAP.get(slot_type.upper(), "활동")

    st.markdown(
        f"""
        <div class="hb-activity-header hb-activity-{css_class}">
            <h2>{emoji} {header}</h2>
            <p>{task}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# 활동별 뷰
# ─────────────────────────────────────────────
def _render_cooking_view(slot: Dict, date_str: str):
    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        _render_steps_with_listen(
            [str(x) for x in guide],
            base_key=f"cook_{date_str}_{slot.get('time','')}",
            title="오늘 요리 안내",
            color=COLORS["cooking"],
        )

    menus = _normalize_menus(slot)

    if menus:
        st.markdown(f'<div class="hb-section-title">메뉴 선택</div>', unsafe_allow_html=True)
        cols = st.columns(min(3, len(menus)))
        for i, m in enumerate(menus[:9]):
            name = m["name"]
            with cols[i % len(cols)]:
                img = m["image"] or _get_menu_image_url(name, slot)
                st.image(img, use_container_width=True)
                if st.button(f"'{name}' 선택", key=f"btn_sel_menu_{date_str}_{slot.get('time','')}_{i}"):
                    st.session_state["selected_menu_for_js"] = name

        chosen = st.session_state.get("selected_menu_for_js", "")
        if chosen:
            st.markdown(
                f"""
                <div class="hb-card hb-card-cooking">
                    <strong>🍳 선택된 메뉴: {chosen}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 영상 표시
            video_url = ""
            menus_list = slot.get("menus") or slot.get("menu_candidates") or []
            chosen_obj = None
            if isinstance(menus_list, list):
                for m in menus_list:
                    if isinstance(m, dict) and str(m.get("name", "")).strip() == str(chosen).strip():
                        chosen_obj = m
                        break

            if chosen_obj and chosen_obj.get("video_url"):
                video_url = str(chosen_obj.get("video_url") or "").strip()

            if not video_url:
                videos = slot.get("videos") or slot.get("video_urls") or {}
                if isinstance(videos, dict):
                    video_url = str(videos.get(chosen, "") or "").strip()

            if not video_url:
                video_url = str(slot.get("video_url", "") or "").strip()

            if video_url:
                st.video(video_url)

            recipe = get_recipe(chosen)
            if recipe:
                tools = recipe.get("tools") or []
                ings = recipe.get("ingredients") or []
                steps = recipe.get("steps") or recipe.get("guide_script") or []

                if tools:
                    st.markdown(f'<div class="hb-section-title">준비물</div>', unsafe_allow_html=True)
                    tool_html = " ".join(
                        [f'<span class="hb-badge hb-badge-cooking">{x}</span>' for x in tools if str(x).strip()]
                    )
                    st.markdown(tool_html, unsafe_allow_html=True)

                if ings:
                    st.markdown(f'<div class="hb-section-title">재료</div>', unsafe_allow_html=True)
                    ing_html = " ".join(
                        [f'<span class="hb-badge hb-badge-general">{x}</span>' for x in ings if str(x).strip()]
                    )
                    st.markdown(ing_html, unsafe_allow_html=True)

                if isinstance(steps, list) and steps:
                    _render_steps_with_listen(
                        [str(x) for x in steps],
                        base_key=f"recipe_{date_str}_{slot.get('time','')}",
                        title="레시피 단계",
                        color=COLORS["cooking"],
                    )
            else:
                st.markdown(
                    '<div class="hb-info">이 메뉴의 상세 레시피가 등록되어 있지 않아요.</div>',
                    unsafe_allow_html=True,
                )


def _render_health_view(slot: Dict, date_str: str):
    video_url = str(slot.get("video_url", "") or "")
    if video_url:
        st.video(video_url)

    st.markdown(f'<div class="hb-section-title">운동 방식 선택</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🪑 앉아서 하는 운동", key="health_choose_seated"):
            st.session_state["health_routine_id"] = "seated"
    with c2:
        if st.button("🧍 서서 하는 운동", key="health_choose_standing"):
            st.session_state["health_routine_id"] = "standing"

    routine_id = st.session_state.get("health_routine_id", "seated")
    routine = get_health_routine(routine_id)
    if routine:
        title = routine.get("title") or ("앉아서 하는 운동" if routine_id == "seated" else "서서 하는 운동")
        steps = routine.get("steps") or []
        if isinstance(steps, list) and steps:
            _render_steps_with_listen(
                [str(x) for x in steps],
                base_key=f"health_{routine_id}_{date_str}_{slot.get('time','')}",
                title=title,
                color=COLORS["health"],
            )
    else:
        st.info("운동 루틴을 불러오지 못했습니다.")

    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        st.divider()
        _render_steps_with_listen(
            [str(x) for x in guide],
            base_key=f"health_guide_{date_str}_{slot.get('time','')}",
            title="추가 안내",
            color=COLORS["health"],
        )


def _render_clothing_view(slot: Dict, date_str: str):
    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        _render_steps_with_listen(
            [str(x) for x in guide],
            base_key=f"cloth_{date_str}_{slot.get('time','')}",
            title="옷 입기 안내",
            color=COLORS["clothing"],
        )

    video_url = str(slot.get("video_url", "") or "")
    if video_url:
        st.video(video_url)
    else:
        st.markdown('<div class="hb-info">추천 영상이 없어요.</div>', unsafe_allow_html=True)


def _render_general_view(slot: Dict, date_str: str, title: str, color: str = ""):
    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        _render_steps_with_listen(
            [str(x) for x in guide],
            base_key=f"gen_{date_str}_{slot.get('time','')}",
            title="안내",
            color=color or COLORS["primary"],
        )


# ─────────────────────────────────────────────
# 타임라인 사이드바
# ─────────────────────────────────────────────
def _render_timeline(annotated: List[Dict]):
    st.markdown(f'<div class="hb-section-title">오늘 타임라인</div>', unsafe_allow_html=True)

    for item in annotated:
        t = item.get("time", "")
        ty = (item.get("type") or "").upper()
        tk = item.get("task", "")
        status = item.get("status", "")
        emoji = get_activity_emoji(ty)

        if status == "active":
            css = "hb-timeline-active"
            dot_css = "hb-timeline-dot-active"
        elif status == "past":
            css = "hb-timeline-past"
            dot_css = "hb-timeline-dot-past"
        else:
            css = "hb-timeline-upcoming"
            dot_css = "hb-timeline-dot-upcoming"

        st.markdown(
            f"""
            <div class="hb-timeline-item {css}">
                <div class="hb-timeline-dot {dot_css}"></div>
                <span>{emoji} <strong>{t}</strong> {tk}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────
# 메인 페이지
# ─────────────────────────────────────────────
def user_page():
    st.set_page_config(
        page_title="하루메이트 - 오늘 하루",
        page_icon="👋",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    render_topbar()

    st_autorefresh(interval=AUTO_REFRESH_SEC * 1000, key="hibuddy_autorefresh_ui")

    _render_audio_unlock_ui()

    schedule, date_str = _load_schedule()
    if not schedule:
        st.warning("오늘 일정이 비어있습니다. 일정 만들기 페이지에서 일정을 추가해 주세요.")
        return

    payload = _prepare_audio_payloads(schedule, date_str)
    _render_js_alarm_scheduler(payload)

    now = datetime.now(KST)
    now_time = now.time()
    active, next_item = find_active_item(schedule, now_time)
    annotated = annotate_schedule_with_status(schedule, now_time)

    # ── 레이아웃 ──
    main_col, side_col = st.columns([0.72, 0.28])

    with main_col:
        # 인사말 배너
        h = datetime.now(KST).hour
        if h < 12:
            greeting = "좋은 아침이에요"
            greeting_emoji = "🌅"
        elif h < 18:
            greeting = "좋은 오후예요"
            greeting_emoji = "☀️"
        else:
            greeting = "좋은 저녁이에요"
            greeting_emoji = "🌙"

        st.markdown(
            f"""
            <div class="hb-greeting">
                <h2>{greeting_emoji} {greeting}</h2>
                <p>오늘도 하루메이트랑 함께 해볼까요? &nbsp; {now.strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 수동 재생
        with st.expander("🔊 음성이 안 나오면 여기를 눌러주세요", expanded=False):
            _tts_button("지금부터 안내를 시작할게요.", key="tts_test_1", label="🔊 음성 허용 및 테스트")
            st.caption("모바일(iOS 등)에서는 '소리 켜기'를 한 번 눌러야 자동 재생이 안정적이에요.")

        if not active:
            st.markdown(
                '<div class="hb-info">아직 첫 활동 전이에요.</div>',
                unsafe_allow_html=True,
            )
            if next_item:
                st.markdown(f"다음 활동은 **{next_item.get('time','')} - {next_item.get('task','')}** 입니다.")
                _tts_button(
                    f"다음 활동은 {next_item.get('time','')}에 시작하는 {next_item.get('task','')} 입니다.",
                    key="tts_next_preview",
                    label="🔊 다음 활동 듣기",
                )
            return

        slot_type = (active.get("type") or "").upper()
        task = str(active.get("task") or "").strip()

        # 활동 헤더 (색상 카드)
        _render_activity_header(slot_type, task)

        today_task_text = f"{HEADER_TEXT_MAP.get(slot_type, '활동')} 시간이에요. 오늘 할 일은 {task} 입니다." if task else f"{HEADER_TEXT_MAP.get(slot_type, '활동')} 시간이에요."
        _tts_button(today_task_text, key="tts_today_task", label="🔊 현재 활동 요약 듣기")

        st.divider()

        # 활동별 뷰
        if slot_type in ("COOKING", "MEAL"):
            _render_cooking_view(active, date_str)
        elif slot_type == "HEALTH":
            _render_health_view(active, date_str)
        elif slot_type == "CLOTHING":
            _render_clothing_view(active, date_str)
        elif slot_type == "REST":
            _render_general_view(active, date_str, "쉬는 시간", COLORS["rest"])
        elif slot_type == "LEISURE":
            _render_general_view(active, date_str, "여가", COLORS["leisure"])
        elif slot_type == "MORNING_BRIEFING":
            _render_general_view(active, date_str, "아침 준비", COLORS["morning"])
        elif slot_type == "NIGHT_WRAPUP":
            _render_general_view(active, date_str, "하루 마무리", COLORS["night"])
        else:
            _render_general_view(active, date_str, "활동")

    with side_col:
        # 다음 활동
        st.markdown(f'<div class="hb-section-title">다음 활동</div>', unsafe_allow_html=True)
        if next_item:
            next_emoji = get_activity_emoji((next_item.get("type") or "").upper())
            st.markdown(
                f"""
                <div class="hb-card hb-card-accent">
                    <strong>{next_emoji} {next_item.get('time', '')} - {next_item.get('task', '')}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="hb-card">다음 활동이 없습니다.</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        _render_timeline(annotated)

        st.divider()
        if st.button("🔄 화면 새로고침", key="btn_rerun"):
            st.rerun()


if __name__ == "__main__":
    user_page()
