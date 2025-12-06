from pathlib import Path
import streamlit as st

def render_topbar() -> None:
    st.markdown(
        """
        <style>
        .hibuddy-topbar {
            background-color: #f8fafc;
            padding: 0.75rem 1rem 0.5rem 1rem;
            border-bottom: 1px solid #e5e7eb;
            margin: -1rem -1rem 1rem -1rem;
            text-align: center;   /* 전체 중앙 정렬 */
        }
        .hibuddy-title {
            font-size: 1.8rem;    /* 더 크게 */
            font-weight: 700;
            margin-bottom: 0.3rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="hibuddy-topbar">', unsafe_allow_html=True)

    # 로고 표시 (있으면) — 가운데
    logo_path = Path("assets/images/default_menu.png")
    if logo_path.exists():
        st.image(str(logo_path), width=70)
    else:
        st.markdown("<div style='font-size:2rem;'>👋</div>", unsafe_allow_html=True)

    # 제목만 가운데 표시
    st.markdown(
        '<div class="hibuddy-title">Hi-Buddy</div>',
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)
