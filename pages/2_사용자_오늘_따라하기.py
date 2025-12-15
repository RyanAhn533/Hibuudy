# pages/2_사용자_오늘_따라하기.py
# -*- coding: utf-8 -*-
"""
[목표]
- 심한 발달장애인/노인 사용자 기준으로 2페이지를 "안내 화면"으로 단순화
- 버튼 최소화: (1) 최초 1회 '소리 켜기' (2) '지금 다시 듣기' (3) '오늘 일정 다시 듣기'
- 자동 음성 안내: 최초 진입 / 슬롯 변경 / (선택) 다음 일정 준비 알림
- 타입(GENERAL/HEALTH 등) 노출 금지: 화면에는 한국어 자연어만 표시
- 숫자/시간이 TTS에서 영어로 읽히는 문제 완화: "08:00" 같은 표현은 "8시" / "8시 30분"으로 변환
- 건강(운동)에서 선택(앉아서/서서) 제거: 코디네이터가 넣은 guide_script만 따라가게
- 취미/여가 영상 추천 UI 제거: video_url이 있으면 보여주고, 없으면 안내만
"""

import base64
import json
import os
import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from utils.topbar import render_topbar
from utils.runtime import find_active_item, annotate_schedule_with_status
from utils.tts import synthesize_tts

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

SCHEDULE_PATH = os.path.join("data", "schedule_today.json")

AUTO_REFRESH_SEC = 20        # 더 촘촘하게 갱신 (상태 전환 반응성 ↑)
PRE_NOTICE_MINUTES = 5       # 다음 활동 준비 알림(원하면 0으로 끄면 됨)


# ─────────────────────────────────────────────
# 0) 스케줄 로드
# ─────────────────────────────────────────────
def _load_schedule() -> Optional[Tuple[List[Dict], str]]:
    if not os.path.exists(SCHEDULE_PATH):
        print(f"[DEBUG] schedule not found: {SCHEDULE_PATH}")
        return None

    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    schedule = data.get("schedule", []) or []
    schedule = sorted(schedule, key=lambda it: (it.get("time") or "00:00"))
    date_str = data.get("date") or ""

    print(f"[DEBUG] loaded schedule: date={date_str}, items={len(schedule)}")
    return schedule, date_str


# ─────────────────────────────────────────────
# 1) TTS 텍스트 전처리 (숫자/시간 영어 읽힘 완화)
# ─────────────────────────────────────────────
_TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")

def _time_to_korean_hhmm(text: str) -> str:
    """
    "08:00" -> "8시"
    "13:30" -> "13시 30분"
    """
    def repl(m):
        hh = int(m.group(1))
        mm = int(m.group(2))
        if mm == 0:
            return f"{hh}시"
        return f"{hh}시 {mm}분"
    return _TIME_RE.sub(repl, text)

def _digits_to_korean(text: str) -> str:
    """
    매우 단순한 숫자 읽기 보정.
    - 0~59 범위(분/단계) 정도는 한국어로 읽히는 경향이 좋아짐.
    - 너무 복잡한 수(전화번호 등)는 오히려 깨질 수 있어 최소 적용.
    """
    digit_map = {
        "0": "영", "1": "일", "2": "이", "3": "삼", "4": "사",
        "5": "오", "6": "육", "7": "칠", "8": "팔", "9": "구"
    }
    # 1~2자리 숫자만 부분적으로 변환 (과도한 변환 방지)
    def repl(m):
        s = m.group(0)
        if len(s) == 1:
            return digit_map.get(s, s)
        # 2자리: 10~59만 변환(단계/분/횟수에 주로 등장)
        n = int(s)
        if 10 <= n <= 59:
            # 예: 12 -> "일이"처럼 되면 이상해서, 10단위는 한국식 표현을 약식으로만
            tens = n // 10
            ones = n % 10
            tens_word = {1:"십",2:"이십",3:"삼십",4:"사십",5:"오십"}.get(tens, "")
            if ones == 0:
                return tens_word
            return tens_word + digit_map.get(str(ones), "")
        return s

    return re.sub(r"\b\d{1,2}\b", repl, text)

def _sanitize_tts_text(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    text = _time_to_korean_hhmm(text)
    text = _digits_to_korean(text)
    # 타입 코드/대괄호가 혹시 섞이면 제거
    text = re.sub(r"\[[A-Z_]+\]\s*", "", text)
    return text.strip()


# ─────────────────────────────────────────────
# 2) 오디오 재생 (자동/수동)
# ─────────────────────────────────────────────
def _play_tts_autoplay(text: str):
    """
    autoplay는 브라우저 정책상 첫 상호작용 전에는 막힐 수 있음.
    따라서 "소리 켜기"가 된 뒤에만 호출하도록 설계.
    """
    text = _sanitize_tts_text(text)
    if not text:
        return

    audio_bytes = synthesize_tts(text)
    if not audio_bytes:
        return

    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    st.markdown(
        f"""
        <audio autoplay>
          <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
        </audio>
        """,
        unsafe_allow_html=True,
    )

def _play_tts_manual(text: str):
    """버튼 누른 뒤 재생(정책 통과 확률 매우 높음)."""
    text = _sanitize_tts_text(text)
    if not text:
        return
    audio_bytes = synthesize_tts(text)
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")


# ─────────────────────────────────────────────
# 3) 슬롯 문장 만들기 (타입 노출 금지)
# ─────────────────────────────────────────────
def _slot_headline_korean(t: str) -> str:
    t = (t or "GENERAL").upper()
    if t == "MORNING_BRIEFING":
        return "아침 준비"
    if t == "COOKING":
        return "식사"
    if t == "HEALTH":
        return "운동"
    if t == "CLOTHING":
        return "옷 입기"
    if t == "NIGHT_WRAPUP":
        return "하루 마무리"
    return "활동"

def _build_now_tts(slot: Dict) -> str:
    """지금 활동 자동 안내용 한 문장(짧고 단정)."""
    t = slot.get("type", "GENERAL")
    task = (slot.get("task") or "").strip()
    guide = slot.get("guide_script") or []
    first = (guide[0] or "").strip() if guide else ""

    head = _slot_headline_korean(t)
    parts = [f"지금은 {head} 시간이에요."]
    if task:
        parts.append(f"지금 할 일은 {task}예요.")
    if first:
        parts.append(first)
    return " ".join(parts)

def _build_pre_notice_tts(next_slot: Dict) -> str:
    time_str = (next_slot.get("time") or "").strip()
    head = _slot_headline_korean(next_slot.get("type", "GENERAL"))
    task = (next_slot.get("task") or "").strip()
    if time_str and task:
        return f"잠시 후 {time_str}에 {head}이 있어요. {task} 준비해요."
    if time_str:
        return f"잠시 후 {time_str}에 다음 활동이 있어요. 준비해요."
    return "잠시 후 다음 활동이 있어요. 준비해요."

def _build_day_overview_tts(schedule: List[Dict], date_str: str) -> str:
    """
    '오늘 일정 전체를 한 번에' 짧게 읽어줌.
    너무 길어지면 사용자에게 부담이므로 핵심만.
    """
    # 최대 N개로 제한(너무 길면 기억/집중 깨짐)
    N = 6
    items = schedule[:N]
    chunks = []
    for it in items:
        t = _slot_headline_korean(it.get("type", "GENERAL"))
        task = (it.get("task") or "").strip()
        time_str = (it.get("time") or "").strip()
        if time_str and task:
            chunks.append(f"{time_str}, {t}, {task}")
        elif time_str:
            chunks.append(f"{time_str}, 다음 활동")
        elif task:
            chunks.append(task)

    if not chunks:
        return "오늘 일정이 아직 없어요."

    joined = " / ".join(chunks)
    extra = ""
    if len(schedule) > N:
        extra = " 그 밖의 일정은 화면에서 계속 안내해 드려요."
    return f"오늘은 {date_str}이에요. 오늘 일정은 {joined} 입니다.{extra}"


# ─────────────────────────────────────────────
# 4) 슬롯 식별키 (중복 재생 방지)
# ─────────────────────────────────────────────
def _make_slot_key(date_str: str, slot: Optional[Dict]) -> Optional[str]:
    if not slot:
        return None
    return f"{date_str}__{slot.get('time')}__{slot.get('type')}__{slot.get('task')}"


# ─────────────────────────────────────────────
# 5) 자동 안내 로직 (성공률 최우선)
# ─────────────────────────────────────────────
def _auto_voice_controller(now: datetime, date_str: str, schedule: List[Dict], active: Optional[Dict], next_item: Optional[Dict]):
    """
    정책 상 자동재생은 '소리 켜기(1회)' 이후에만 시행.
    또한 st_autorefresh 때문에 rerun이 잦으므로, 슬롯 키로 중복 방지.
    """
    # 날짜 바뀌면 상태 초기화
    if st.session_state.get("voice_date") != date_str:
        st.session_state["voice_date"] = date_str
        st.session_state["day_overview_done"] = False
        st.session_state["last_slot_key_spoken"] = None
        st.session_state["last_pre_notice_spoken"] = None

    if "sound_enabled" not in st.session_state:
        st.session_state["sound_enabled"] = False
    if "day_overview_done" not in st.session_state:
        st.session_state["day_overview_done"] = False
    if "last_slot_key_spoken" not in st.session_state:
        st.session_state["last_slot_key_spoken"] = None
    if "last_pre_notice_spoken" not in st.session_state:
        st.session_state["last_pre_notice_spoken"] = None

    # 아직 소리 허용 전이면 자동재생은 하지 않음
    if not st.session_state["sound_enabled"]:
        return

    # 1) 최초 1회: 오늘 일정 전체 요약
    if not st.session_state["day_overview_done"]:
        overview = _build_day_overview_tts(schedule, date_str)
        _play_tts_autoplay(overview)
        st.session_state["day_overview_done"] = True
        # 이어서 현재 슬롯도 바로(가능하면)
        if active:
            cur_text = _build_now_tts(active)
            _play_tts_autoplay(cur_text)
            st.session_state["last_slot_key_spoken"] = _make_slot_key(date_str, active)
        return

    # 2) 슬롯 변경 시: 지금 활동 안내
    cur_key = _make_slot_key(date_str, active)
    if active and cur_key and cur_key != st.session_state["last_slot_key_spoken"]:
        _play_tts_autoplay(_build_now_tts(active))
        st.session_state["last_slot_key_spoken"] = cur_key
        return

    # 3) 다음 활동 준비 알림 (옵션)
    if PRE_NOTICE_MINUTES <= 0:
        return

    if next_item and next_item.get("time"):
        try:
            schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            schedule_date = now.date()

        try:
            slot_time = datetime.strptime(next_item["time"], "%H:%M").time()
            slot_dt = datetime.combine(schedule_date, slot_time).replace(tzinfo=KST)
            diff_min = (slot_dt - now).total_seconds() / 60.0
        except Exception as e:
            print(f"[DEBUG] pre-notice calc error: {e}")
            diff_min = None

        if diff_min is not None and 0 < diff_min <= PRE_NOTICE_MINUTES:
            nxt_key = _make_slot_key(date_str, next_item)
            if nxt_key and nxt_key != st.session_state["last_pre_notice_spoken"]:
                _play_tts_autoplay(_build_pre_notice_tts(next_item))
                st.session_state["last_pre_notice_spoken"] = nxt_key
                return


# ─────────────────────────────────────────────
# 6) UI 컴포넌트 (최소)
# ─────────────────────────────────────────────
def _render_sound_gate():
    """
    정책 우회용 1회 버튼.
    - 반드시 "처음에는 버튼을 눌러야 소리가 나요" 안내를 포함.
    - 버튼을 누르면 즉시 짧은 확인 음성도 재생(정책 통과율 ↑).
    """
    st.markdown("### 🔈 소리 안내를 켜 주세요")
    st.info("처음에는 **버튼을 한 번 눌러야** 소리가 나와요.\n\n버튼은 **오늘 한 번만** 누르면 됩니다.")

    # 큰 버튼 느낌(색/크기)
    if st.button("✅ 소리 켜기 (한 번만 누르면 됩니다)", use_container_width=True, type="primary"):
        st.session_state["sound_enabled"] = True
        # 버튼 직후는 사용자 상호작용이므로 거의 확실하게 재생됨
        _play_tts_manual("소리가 켜졌어요. 이제부터는 자동으로 안내해 드릴게요.")


def _render_big_card(title: str, task: str, icon: str = "🟦"):
    st.markdown(
        f"""
        <div style="
            border-radius: 24px;
            padding: 24px;
            border: 2px solid #e6e6e6;
            background: #ffffff;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        ">
            <div style="font-size: 56px; line-height: 1.1;">{icon}</div>
            <div style="font-size: 40px; font-weight: 800; margin-top: 6px;">{title}</div>
            <div style="font-size: 34px; font-weight: 700; margin-top: 10px;">{task}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_simple_video(slot: Dict):
    """
    영상은 '있으면 보여주기'만.
    추천/검색/선택 UI는 2페이지에서 제거.
    """
    vurl = (slot.get("video_url") or "").strip()
    if not vurl:
        return
    st.markdown("---")
    st.markdown("### 🎬 설명 영상")
    st.video(vurl)


# ─────────────────────────────────────────────
# 7) 메인
# ─────────────────────────────────────────────
def user_page():
    render_topbar()

    # 세션 유지 자동 새로고침
    st_autorefresh(interval=AUTO_REFRESH_SEC * 1000, key="auto_refresh_user")

    data = _load_schedule()
    if not data:
        st.error("오늘 일정 파일이 없어요.\n코디네이터 화면에서 먼저 일정을 저장해 주세요.")
        return

    schedule, date_str = data
    if not schedule:
        st.warning("오늘 일정이 비어 있어요.\n코디네이터에게 일정을 확인해 달라고 부탁해 주세요.")
        return

    now = datetime.now(KST)
    active, next_item = find_active_item(schedule, now.time())
    annotated = annotate_schedule_with_status(schedule, now.time())

    # 자동 음성 제어 (소리 켜기 이후에만)
    _auto_voice_controller(now, date_str, schedule, active, next_item)

    # ── 상단 최소 정보 ──
    st.markdown("## HiBuddy · 따라하기")
    st.caption("이 화면은 하루 동안 켜두는 화면이에요.")

    # 소리 게이트(최초 1회)
    if "sound_enabled" not in st.session_state:
        st.session_state["sound_enabled"] = False

    if not st.session_state["sound_enabled"]:
        _render_sound_gate()
        st.markdown("---")

    # ── 메인: 지금 할 일 1개만 크게 ──
    st.markdown(f"### 오늘: **{date_str}** · 지금: **{now.strftime('%H:%M')}**")
    st.markdown("---")

    if not active:
        # 아직 첫 활동 전
        _render_big_card("지금은 쉬는 시간", "조금만 기다려요", icon="⏳")
        if next_item:
            n_task = (next_item.get("task") or "").strip()
            n_time = (next_item.get("time") or "").strip()
            st.markdown("---")
            st.markdown("### 다음 할 일")
            st.write(f"{_sanitize_tts_text(n_time)}에 {n_task}")
    else:
        t = active.get("type", "GENERAL")
        title = f"지금은 {_slot_headline_korean(t)} 시간"
        task = (active.get("task") or "").strip() or "할 일이 있어요"
        icon_map = {
            "MORNING_BRIEFING": "☀️",
            "COOKING": "🍽️",
            "HEALTH": "💪",
            "CLOTHING": "👕",
            "NIGHT_WRAPUP": "🌙",
            "GENERAL": "🟦",
        }
        icon = icon_map.get((t or "GENERAL").upper(), "🟦")
        _render_big_card(title, task, icon=icon)

        # guide_script는 "읽기"가 아니라 "보이기"만(필요 최소)
        guide = active.get("guide_script") or []
        if guide:
            st.markdown("---")
            st.markdown("### 안내")
            # 너무 길면 부담: 최대 3줄만 화면에
            for line in guide[:3]:
                st.write(line)

        # 영상은 있으면 보여주기만
        _render_simple_video(active)

    # ── 버튼 2~3개만: 다시 듣기 ──
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        if st.button("🔁 지금 다시 듣기", use_container_width=True):
            if active:
                _play_tts_manual(_build_now_tts(active))
            else:
                _play_tts_manual("지금은 잠시 기다리는 시간이에요.")

    with col2:
        if st.button("📅 오늘 일정 다시 듣기", use_container_width=True):
            _play_tts_manual(_build_day_overview_tts(schedule, date_str))

    with col3:
        # 보호자/코디용 디버그 보기(사용자에겐 숨기고 싶으면 expander로)
        with st.expander("오늘 타임라인 보기(보호자용)", expanded=False):
            for item in annotated:
                # 타입 노출 금지: 시간 + 할 일만
                label = f"{item.get('time','??:??')} · {item.get('task','')}"
                status = item.get("status")
                if status == "active":
                    st.markdown(f"- ✅ **{label}**")
                elif status == "past":
                    st.markdown(f"- ⚪ {label}")
                else:
                    st.markdown(f"- 🕒 {label}")


if __name__ == "__main__":
    user_page()
