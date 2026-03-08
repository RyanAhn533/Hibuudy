# utils/topbar.py
# -*- coding: utf-8 -*-
import streamlit as st
from utils.styles import get_global_css


def render_topbar() -> None:
    """글로벌 CSS + 브랜드 탑바 렌더링"""
    # 글로벌 디자인 시스템 CSS 주입
    st.markdown(get_global_css(), unsafe_allow_html=True)

    st.markdown(
        """
        <div class="hb-topbar">
            <div class="hb-topbar-emoji">👋</div>
            <div class="hb-topbar-title">Hi-Buddy</div>
            <div class="hb-topbar-sub">발달장애인을 위한 하루 도우미</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
