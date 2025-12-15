import streamlit as st
from utils.topbar import render_topbar


def _big_card(title: str, icon: str, desc_lines: list, kind: str = "info"):
    text = f"### {icon} {title}\n" + "\n".join([f"- {line}" for line in desc_lines])
    if kind == "success":
        st.success(text)
    elif kind == "warning":
        st.warning(text)
    else:
        st.info(text)


def main():
    render_topbar()

    st.markdown("# HiBuddy")
    st.markdown("## 발달장애인 하루 스케줄 도우미")
    st.caption("오늘 할 일을 쉽게 만들고, 하루 동안 따라할 수 있게 안내합니다.")

    st.markdown("---")

    # ---- 핵심 2기능을 ‘그림(아이콘)+짧은 문장’으로 ----
    col1, col2 = st.columns(2, gap="large")

    with col1:
        _big_card(
            "코디네이터 화면",
            "🧑‍🏫",
            [
                "오늘 할 일을 적고 저장합니다.",
                "중간 일정도 수정/삭제/이동할 수 있습니다.",
                "필요하면 요리/운동/취미 영상도 넣을 수 있습니다.",
            ],
            kind="info",
        )

    with col2:
        _big_card(
            "사용자 화면(따라하기)",
            "🧑‍🦽",
            [
                "지금 해야 할 일을 크게 보여줍니다.",
                "필요하면 영상으로 따라할 수 있습니다.",
                "다음 일정도 함께 보여줍니다.",
            ],
            kind="success",
        )

    st.markdown("---")

    # ---- 사용 방법: 2단계만 크게 ----
    st.markdown("## 사용 방법 (딱 2단계)")
    _big_card(
        "1단계 · 코디네이터가 오늘 일정 만들기",
        "①",
        [
            "왼쪽 메뉴(사이드바)에서 ‘1_코디네이터_일정입력’을 누릅니다.",
            "일정을 입력하고 ‘저장’ 버튼을 누릅니다.",
        ],
        kind="info",
    )
    _big_card(
        "2단계 · 사용자가 ‘오늘 따라하기’ 켜두기",
        "②",
        [
            "왼쪽 메뉴(사이드바)에서 ‘2_사용자_오늘_따라하기’를 누릅니다.",
            "사용자 스마트폰/태블릿에서 하루 동안 켜두면 됩니다.",
        ],
        kind="success",
    )

    st.markdown("---")

    # ---- 바로 이동: page_link(페이지명 기반) ----
    st.markdown("## 바로 이동")

    c1, c2 = st.columns(2, gap="large")

    with c1:
        try:
            st.page_link(
                "1_코디네이터_일정입력",
                label="🧑‍🏫 코디네이터 일정 만들기",
                icon="🧑‍🏫",
            )
            st.caption("오늘 할 일을 입력하고 저장하는 곳")
        except Exception:
            st.warning("왼쪽 메뉴(사이드바)에서 ‘1_코디네이터_일정입력’을 눌러주세요.")

    with c2:
        try:
            st.page_link(
                "2_사용자_오늘_따라하기",
                label="🧑‍🦽 사용자 오늘 따라하기",
                icon="🧑‍🦽",
            )
            st.caption("사용자가 지금 해야 할 일을 크게 보는 화면")
        except Exception:
            st.warning("왼쪽 메뉴(사이드바)에서 ‘2_사용자_오늘_따라하기’를 눌러주세요.")

    st.markdown("---")

    # ---- 입력 예시: 최소 ----
    st.markdown("## 입력 예시(짧게)")
    st.code("10:00 옷 입기\n12:00 점심 먹기\n19:00 드라마 보기", language="text")
    st.caption("길게 쓰지 않아도 됩니다. 시간과 할 일만 적어도 됩니다.")


if __name__ == "__main__":
    main()
