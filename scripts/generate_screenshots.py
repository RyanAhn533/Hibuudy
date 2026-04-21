"""
하루메이트 Play Store 스크린샷 5장 생성기
────────────────────────────────────────────────────
1080×1920 × 5장 · 세일즈 스토리보드 반영 · PIL 렌더링
"""
from __future__ import annotations
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── 브랜드 색 ──
PRIMARY = (79, 124, 255)
PRIMARY_SOFT = (230, 238, 255)
ACCENT = (255, 181, 71)
ACCENT_SOFT = (255, 244, 224)
SUCCESS = (63, 183, 101)
DANGER = (232, 89, 74)
N50 = (250, 250, 250)
N100 = (244, 245, 247)
N200 = (229, 231, 235)
N400 = (154, 160, 166)
N700 = (58, 61, 66)
N900 = (26, 28, 31)
WHITE = (255, 255, 255)

W, H = 1080, 1920

# ── 폰트 ──
FONT_PATHS = [
    "C:/Windows/Fonts/malgunbd.ttf",
    "C:/Windows/Fonts/malgun.ttf",
]


def font(size: int, bold=False) -> ImageFont.FreeTypeFont:
    for p in FONT_PATHS:
        try:
            if bold and "malgunbd" in p:
                return ImageFont.truetype(p, size)
            if not bold and "malgunbd" not in p:
                return ImageFont.truetype(p, size)
        except Exception:
            continue
    # fallback
    for p in FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def rounded_rect(draw: ImageDraw.ImageDraw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_centered_text(draw, y, text, f, color, width=W):
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2, y), text, font=f, fill=color)


def draw_multiline_centered(draw, y, text, f, color, width=W, line_gap=6):
    lines = text.split("\n")
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=f)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((width - tw) // 2, y), line, font=f, fill=color)
        y += th + line_gap


def base_canvas(bg_top=PRIMARY, bg_bottom=None) -> Image.Image:
    img = Image.new("RGB", (W, H), bg_top)
    if bg_bottom:
        # simple vertical gradient
        for y in range(H):
            r = int(bg_top[0] + (bg_bottom[0] - bg_top[0]) * y / H)
            g = int(bg_top[1] + (bg_bottom[1] - bg_top[1]) * y / H)
            b = int(bg_top[2] + (bg_bottom[2] - bg_top[2]) * y / H)
            ImageDraw.Draw(img).line([(0, y), (W, y)], fill=(r, g, b))
    return img


def draw_header(img, headline, subtitle, title_color=WHITE, sub_color=(255, 255, 255, 230)):
    draw = ImageDraw.Draw(img)
    # 상단 "하루메이트" 작은 워드마크
    wm_font = font(34, bold=True)
    bbox = draw.textbbox((0, 0), "하루메이트", font=wm_font)
    tw = bbox[2] - bbox[0]
    # 작은 해 아이콘 왼쪽에
    icon_size = 42
    total_w = icon_size + 16 + tw
    start_x = (W - total_w) // 2
    # 해 동그라미
    cx, cy = start_x + icon_size // 2, 100 + icon_size // 2
    draw.ellipse([(cx - icon_size // 2, cy - icon_size // 2),
                  (cx + icon_size // 2, cy + icon_size // 2)], fill=ACCENT)
    draw.text((start_x + icon_size + 16, 100), "하루메이트", font=wm_font, fill=WHITE)

    # 헤드라인
    head_font = font(88, bold=True)
    draw_multiline_centered(draw, 230, headline, head_font, title_color, line_gap=20)

    # 서브
    sub_font = font(40)
    # subtitle y position after headline
    # simple: fixed y
    lines = headline.split("\n")
    sub_y = 230 + len(lines) * 120 + 10
    draw_multiline_centered(draw, sub_y, subtitle, sub_font, N50)


def draw_phone_frame(img, x, y, w=640, h=1180, content_drawer=None):
    """Phone frame centered · 다크 베젤 + 흰 화면."""
    draw = ImageDraw.Draw(img)
    # 베젤
    rounded_rect(draw, (x, y, x + w, y + h), radius=72, fill=N900)
    # 화면
    screen_x, screen_y = x + 16, y + 16
    screen_w, screen_h = w - 32, h - 32
    rounded_rect(draw, (screen_x, screen_y, screen_x + screen_w, screen_y + screen_h),
                 radius=60, fill=N50)
    # 노치
    notch_w, notch_h = 200, 36
    notch_x = x + (w - notch_w) // 2
    rounded_rect(draw, (notch_x, y + 16, notch_x + notch_w, y + 16 + notch_h),
                 radius=18, fill=N900)

    if content_drawer:
        content_drawer(img, screen_x, screen_y, screen_w, screen_h)


def draw_footer(img, subline=None):
    draw = ImageDraw.Draw(img)
    y = H - 100
    draw.rectangle([(0, H - 140), (W, H)], fill=(255, 255, 255, 40))
    # 브랜드 줄
    brand_font = font(32)
    text = subline or "하루메이트 · 발달장애인과 보호자의 하루 도우미"
    bbox = draw.textbbox((0, 0), text, font=brand_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, font=brand_font, fill=WHITE)


# ═══════════════════════════════════════════════════════════
# SCREEN 1: 당사자 홈
# ═══════════════════════════════════════════════════════════
def content_user_home(img, sx, sy, sw, sh):
    draw = ImageDraw.Draw(img)
    # Topbar gradient
    top = Image.new("RGB", (sw - 64, 140), PRIMARY)
    img.paste(top, (sx + 32, sy + 80))
    tb_mask = Image.new("L", top.size, 0)
    ImageDraw.Draw(tb_mask).rounded_rectangle([(0, 0), (top.size[0] - 1, top.size[1] - 1)], radius=28, fill=255)
    img.paste(top, (sx + 32, sy + 80), tb_mask)
    f1 = font(36, bold=True)
    f2 = font(24)
    draw_centered_text(draw, sy + 110, "안녕하세요, 유진님", f1, WHITE, width=sw + sx * 2 - (sw + sx * 2 - sx - sx) + sw)
    # simple: center manually
    bbox = draw.textbbox((0, 0), "안녕하세요, 유진님", font=f1)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 108), "안녕하세요, 유진님", font=f1, fill=WHITE)
    bbox = draw.textbbox((0, 0), "토요일, 오후 2시", font=f2)
    tw2 = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw2) // 2, sy + 158), "토요일, 오후 2시", font=f2, fill=(255, 255, 255))

    # Hero card
    rounded_rect(draw, (sx + 32, sy + 250, sx + sw - 32, sy + 380),
                 radius=28, fill=PRIMARY_SOFT, outline=PRIMARY, width=3)
    f_hero = font(32, bold=True)
    f_hero2 = font(24)
    bbox = draw.textbbox((0, 0), "오늘 할 일이 있어요", font=f_hero)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 275), "오늘 할 일이 있어요", font=f_hero, fill=N900)
    bbox = draw.textbbox((0, 0), "지금은 라면 끓이기 시간이에요", font=f_hero2)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 320), "지금은 라면 끓이기 시간이에요", font=f_hero2, fill=N700)

    # Big CTA 1
    rounded_rect(draw, (sx + 32, sy + 430, sx + sw - 32, sy + 610),
                 radius=32, fill=PRIMARY)
    f_cta = font(40, bold=True)
    bbox = draw.textbbox((0, 0), "▶  오늘 하루 보기", font=f_cta)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 490), "▶  오늘 하루 보기", font=f_cta, fill=WHITE)

    # Big CTA 2
    rounded_rect(draw, (sx + 32, sy + 640, sx + sw - 32, sy + 820),
                 radius=32, fill=ACCENT)
    bbox = draw.textbbox((0, 0), "💬  도우미에게 물어보기", font=f_cta)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 700), "💬  도우미에게 물어보기", font=f_cta, fill=N900)

    # SOS
    rounded_rect(draw, (sx + sw - 130, sy + sh - 130, sx + sw - 40, sy + sh - 40),
                 radius=45, fill=DANGER)
    f_sos = font(24, bold=True)
    bbox = draw.textbbox((0, 0), "SOS", font=f_sos)
    tw = bbox[2] - bbox[0]
    draw.text((sx + sw - 130 + (90 - tw) // 2, sy + sh - 130 + 34), "SOS", font=f_sos, fill=WHITE)


# ═══════════════════════════════════════════════════════════
# SCREEN 2: 현재 활동
# ═══════════════════════════════════════════════════════════
def content_activity(img, sx, sy, sw, sh):
    draw = ImageDraw.Draw(img)
    # Time chip
    rounded_rect(draw, (sx + 32, sy + 100, sx + 340, sy + 160), radius=20, fill=ACCENT_SOFT)
    f_chip = font(26, bold=True)
    draw.text((sx + 60, sy + 116), "⏰  14:00 · 지금 시간", font=f_chip, fill=N900)

    # Title
    f_title = font(56, bold=True)
    draw.text((sx + 32, sy + 200), "라면 끓이기", font=f_title, fill=N900)
    f_sub = font(28)
    draw.text((sx + 32, sy + 280), "5단계 · 약 12분", font=f_sub, fill=N400)

    # Step card
    rounded_rect(draw, (sx + 32, sy + 340, sx + sw - 32, sy + 720),
                 radius=28, fill=WHITE, outline=PRIMARY, width=4)
    # step number
    cx = sx + sw // 2
    draw.ellipse([(cx - 40, sy + 370), (cx + 40, sy + 450)], fill=PRIMARY)
    f_num = font(44, bold=True)
    bbox = draw.textbbox((0, 0), "1", font=f_num)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw // 2, sy + 380), "1", font=f_num, fill=WHITE)

    # step text
    step_font = font(40, bold=True)
    lines = ["냄비에 물 500ml를", "부어주세요"]
    y = sy + 480
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=step_font)
        tw = bbox[2] - bbox[0]
        draw.text((sx + (sw - tw) // 2, y), line, font=step_font, fill=N900)
        y += 60

    # Listen button
    rounded_rect(draw, (sx + 80, sy + 640, sx + sw - 80, sy + 700),
                 radius=16, fill=SUCCESS)
    f_listen = font(28, bold=True)
    bbox = draw.textbbox((0, 0), "🔊  다시 들어보기", font=f_listen)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 658), "🔊  다시 들어보기", font=f_listen, fill=WHITE)

    # Progress
    rounded_rect(draw, (sx + 32, sy + 770, sx + sw - 32, sy + 790), radius=10, fill=N200)
    rounded_rect(draw, (sx + 32, sy + 770, sx + 32 + (sw - 64) // 5, sy + 790), radius=10, fill=SUCCESS)
    f_prog = font(22)
    bbox = draw.textbbox((0, 0), "1 / 5 단계", font=f_prog)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 810), "1 / 5 단계", font=f_prog, fill=N400)

    # Next button
    rounded_rect(draw, (sx + 32, sy + 870, sx + sw - 32, sy + 960),
                 radius=24, fill=PRIMARY)
    f_next = font(36, bold=True)
    bbox = draw.textbbox((0, 0), "✓  했어요 · 다음 단계", font=f_next)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 895), "✓  했어요 · 다음 단계", font=f_next, fill=WHITE)


# ═══════════════════════════════════════════════════════════
# SCREEN 3: 코디 일정 입력
# ═══════════════════════════════════════════════════════════
def content_coord_input(img, sx, sy, sw, sh):
    draw = ImageDraw.Draw(img)

    # Title
    f_title = font(48, bold=True)
    draw.text((sx + 32, sy + 100), "일정 만들기", font=f_title, fill=N900)
    f_sub = font(28)
    draw.text((sx + 32, sy + 170), "말하듯 편하게 적어주세요", font=f_sub, fill=N400)

    # Textarea
    rounded_rect(draw, (sx + 32, sy + 240, sx + sw - 32, sy + 720),
                 radius=24, fill=WHITE, outline=PRIMARY_SOFT, width=4)
    f_ta = font(30)
    items = [
        "08:00 · 아침 일정 안내",
        "10:00 · 옷 입기 연습",
        "12:00 · 라면 또는 카레",
        "15:00 · 쉬는 시간",
        "18:00 · 운동하기",
        "22:00 · 하루 마무리",
    ]
    y = sy + 270
    for item in items:
        draw.text((sx + 60, y), item, font=f_ta, fill=N900)
        y += 70

    # AI button
    rounded_rect(draw, (sx + 32, sy + 770, sx + sw - 32, sy + 870),
                 radius=24, fill=PRIMARY)
    f_btn = font(36, bold=True)
    bbox = draw.textbbox((0, 0), "✨  일정표 만들기", font=f_btn)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 800), "✨  일정표 만들기", font=f_btn, fill=WHITE)

    # hint
    f_hint = font(22)
    hint = "AI가 약 5초 안에 만들어요"
    bbox = draw.textbbox((0, 0), hint, font=f_hint)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 890), hint, font=f_hint, fill=N400)


# ═══════════════════════════════════════════════════════════
# SCREEN 4: 주간 리포트
# ═══════════════════════════════════════════════════════════
def content_report(img, sx, sy, sw, sh):
    draw = ImageDraw.Draw(img)

    f_title = font(48, bold=True)
    draw.text((sx + 32, sy + 100), "유진님의 한 주", font=f_title, fill=N900)
    f_sub = font(26)
    draw.text((sx + 32, sy + 170), "4월 13일 ~ 19일", font=f_sub, fill=N400)

    # Highlight card
    rounded_rect(draw, (sx + 32, sy + 240, sx + sw - 32, sy + 560),
                 radius=24, fill=PRIMARY_SOFT, outline=PRIMARY, width=3)
    f_lbl = font(22, bold=True)
    draw.text((sx + 64, sy + 270), "이번 주 해낸 것", font=f_lbl, fill=PRIMARY)
    f_items = font(32, bold=True)
    items = [
        "✓  요리를 18번 했어요",
        "✓  운동을 8번 했어요",
        "✓  혼자 옷을 19번 입었어요",
    ]
    y = sy + 330
    for item in items:
        draw.text((sx + 64, y), item, font=f_items, fill=N900)
        y += 60

    # Activity card
    rounded_rect(draw, (sx + 32, sy + 600, sx + sw - 32, sy + 920),
                 radius=24, fill=WHITE, outline=N200, width=2)
    draw.text((sx + 64, sy + 630), "활동별 진행", font=f_lbl, fill=N400)
    f_a = font(28, bold=True)
    f_b = font(26)
    acts = [("🍳 요리", "18 / 21"), ("🏃 운동", "8 / 13"), ("👕 옷 입기", "19 / 21")]
    y = sy + 690
    for label, n in acts:
        draw.text((sx + 64, y), label, font=f_a, fill=N900)
        bbox = draw.textbbox((0, 0), n, font=f_b)
        tw = bbox[2] - bbox[0]
        draw.text((sx + sw - 64 - tw, y + 2), n, font=f_b, fill=N700)
        y += 70


# ═══════════════════════════════════════════════════════════
# SCREEN 5: SOS
# ═══════════════════════════════════════════════════════════
def content_sos(img, sx, sy, sw, sh):
    draw = ImageDraw.Draw(img)
    # SOS icon
    cx = sx + sw // 2
    cy = sy + 180
    r = 60
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=DANGER)
    f_sos = font(56, bold=True)
    bbox = draw.textbbox((0, 0), "!", font=f_sos)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 10), "!", font=f_sos, fill=WHITE)

    f_title = font(48, bold=True)
    text = "도움이 필요해요"
    bbox = draw.textbbox((0, 0), text, font=f_title)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 280), text, font=f_title, fill=N900)

    f_sub = font(28)
    text = "누구에게 알릴까요?"
    bbox = draw.textbbox((0, 0), text, font=f_sub)
    tw = bbox[2] - bbox[0]
    draw.text((sx + (sw - tw) // 2, sy + 350), text, font=f_sub, fill=N400)

    # Contact cards
    contacts = [
        ("💗  엄마", "010-1234-5678", PRIMARY),
        ("🏫  김선생님", "복지관 담당", PRIMARY),
    ]
    y = sy + 440
    f_name = font(32, bold=True)
    f_phone = font(24)
    for name, phone, color in contacts:
        rounded_rect(draw, (sx + 32, y, sx + sw - 32, y + 120),
                     radius=24, fill=WHITE, outline=N200, width=2)
        draw.text((sx + 64, y + 22), name, font=f_name, fill=N900)
        draw.text((sx + 64, y + 72), phone, font=f_phone, fill=N400)
        # call icon
        draw.ellipse([(sx + sw - 110, y + 30), (sx + sw - 50, y + 90)], fill=SUCCESS)
        f_ph = font(32)
        draw.text((sx + sw - 96, y + 38), "📞", font=f_ph, fill=WHITE)
        y += 140

    # 119
    rounded_rect(draw, (sx + 32, y, sx + sw - 32, y + 120),
                 radius=24, fill=DANGER)
    draw.text((sx + 64, y + 22), "🚨  119 응급 전화", font=f_name, fill=WHITE)
    draw.text((sx + 64, y + 72), "아주 급할 때만", font=f_phone, fill=WHITE)


# ═══════════════════════════════════════════════════════════
# SCREENS CONFIG
# ═══════════════════════════════════════════════════════════
SCREENS = [
    {
        "num": 1,
        "headline": "혼자서도 하루를\n시작할 수 있어요",
        "subtitle": "큰 버튼 2개 · 친절한 음성 안내",
        "content": content_user_home,
        "bg": PRIMARY,
        "bg2": (107, 142, 255),
    },
    {
        "num": 2,
        "headline": "한 단계씩\n같이 따라가요",
        "subtitle": "존댓말로 짧게 · 음성 재생 가능",
        "content": content_activity,
        "bg": ACCENT,
        "bg2": (255, 200, 120),
    },
    {
        "num": 3,
        "headline": "선생님이 일정을\n만들어 주세요",
        "subtitle": "말하듯 적으면 · AI가 정리해 드려요",
        "content": content_coord_input,
        "bg": PRIMARY,
        "bg2": (127, 162, 255),
    },
    {
        "num": 4,
        "headline": "해낸 것을\n그대로 보여드려요",
        "subtitle": "퍼센트가 아닌 · 진짜 해낸 개수로",
        "content": content_report,
        "bg": SUCCESS,
        "bg2": (100, 210, 140),
    },
    {
        "num": 5,
        "headline": "언제나 도움을\n부를 수 있어요",
        "subtitle": "한 번의 터치 · 가족과 119 연결",
        "content": content_sos,
        "bg": DANGER,
        "bg2": (255, 120, 110),
    },
]


def main():
    out_dir = Path(__file__).resolve().parent.parent / "assets" / "brand" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)

    for s in SCREENS:
        img = base_canvas(s["bg"], s["bg2"])
        draw_header(img, s["headline"], s["subtitle"])
        # Phone centered, below header
        phone_w, phone_h = 680, 1100
        phone_x = (W - phone_w) // 2
        phone_y = 580
        draw_phone_frame(img, phone_x, phone_y, phone_w, phone_h, content_drawer=s["content"])
        draw_footer(img)

        out_path = out_dir / f"screenshot_{s['num']}_1080x1920.png"
        img.save(out_path, "PNG", optimize=True)
        print(f"[+] {out_path.name}")

    print(f"\n[OK] 5 screenshots saved to {out_dir.relative_to(out_dir.parent.parent.parent)}")


if __name__ == "__main__":
    main()
