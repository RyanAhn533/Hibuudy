# -*- coding: utf-8 -*-
"""Play Console 스토어 등록정보 애셋 생성: 휴대전화 스크린샷 6장(1080x1920, 9:16) + 그래픽 이미지(1024x500) + 텍스트."""
import os
from PIL import Image, ImageDraw, ImageFont

SRC = r"C:\Users\wnsdu\Hibuudy\docs\screenshots"
OUT = r"C:\Users\wnsdu\Desktop\하루메이트-스토어등록정보-v1.5.0"
FONT = r"C:\Users\wnsdu\Hibuudy\hi_buddy_app\assets\fonts\PretendardVariable.ttf"
os.makedirs(OUT, exist_ok=True)

BG = (0xFA, 0xF7, 0xF2)      # surfaceBase
INK = (0x2A, 0x26, 0x20)     # inkPrimary
BODY = (0x45, 0x40, 0x3A)    # inkBody
CORAL = (0xD1, 0x75, 0x59)   # brandWarm
CORAL_DEEP = (0xB3, 0x5D, 0x43)
WHITE = (255, 255, 255)

def font(size, weight=700):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f

def rounded(im, radius):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], radius=radius, fill=255)
    out = Image.new("RGBA", im.size)
    out.paste(im.convert("RGBA"), (0, 0), mask)
    return out

SHOTS = [
    ("v15_r3b_01_home", "지금 할 일이 한눈에", "큰 버튼 4개. 지금과 다음이 항상 보여요"),
    ("v15_r3_02_user_steps_checked", "한 단계씩 소리로 안내", "체크하면 다음 단계. 타이머는 한 번만 탭"),
    ("v15_r3b_02_today", "오늘 하루를 한 줄로", "지난 일은 흐리게, 지금 할 일은 진하게"),
    ("v15_06_help_mood_hard", "급할 때는 한 번만", "전화·문자·도움 요청, 지금 기분도 알려줘요"),
    ("v15_r2_04_mate", "말 걸면 대답하는 메이트", "오늘 일정, 운동, 요리를 물어보세요"),
    ("v15_p0_04_coord_home", "보호자는 한 문장으로 확인", "오늘 몇 개 했는지, 이번 주 기분은 어땠는지"),
]

W, H = 1080, 1920
for i, (name, title, sub) in enumerate(SHOTS, 1):
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)
    # 상단 캡션
    d.text((W // 2, 150), title, font=font(72, 800), fill=INK, anchor="mm")
    d.text((W // 2, 240), sub, font=font(40, 500), fill=BODY, anchor="mm")
    # 코랄 포인트 바
    d.rounded_rectangle([W // 2 - 40, 292, W // 2 + 40, 300], radius=4, fill=CORAL)
    # 기기 화면 (전체 비율 유지, 높이 기준 축소)
    shot = Image.open(os.path.join(SRC, name + ".png")).convert("RGB")
    target_h = 1520
    scale = target_h / shot.height
    shot = shot.resize((int(shot.width * scale), target_h), Image.LANCZOS)
    frame = rounded(shot, 48)
    # 테두리
    x = (W - frame.width) // 2
    y = 340
    d.rounded_rectangle([x - 6, y - 6, x + frame.width + 6, y + frame.height + 6], radius=54, fill=CORAL)
    canvas.paste(frame, (x, y), frame)
    path = os.path.join(OUT, f"screenshot_{i:02d}_{name.replace('v15_', '')}.png")
    canvas.save(path, "PNG", optimize=True)
    print("saved", path, canvas.size)

# ── 그래픽 이미지 1024x500 ──
fg = Image.new("RGB", (1024, 500), CORAL)
d = ImageDraw.Draw(fg)
# 은은한 원 장식
d.ellipse([700, -220, 1180, 260], fill=CORAL_DEEP)
d.text((70, 150), "하루메이트", font=font(104, 800), fill=WHITE, anchor="lm")
d.text((74, 245), "발달장애인을 위한 AI 하루 도우미", font=font(40, 600), fill=(255, 240, 232), anchor="lm")
d.text((74, 310), "지금 할 일 · 단계별 음성 안내 · 도움 요청 한 번에", font=font(30, 500), fill=(255, 240, 232), anchor="lm")
shot = Image.open(os.path.join(SRC, "v15_r3b_01_home.png")).convert("RGB")
scale = 560 / shot.height
shot = shot.resize((int(shot.width * scale), 560), Image.LANCZOS)
frame = rounded(shot, 30)
x, y = 1024 - frame.width - 70, 60
d.rounded_rectangle([x - 5, y - 5, x + frame.width + 5, y + frame.height + 5], radius=34, fill=WHITE)
fg.paste(frame, (x, y), frame)
fg = fg.crop((0, 0, 1024, 500))
fg.save(os.path.join(OUT, "feature_graphic_1024x500.png"), "PNG", optimize=True)
print("saved feature graphic")

# ── 앱 아이콘 512 (기존 런처 아이콘 업스케일, 참고용) ──
try:
    ic = Image.open(r"C:\Users\wnsdu\Hibuudy\hi_buddy_app\android\app\src\main\res\mipmap-xxxhdpi\ic_launcher.png").convert("RGBA")
    ic.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "app_icon_512_참고용(기존 아이콘 업스케일, 기존 콘솔 아이콘 유지 권장).png"))
    print("icon ref saved", ic.size)
except Exception as e:
    print("icon skip", e)
