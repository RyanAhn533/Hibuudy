import streamlit as st

from utils.topbar import render_topbar


def main():
    st.set_page_config(
        page_title="HiBuddy · 하루 스케줄러",
        page_icon="🧩",
        layout="centered",
        initial_sidebar_state="expanded",
    )

    render_topbar()

    # ─────────────────────────────────────────────
    # 접근성(노인/저시력)용 스타일
    # ─────────────────────────────────────────────
    st.markdown(
        """
        <style>
        .hibuddy-title{
            font-size: 40px;
            font-weight: 800;
            margin: 6px 0 4px 0;
            line-height: 1.2;
        }
        .hibuddy-sub{
            font-size: 20px;
            opacity: 0.85;
            margin-bottom: 14px;
        }
        .hibuddy-chip{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(0,0,0,0.05);
            font-size: 16px;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        .hibuddy-card{
            border: 1px solid rgba(0,0,0,0.10);
            border-radius: 16px;
            padding: 16px 16px;
            background: rgba(255,255,255,0.55);
            margin: 10px 0;
        }
        .hibuddy-card h3{
            margin: 0 0 8px 0;
            font-size: 24px;
        }
        .hibuddy-card p, .hibuddy-card li{
            font-size: 18px;
            line-height: 1.6;
        }
        .hibuddy-step{
            font-size: 18px;
            padding: 12px 14px;
            border-left: 6px solid rgba(0,0,0,0.15);
            background: rgba(0,0,0,0.03);
            border-radius: 10px;
            margin: 8px 0;
        }
        /* 버튼 크게 */
        div.stButton > button {
            width: 100%;
            padding: 14px 16px;
            font-size: 20px;
            font-weight: 700;
            border-radius: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ─────────────────────────────────────────────
    # 상단 헤더
    # ─────────────────────────────────────────────
    st.markdown('<div class="hibuddy-title">HiBuddy · 발달장애인 하루 스케줄러</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hibuddy-sub">하루 일정을 “만들기”와 “따라하기”로 나누어, 화면을 단순하게 구성했습니다</div>',
        unsafe_allow_html=True,
    )

    # 칩(요약)
    st.markdown(
        """
        <span class="hibuddy-chip">큰 글씨</span>
        <span class="hibuddy-chip">큰 버튼</span>
        <span class="hibuddy-chip">한 번에 한 가지 활동</span>
        <span class="hibuddy-chip">사진/영상 활용</span>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # ─────────────────────────────────────────────
    # 핵심 기능 카드 2개
    # ─────────────────────────────────────────────
    st.markdown(
        """
        <div class="hibuddy-card">
            <h3>1 코디네이터가 일정을 만드는 공간</h3>
            <ul>
                <li>오늘 해야 할 일을 말로 적기만 하면, 일정표로 자동 변환됩니다</li>
                <li>요리 시간에는 메뉴, 운동 시간에는 동작을 사진/영상과 함께 저장할 수 있습니다</li>
                <li>저장한 내용은 “오늘 일정 파일”로 보관되고, 다음 화면에서 그대로 불러옵니다</li>
            </ul>
        </div>

        <div class="hibuddy-card">
            <h3>2 사용자가 따라 하는 화면</h3>
            <ul>
                <li>하루 종일 켜두는 따라 하기 전용 화면입니다</li>
                <li>지금 해야 할 활동 “한 개”만 크게 보여주어 집중하기 쉽습니다</li>
                <li>요리/운동은 단계별로 안내하고, 다음 활동은 옆에 작게 보여줍니다</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─────────────────────────────────────────────
    # 바로가기 버튼(노인 UX: “어디 눌러야 하는지” 명확히)
    # ─────────────────────────────────────────────
    st.markdown("### 바로 시작하기")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        if st.button("일정 만들기 (코디네이터)"):
            st.switch_page("pages/1_코디네이터_오늘_일정_설계.py")
    with col2:
        if st.button("따라 하기 (사용자 화면)"):
            st.switch_page("pages/2_사용자_오늘_따라하기.py")

    st.write("")

    # ─────────────────────────────────────────────
    # 사용 방법: 단계 박스
    # ─────────────────────────────────────────────
    st.markdown("### 사용 방법 안내")

    st.markdown(
        """
        <div class="hibuddy-step">
            1 왼쪽 메뉴에서 “일정 만들기(코디네이터)”로 들어가서 오늘 일정을 입력하고 저장합니다
        </div>
        <div class="hibuddy-step">
            2 그 다음 “따라 하기(사용자 화면)”를 열어, 하루 동안 화면을 켜두면 됩니다
        </div>
        <div class="hibuddy-step">
            3 화면에는 지금 해야 할 것만 크게 나오고, 다음 할 일은 작게 표시됩니다
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─────────────────────────────────────────────
    # 안심 문구(노인/초심자 UX)
    # ─────────────────────────────────────────────
    st.info(
        "어렵게 조작할 필요 없습니다  화면에 나오는 안내를 그대로 따라 하면 됩니다",
        icon="ℹ️",
    )


if __name__ == "__main__":
    main()
