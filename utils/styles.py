# utils/styles.py
# -*- coding: utf-8 -*-
"""
Hi-Buddy 글로벌 디자인 시스템
- 발달장애인/저시력 사용자를 위한 따뜻하고 친근한 디자인
- 큰 글씨, 높은 대비, 둥근 모서리, 밝은 색상
"""

# 메인 컬러 팔레트
COLORS = {
    "primary": "#4F46E5",       # 인디고 (메인 브랜드)
    "primary_light": "#818CF8",
    "primary_bg": "#EEF2FF",
    "secondary": "#F59E0B",     # 앰버 (강조)
    "secondary_light": "#FCD34D",
    "success": "#10B981",       # 그린 (완료/성공)
    "success_bg": "#D1FAE5",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "bg": "#F8FAFC",
    "card_bg": "#FFFFFF",
    "text": "#1E293B",
    "text_muted": "#64748B",
    "border": "#E2E8F0",
    # 활동 타입별 색상
    "cooking": "#F97316",       # 오렌지
    "cooking_bg": "#FFF7ED",
    "health": "#10B981",        # 그린
    "health_bg": "#ECFDF5",
    "clothing": "#8B5CF6",      # 바이올렛
    "clothing_bg": "#F5F3FF",
    "leisure": "#EC4899",       # 핑크
    "leisure_bg": "#FDF2F8",
    "morning": "#F59E0B",       # 앰버
    "morning_bg": "#FFFBEB",
    "night": "#6366F1",         # 인디고
    "night_bg": "#EEF2FF",
    "rest": "#06B6D4",          # 시안
    "rest_bg": "#ECFEFF",
    "general": "#64748B",       # 슬레이트
    "general_bg": "#F8FAFC",
}


def get_global_css() -> str:
    """모든 페이지에서 공통 적용할 CSS"""
    return f"""
    <style>
    /* ============ RESET & BASE ============ */
    .stApp {{
        background-color: {COLORS['bg']};
    }}

    /* ============ TOPBAR ============ */
    .hb-topbar {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_light']} 100%);
        padding: 1rem 1.5rem;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 1.5rem -1rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(79, 70, 229, 0.15);
    }}
    .hb-topbar-title {{
        color: white;
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }}
    .hb-topbar-sub {{
        color: rgba(255,255,255,0.85);
        font-size: 1rem;
        margin: 0.2rem 0 0 0;
    }}
    .hb-topbar-emoji {{
        font-size: 2.5rem;
        margin-bottom: 0.3rem;
    }}

    /* ============ CARDS ============ */
    .hb-card {{
        background: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .hb-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .hb-card-accent {{
        border-left: 5px solid {COLORS['primary']};
    }}

    /* 활동 타입별 카드 */
    .hb-card-cooking {{
        background: {COLORS['cooking_bg']};
        border-left: 5px solid {COLORS['cooking']};
    }}
    .hb-card-health {{
        background: {COLORS['health_bg']};
        border-left: 5px solid {COLORS['health']};
    }}
    .hb-card-clothing {{
        background: {COLORS['clothing_bg']};
        border-left: 5px solid {COLORS['clothing']};
    }}
    .hb-card-leisure {{
        background: {COLORS['leisure_bg']};
        border-left: 5px solid {COLORS['leisure']};
    }}
    .hb-card-morning {{
        background: {COLORS['morning_bg']};
        border-left: 5px solid {COLORS['morning']};
    }}
    .hb-card-night {{
        background: {COLORS['night_bg']};
        border-left: 5px solid {COLORS['night']};
    }}
    .hb-card-rest {{
        background: {COLORS['rest_bg']};
        border-left: 5px solid {COLORS['rest']};
    }}

    /* ============ HERO SECTION ============ */
    .hb-hero {{
        background: linear-gradient(135deg, {COLORS['primary_bg']} 0%, #DBEAFE 50%, #FEF3C7 100%);
        border-radius: 24px;
        padding: 2.5rem 2rem;
        text-align: center;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(79, 70, 229, 0.1);
    }}
    .hb-hero-icon {{
        font-size: 4rem;
        margin-bottom: 0.5rem;
    }}
    .hb-hero h1 {{
        font-size: 2.5rem;
        font-weight: 800;
        color: {COLORS['text']};
        margin: 0.5rem 0;
        letter-spacing: -1px;
    }}
    .hb-hero p {{
        font-size: 1.2rem;
        color: {COLORS['text_muted']};
        margin: 0;
    }}

    /* ============ FEATURE CARDS (HOME) ============ */
    .hb-feature {{
        background: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 20px;
        padding: 2rem 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
        height: 100%;
    }}
    .hb-feature:hover {{
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }}
    .hb-feature-icon {{
        width: 72px;
        height: 72px;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        margin-bottom: 1rem;
    }}
    .hb-feature-icon-blue {{
        background: {COLORS['primary_bg']};
    }}
    .hb-feature-icon-amber {{
        background: #FEF3C7;
    }}
    .hb-feature h3 {{
        font-size: 1.4rem;
        font-weight: 700;
        color: {COLORS['text']};
        margin: 0 0 0.75rem 0;
    }}
    .hb-feature p, .hb-feature li {{
        font-size: 1.05rem;
        color: {COLORS['text_muted']};
        line-height: 1.8;
        text-align: left;
    }}
    .hb-feature ul {{
        list-style: none;
        padding: 0;
        margin: 0;
    }}
    .hb-feature li::before {{
        content: "\\2713\\0020";
        color: {COLORS['success']};
        font-weight: 700;
        margin-right: 6px;
    }}

    /* ============ STEP PILLS ============ */
    .hb-step {{
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 1rem 1.25rem;
        background: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 14px;
        margin: 0.5rem 0;
        font-size: 1.1rem;
        line-height: 1.6;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}
    .hb-step-num {{
        background: {COLORS['primary']};
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.9rem;
        flex-shrink: 0;
    }}
    .hb-step-text {{
        flex: 1;
        color: {COLORS['text']};
    }}

    /* ============ ACTIVITY HEADER (USER PAGE) ============ */
    .hb-activity-header {{
        padding: 1.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 1rem;
    }}
    .hb-activity-header h2 {{
        margin: 0;
        font-size: 2rem;
        font-weight: 800;
    }}
    .hb-activity-header p {{
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.85;
    }}
    .hb-activity-cooking {{
        background: linear-gradient(135deg, {COLORS['cooking_bg']} 0%, #FFEDD5 100%);
        color: #9A3412;
    }}
    .hb-activity-health {{
        background: linear-gradient(135deg, {COLORS['health_bg']} 0%, #D1FAE5 100%);
        color: #065F46;
    }}
    .hb-activity-clothing {{
        background: linear-gradient(135deg, {COLORS['clothing_bg']} 0%, #EDE9FE 100%);
        color: #5B21B6;
    }}
    .hb-activity-leisure {{
        background: linear-gradient(135deg, {COLORS['leisure_bg']} 0%, #FCE7F3 100%);
        color: #9D174D;
    }}
    .hb-activity-morning {{
        background: linear-gradient(135deg, {COLORS['morning_bg']} 0%, #FEF3C7 100%);
        color: #92400E;
    }}
    .hb-activity-night {{
        background: linear-gradient(135deg, {COLORS['night_bg']} 0%, #E0E7FF 100%);
        color: #3730A3;
    }}
    .hb-activity-rest {{
        background: linear-gradient(135deg, {COLORS['rest_bg']} 0%, #CFFAFE 100%);
        color: #155E75;
    }}
    .hb-activity-general {{
        background: linear-gradient(135deg, {COLORS['general_bg']} 0%, #E2E8F0 100%);
        color: #334155;
    }}

    /* ============ TIMELINE (SIDEBAR) ============ */
    .hb-timeline-item {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.6rem 0.8rem;
        border-radius: 10px;
        margin: 0.3rem 0;
        font-size: 0.95rem;
        transition: background 0.2s;
    }}
    .hb-timeline-active {{
        background: {COLORS['success_bg']};
        border: 2px solid {COLORS['success']};
        font-weight: 700;
    }}
    .hb-timeline-past {{
        opacity: 0.5;
        text-decoration: line-through;
    }}
    .hb-timeline-upcoming {{
        background: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
    }}
    .hb-timeline-dot {{
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex-shrink: 0;
    }}
    .hb-timeline-dot-active {{
        background: {COLORS['success']};
        box-shadow: 0 0 0 3px {COLORS['success_bg']};
    }}
    .hb-timeline-dot-past {{
        background: {COLORS['text_muted']};
    }}
    .hb-timeline-dot-upcoming {{
        background: {COLORS['border']};
    }}

    /* ============ GREETING BANNER ============ */
    .hb-greeting {{
        background: linear-gradient(135deg, {COLORS['primary_bg']} 0%, #DBEAFE 100%);
        border-radius: 20px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(79, 70, 229, 0.1);
    }}
    .hb-greeting h2 {{
        color: {COLORS['text']};
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0 0 0.3rem 0;
    }}
    .hb-greeting p {{
        color: {COLORS['text_muted']};
        font-size: 1.1rem;
        margin: 0;
    }}

    /* ============ BUTTONS ============ */
    div.stButton > button {{
        width: 100%;
        padding: 14px 20px;
        font-size: 1.15rem;
        font-weight: 700;
        border-radius: 14px;
        border: none;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    }}
    div.stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }}
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_light']} 100%);
        color: white;
    }}

    /* ============ EXPANDER ============ */
    .streamlit-expanderHeader {{
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
    }}

    /* ============ BADGE / CHIP ============ */
    .hb-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }}
    .hb-badge-cooking {{ background: #FFEDD5; color: #9A3412; }}
    .hb-badge-health {{ background: #D1FAE5; color: #065F46; }}
    .hb-badge-clothing {{ background: #EDE9FE; color: #5B21B6; }}
    .hb-badge-leisure {{ background: #FCE7F3; color: #9D174D; }}
    .hb-badge-morning {{ background: #FEF3C7; color: #92400E; }}
    .hb-badge-night {{ background: #E0E7FF; color: #3730A3; }}
    .hb-badge-rest {{ background: #ECFEFF; color: #155E75; }}
    .hb-badge-general {{ background: #F1F5F9; color: #475569; }}

    /* ============ SECTION TITLE ============ */
    .hb-section-title {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {COLORS['text']};
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid {COLORS['primary']};
        display: inline-block;
    }}

    /* ============ RECIPE STEP (USER PAGE) ============ */
    .hb-recipe-step {{
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 1rem 1.25rem;
        background: white;
        border: 1px solid {COLORS['border']};
        border-radius: 14px;
        margin: 0.4rem 0;
        font-size: 1.15rem;
        line-height: 1.7;
    }}
    .hb-recipe-step-num {{
        background: {COLORS['cooking']};
        color: white;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1rem;
        flex-shrink: 0;
    }}

    /* ============ INFO BOX ============ */
    .hb-info {{
        background: {COLORS['primary_bg']};
        border: 1px solid rgba(79, 70, 229, 0.2);
        border-radius: 14px;
        padding: 1rem 1.25rem;
        font-size: 1.05rem;
        color: {COLORS['text']};
        line-height: 1.6;
    }}

    /* ============ COORDINATOR SCHEDULE ITEM ============ */
    .hb-sched-item {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        background: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        margin: 0.4rem 0;
        font-size: 1.05rem;
    }}
    .hb-sched-time {{
        background: {COLORS['primary']};
        color: white;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.95rem;
        white-space: nowrap;
    }}

    /* ============ RESPONSIVE ============ */
    @media (max-width: 768px) {{
        .hb-hero h1 {{ font-size: 1.8rem; }}
        .hb-hero p {{ font-size: 1rem; }}
        .hb-feature h3 {{ font-size: 1.2rem; }}
        .hb-greeting h2 {{ font-size: 1.4rem; }}
    }}
    </style>
    """


def get_activity_css_class(slot_type: str) -> str:
    """슬롯 타입에 따른 CSS 클래스명 반환"""
    mapping = {
        "COOKING": "cooking",
        "MEAL": "cooking",
        "HEALTH": "health",
        "CLOTHING": "clothing",
        "LEISURE": "leisure",
        "MORNING_BRIEFING": "morning",
        "NIGHT_WRAPUP": "night",
        "REST": "rest",
    }
    return mapping.get(slot_type.upper(), "general")


def get_activity_emoji(slot_type: str) -> str:
    """슬롯 타입에 따른 이모지"""
    mapping = {
        "COOKING": "🍳",
        "MEAL": "🍽️",
        "HEALTH": "💪",
        "CLOTHING": "👔",
        "LEISURE": "🎮",
        "MORNING_BRIEFING": "🌅",
        "NIGHT_WRAPUP": "🌙",
        "REST": "☕",
        "ROUTINE": "🧹",
        "GENERAL": "📋",
    }
    return mapping.get(slot_type.upper(), "📋")
