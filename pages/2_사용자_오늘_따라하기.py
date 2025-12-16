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
from utils.tts import synthesize_tts  # TTS 유틸

# ─────────────────────────────────────────────
# 타임존 설정 (Asia/Seoul 고정)
# ─────────────────────────────────────────────
try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python 3.8 이하
    from backports.zoneinfo import ZoneInfo  # type: ignore

KST = ZoneInfo("Asia/Seoul")

SCHEDULE_PATH = os.path.join("data", "schedule_today.json")

# UI는 느리게 새로고침(영상/상태 표시만 갱신)
# 정시 알람/음성은 JS가 1초 타이머로 처리하므로 여기는 낮출 필요 없음
AUTO_REFRESH_SEC = 30

# (선택) N분 전 예고도 JS에서 같이 처리
PRE_NOTICE_MINUTES = 5

ALARM_SOUND_PATH = os.path.join("assets", "sounds", "alarm.mp3")


# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────
def _load_schedule() -> Tuple[List[Dict], str]:
    if not os.path.exists(SCHEDULE_PATH):
        st.error("오늘 스케줄 파일이 없습니다. 코디네이터 페이지에서 먼저 저장해 주세요.")
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
        + struct.pack("<H", 1)  # PCM
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
    # COOKING: 선택 메뉴가 있으면 레시피까지 붙여서 “한 번에 쭉”
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
        else:
            # 메뉴 선택 전에도 기본 안내는 가능
            extra = ""

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

    st.info("모바일에서는 자동으로 소리가 안 나올 수 있어요. 아래 버튼을 한 번 눌러서 소리를 켜 주세요.")
    if st.button("소리 켜기", key="btn_unlock_audio"):
        st.session_state["audio_unlocked"] = True
        st.audio(_make_silence_wav(), format="audio/wav")
        st.success("소리가 켜졌어요. 이제 일정 시간이 되면 알람과 안내 음성이 자동으로 나와요.")


# ─────────────────────────────────────────────
# ✅ JS 스케줄러를 위한 “오디오 맵” 생성
#   - (중요) 정시 알람을 rerun 없이 재생하려면
#     스케줄별 TTS를 미리 만들어서 페이지에 넣어야 함
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _prepare_audio_payloads(schedule: List[Dict], date_str: str) -> Dict:
    """
    반환 형태:
    {
      "date": "YYYY-MM-DD",
      "alarm_b64": "... or ''",
      "items": {
        "HH:MM": {"tts_b64": "...", "text": "..."},
        "HH:MM_PRE": {"tts_b64": "...", "text": "..."}  # (옵션) N분전 예고
      }
    }
    """
    alarm_bytes = _read_bytes(ALARM_SOUND_PATH)
    alarm_b64 = base64.b64encode(alarm_bytes).decode("utf-8") if alarm_bytes else ""

    items: Dict[str, Dict[str, str]] = {}

    # 슬롯 시작 알림: "HH:MM" 키
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

    # (옵션) PRE_NOTICE: 다음 활동 N분 전 예고
    # JS는 '현재 시각' 기준으로 N분 뒤의 HH:MM을 만들어서 키 조회하면 됨
    # 여기서는 미리 "HH:MM_PRE"를 만들어 둠
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
    """
    - 1초마다 HH:MM 체크
    - payload.items["HH:MM"] 있으면:
        alarm(있으면) -> tts 순서로 재생
    - 같은 날 같은 HH:MM은 localStorage로 중복 재생 방지
    - audio_unlocked가 True일 때만 실행
    """
    # Streamlit 세션이 바뀌어도 “정시 중복재생” 막으려면 localStorage를 써야 함
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
        // 브라우저 로컬이 KST라고 가정(한국 기기). 타임존 강제는 웹에서 어렵다.
        // 대신 dateStr(스케줄 날짜) 기반으로 "오늘만" 재생되도록 막는다.
        const d = new Date();
        const hh = String(d.getHours()).padStart(2, '0');
        const mm = String(d.getMinutes()).padStart(2, '0');
        return hh + ":" + mm;
      }}

      function todayKeyBase() {{
        // 스케줄 날짜가 오늘이 아닐 때는 재생하지 않도록 base 키에 dateStr 포함
        return "hibuddy_played_" + dateStr + "_";
      }}

      function wasPlayed(key) {{
        try {{
          return localStorage.getItem(todayKeyBase() + key) === "1";
        }} catch (e) {{
          return false;
        }}
      }}

      function markPlayed(key) {{
        try {{
          localStorage.setItem(todayKeyBase() + key, "1");
        }} catch (e) {{}}
      }}

      function b64ToUrl(b64, mime) {{
        return "data:" + mime + ";base64," + b64;
      }}

      const alarmB64 = payload.alarm_b64 || "";
      const alarmUrl = alarmB64 ? b64ToUrl(alarmB64, "audio/mpeg") : "";

      function playSequence(alarmUrl, ttsUrl) {{
        // iOS/Safari에서 안전하게: 새 Audio 객체로 순차 재생
        return new Promise((resolve) => {{
          function playTts() {{
            const t = new Audio(ttsUrl);
            t.onended = () => resolve(true);
            t.onerror = () => resolve(false);
            t.play().catch(() => resolve(false));
          }}

          if (!alarmUrl) {{
            playTts();
            return;
          }}

          const a = new Audio(alarmUrl);
          a.onended = () => playTts();
          a.onerror = () => playTts(); // 알람 실패해도 TTS는 시도
          a.play().catch(() => playTts());
        }});
      }}

      async function tick() {{
        const hhmm = nowKST();

        // 1) 슬롯 시작 알림
        if (items[hhmm] && !wasPlayed(hhmm)) {{
          const ttsB64 = items[hhmm].tts_b64 || "";
          if (ttsB64) {{
            markPlayed(hhmm); // 먼저 찍어서 중복 방지(재생 실패해도 폭주 방지)
            await playSequence(alarmUrl, b64ToUrl(ttsB64, "audio/mpeg"));
          }}
        }}

        // 2) N분 전 예고 (옵션)
        const preKey = hhmm + "_PRE";
        if (items[preKey] && !wasPlayed(preKey)) {{
          const ttsB64 = items[preKey].tts_b64 || "";
          if (ttsB64) {{
            markPlayed(preKey);
            await playSequence("", b64ToUrl(ttsB64, "audio/mpeg"));
          }}
        }}
      }}

      // 즉시 1회, 이후 1초마다
      tick();
      setInterval(tick, 1000);
    }})();
    </script>
    """
    st.components.v1.html(html, height=0)


# ─────────────────────────────────────────────
# “단계 클릭 강제” 줄인 UI
# ─────────────────────────────────────────────
def _render_steps_with_listen(lines: List[str], base_key: str, title: str = "자세한 단계"):
    if not lines:
        st.info("표시할 단계가 없습니다.")
        return

    st.subheader(title)

    all_text = _join_lines_for_tts(lines, prefix="전체 단계를 다시 안내할게요.")
    _tts_button(all_text, key=f"{base_key}_listen_all", label="🔊 전체 안내 다시 듣기")

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


def _get_menu_image_url(menu_name: str, slot: Dict) -> str:
    image_map = slot.get("menu_images") or slot.get("image_map") or {}
    if isinstance(image_map, dict) and menu_name in image_map:
        return str(image_map[menu_name])
    q = urlquote(menu_name)
    return f"https://source.unsplash.com/featured/?food,{q}"

def _normalize_menus(slot: Dict) -> List[Dict]:
    """
    코디네이터 저장 포맷:
      menus = [{"name":..., "image":..., "video_url":...}, ...]
    과거/예전 포맷(문자열 리스트)도 같이 지원.
    반환: [{"name": str, "image": str, "video_url": str}, ...]
    """
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

def _render_cooking_view(slot: Dict, date_str: str):
    st.header("요리하기")

    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        _render_steps_with_listen([str(x) for x in guide], base_key=f"cook_{date_str}_{slot.get('time','')}", title="오늘 요리 안내")

    menus = _normalize_menus(slot)


    # NOTE: JS 알람용으로 "선택 메뉴"를 세션에 하나 더 저장(최소 변경)
    # - 기존 네 코드에서 menu selection key가 더 복잡하면 여기만 맞춰주면 됨
    if menus:
        st.subheader("메뉴 선택")
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
            st.success(f"선택된 메뉴: {chosen}")

            # ✅ 코디네이터 저장 포맷 우선 지원:
            # menus = [{"name":..., "image":..., "video_url":...}, ...]
            # chosen 메뉴에 해당하는 menu dict의 video_url을 가장 먼저 사용
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

            # ✅ 하위 호환: slot["videos"] / slot["video_urls"] 딕셔너리 매핑도 지원
            if not video_url:
                videos = slot.get("videos") or slot.get("video_urls") or {}
                if isinstance(videos, dict):
                    video_url = str(videos.get(chosen, "") or "").strip()

            # ✅ 최후 fallback: slot["video_url"]
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
                    st.subheader("준비물")
                    st.write("• " + "\n• ".join([str(x) for x in tools if str(x).strip()]))

                if ings:
                    st.subheader("재료")
                    st.write("• " + "\n• ".join([str(x) for x in ings if str(x).strip()]))

                if isinstance(steps, list) and steps:
                    _render_steps_with_listen(
                        [str(x) for x in steps],
                        base_key=f"recipe_{date_str}_{slot.get('time','')}",
                        title="레시피 단계",
                    )
            else:
                st.info("이 메뉴의 상세 레시피가 등록되어 있지 않아요.")



def _render_health_view(slot: Dict, date_str: str):
    st.header("운동하기")

    video_url = str(slot.get("video_url", "") or "")
    if video_url:
        st.video(video_url)


def _render_clothing_view(slot: Dict, date_str: str):
    st.header("옷 입기 연습")

    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        _render_steps_with_listen([str(x) for x in guide], base_key=f"cloth_{date_str}_{slot.get('time','')}", title="옷 입기 안내")

    video_url = str(slot.get("video_url", "") or "")
    if video_url:
        st.video(video_url)
    else:
        st.info("추천 영상이 없어요.")


def _render_general_view(slot: Dict, date_str: str, title: str):
    st.header(title)
    guide = slot.get("guide_script") if isinstance(slot.get("guide_script"), list) else []
    if guide:
        _render_steps_with_listen([str(x) for x in guide], base_key=f"gen_{date_str}_{slot.get('time','')}", title="안내")


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

    # UI만 갱신(정시 알람은 JS가 처리)
    st_autorefresh(interval=AUTO_REFRESH_SEC * 1000, key="hibuddy_autorefresh_ui")

    # 오디오 언락(모바일 자동재생 대응)
    _render_audio_unlock_ui()

    schedule, date_str = _load_schedule()
    if not schedule:
        st.warning("오늘 일정이 비어있습니다. 코디네이터 페이지에서 일정을 추가해 주세요.")
        return

    # ✅ JS 알람 스케줄러: 페이지 로드 시 “스케줄별 TTS를 미리 만들어” 1초 타이머로 재생
    # (audio_unlocked=True일 때만 실행됨)
    payload = _prepare_audio_payloads(schedule, date_str)
    _render_js_alarm_scheduler(payload)

    now = datetime.now(KST)
    now_time = now.time()  # ✅ find_active_item에 time 객체로 전달해야 함 (문자열 넣으면 TypeError 났던 케이스 있음)
    active, next_item = find_active_item(schedule, now_time)
    annotated = annotate_schedule_with_status(schedule, now_time)

    # ─────────────────────────────────────────────
    # 레이아웃
    # ─────────────────────────────────────────────
    main_col, side_col = st.columns([0.72, 0.28])

    with main_col:
        # 인사말은 항상 “지금” 기준(세션/가드 때문에 stale 되지 않게)
        h = datetime.now(KST).hour
        if h < 12:
            greeting = "좋은 아침이에요."
        elif h < 18:
            greeting = "좋은 오후예요."
        else:
            greeting = "좋은 저녁이에요."
        st.markdown(f"## {greeting} 오늘도 하이버디랑 함께 해볼까요?")

        st.markdown(f"### 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # 수동 재생(자동이 막히거나 끊긴 경우 대비)
        with st.expander("소리가 안 들리면 여기에서 테스트", expanded=False):
            _tts_button("지금부터 안내를 시작할게요.", key="tts_test_1", label="🔊 테스트 음성 재생")
            st.caption("모바일(iOS 등)에서는 ‘소리 켜기’를 한 번 눌러야 자동 재생이 안정적이에요.")

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

        header_text = {
            "MORNING_BRIEFING": "아침 준비",
            "COOKING": "요리/식사",
            "HEALTH": "운동",
            "REST": "쉬는 시간",
            "LEISURE": "여가",
            "CLOTHING": "옷 입기",
            "NIGHT_WRAPUP": "마무리",
        }.get(slot_type, "활동")

        st.markdown(f"## {header_text}")
        if task:
            st.markdown(f"**오늘 할 일:** {task}")

        today_task_text = f"{header_text} 시간이에요. 오늘 할 일은 {task} 입니다." if task else f"{header_text} 시간이에요."
        _tts_button(today_task_text, key="tts_today_task", label="🔊 현재 활동 요약 듣기")

        st.divider()

        if slot_type == "COOKING":
            _render_cooking_view(active, date_str)

        elif slot_type == "MEAL":
            # 코디네이터에서 MEAL이 남아있을 수 있으니 COOKING으로 처리
            _render_cooking_view(active, date_str)

        elif slot_type == "HEALTH":
            _render_health_view(active, date_str)

        elif slot_type == "CLOTHING":
            _render_clothing_view(active, date_str)

        elif slot_type == "REST":
            _render_general_view(active, date_str, "쉬는 시간")

        elif slot_type == "LEISURE":
            _render_general_view(active, date_str, "여가")

        elif slot_type == "MORNING_BRIEFING":
            _render_general_view(active, date_str, "아침 준비")

        elif slot_type == "NIGHT_WRAPUP":
            _render_general_view(active, date_str, "하루 마무리")

        else:
            _render_general_view(active, date_str, "활동")


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
