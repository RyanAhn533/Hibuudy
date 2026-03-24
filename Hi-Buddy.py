import streamlit as st

from utils.topbar import render_topbar

COORDINATOR_PAGE = "pages/1_코디네이터_일정입력.py"
USER_PAGE = "pages/2_사용자_오늘_따라하기.py"


def main():
    st.set_page_config(
        page_title="하루메이트 - 하루 스케줄러",
        page_icon="👋",
        layout="centered",
        initial_sidebar_state="expanded",
    )

    render_topbar()

    # ── Hero Section ──
    st.markdown(
        """
        <div class="hb-hero">
            <div class="hb-hero-icon">🧩</div>
            <h1>오늘 하루, 같이 해봐요!</h1>
            <p>선생님이 만든 일정을 따라 하루를 보내요</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Feature Cards ──
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div class="hb-feature">
                <div class="hb-feature-icon hb-feature-icon-blue">📝</div>
                <h3>일정 만들기</h3>
                <ul>
                    <li>말로 적으면 일정표 자동 생성</li>
                    <li>활동별 안내 문장 자동 작성</li>
                    <li>저장하면 바로 사용 가능</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("일정 만들기", type="primary", key="btn_coord"):
            st.switch_page(COORDINATOR_PAGE)

    with col2:
        st.markdown(
            """
            <div class="hb-feature">
                <div class="hb-feature-icon hb-feature-icon-amber">📺</div>
                <h3>오늘 하루</h3>
                <ul>
                    <li>하루 종일 켜두는 안내 화면</li>
                    <li>지금 할 일 한 개만 크게 표시</li>
                    <li>단계별 음성 안내 제공</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("오늘 하루 보기", type="primary", key="btn_user"):
            st.switch_page(USER_PAGE)

    # ── How to Use ──
    st.markdown('<div class="hb-section-title">사용 방법 안내</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="hb-step">
            <div class="hb-step-num">1</div>
            <div class="hb-step-text">
                왼쪽 메뉴에서 <strong>"일정 만들기"</strong>로 들어가서 오늘 일정을 입력하고 저장합니다
            </div>
        </div>
        <div class="hb-step">
            <div class="hb-step-num">2</div>
            <div class="hb-step-text">
                그 다음 <strong>"오늘 하루"</strong>를 열어, 하루 동안 화면을 켜두면 됩니다
            </div>
        </div>
        <div class="hb-step">
            <div class="hb-step-num">3</div>
            <div class="hb-step-text">
                화면에는 지금 해야 할 것만 크게 나오고, 다음 할 일은 작게 표시됩니다
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    st.markdown(
        """
        <div class="hb-info">
            ℹ️ 어렵게 조작할 필요 없습니다. 화면에 나오는 안내를 그대로 따라 하면 됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
