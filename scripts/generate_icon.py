"""
하루메이트 HaruMate — App Icon Generator
───────────────────────────────────────────────────────────
Brand Identity v1.0 기반. 파라미터화된 PIL 아이콘 생성기.
재생성 가능 · 서브 브랜드 변주 가능 · 모든 해상도 자동 출력.

사용법:
    python scripts/generate_icon.py [variant]
    variant: master | eyes | dense | senior (기본: master)

출력:
    assets/brand/icons/
      master/            ← variant
        icon_1024.png
        icon_512.png
        mipmap_48/72/96/144/192.png
        adaptive_fg.png  adaptive_bg.png
      feature_graphic_1024x500.png
"""
from __future__ import annotations
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── 색 토큰 (Brand Identity v1.0) ──
PRIMARY      = (79, 124, 255)
PRIMARY_DARK = (58, 95, 204)      # 시니어 서브 브랜드
ACCENT       = (255, 181, 71)
WHITE        = (255, 255, 255)
N900         = (26, 28, 31)

# ── 아이콘 기본 사양 ──
CANVAS = 1024

# ── 변형 정의 ──
VARIANTS = {
    "master": {
        "description": "마스터 아이콘 (발달장애 Phase 1)",
        "bg": PRIMARY,
        "sun_fill": ACCENT,
        "sun_core_radius": 230,
        "ray_count": 8,
        "ray_length": 115,
        "ray_width": 52,
        "ray_gap": 28,
        "has_eyes": False,
        "submark": None,
    },
    "eyes": {
        "description": "마스터 + 눈 2개 (따뜻한 인격 암시)",
        "bg": PRIMARY,
        "sun_fill": ACCENT,
        "sun_core_radius": 230,
        "ray_count": 8,
        "ray_length": 115,
        "ray_width": 52,
        "ray_gap": 28,
        "has_eyes": True,
        "submark": None,
    },
    "dense": {
        "description": "12광선 (더 풍성)",
        "bg": PRIMARY,
        "sun_fill": ACCENT,
        "sun_core_radius": 220,
        "ray_count": 12,
        "ray_length": 95,
        "ray_width": 38,
        "ray_gap": 30,
        "has_eyes": False,
        "submark": None,
    },
    "senior": {
        "description": "시니어 서브 브랜드 (해+집지붕)",
        "bg": PRIMARY_DARK,
        "sun_fill": ACCENT,
        "sun_core_radius": 200,
        "ray_count": 8,
        "ray_length": 95,
        "ray_width": 48,
        "ray_gap": 26,
        "has_eyes": False,
        "submark": "roof",
    },
}


def draw_rounded_ray(width: int, length: int, color) -> Image.Image:
    """라운드 캡 광선 1개를 세로로 그림. (0,0) 상단에 시작."""
    img = Image.new("RGBA", (width, length), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([(0, 0), (width - 1, length - 1)], radius=width // 2, fill=color)
    return img


def place_ray(base: Image.Image, center: tuple[int, int], angle_deg: float,
              distance: int, length: int, width: int, color):
    """중심에서 angle_deg 방향으로 광선 배치 (0°=위쪽, 시계방향)."""
    ray = draw_rounded_ray(width, length, color)
    # PIL rotate: 각도 = 반시계. 우리는 시계방향 양수 → -angle_deg.
    rotated = ray.rotate(-angle_deg, resample=Image.BICUBIC, expand=True)

    # 광선 중심점 = 이미지 중심 + (distance + length/2) * (angle 방향 벡터)
    rad = math.radians(angle_deg)
    offset = distance + length / 2
    cx = center[0] + math.sin(rad) * offset
    cy = center[1] - math.cos(rad) * offset

    x = int(cx - rotated.width / 2)
    y = int(cy - rotated.height / 2)
    base.alpha_composite(rotated, (x, y))


def draw_sun(canvas: Image.Image, center: tuple[int, int], cfg: dict):
    """해 그리기 — 중심 원 + 광선 + 옵션 눈."""
    d = ImageDraw.Draw(canvas)

    # 광선 (원 뒤에 그려서 겹침 깔끔)
    ray_count = cfg["ray_count"]
    angle_step = 360 / ray_count
    for i in range(ray_count):
        angle = i * angle_step
        place_ray(
            canvas, center, angle,
            distance=cfg["sun_core_radius"] + cfg["ray_gap"],
            length=cfg["ray_length"],
            width=cfg["ray_width"],
            color=cfg["sun_fill"],
        )

    # 중심 원
    r = cfg["sun_core_radius"]
    d.ellipse(
        [(center[0] - r, center[1] - r), (center[0] + r, center[1] + r)],
        fill=cfg["sun_fill"],
    )

    # 눈 (옵션)
    if cfg.get("has_eyes"):
        eye_offset_x = 75
        eye_y = center[1] - 20
        eye_r = 20
        for sign in (-1, 1):
            x = center[0] + sign * eye_offset_x
            d.ellipse(
                [(x - eye_r, eye_y - eye_r), (x + eye_r, eye_y + eye_r)],
                fill=PRIMARY,
            )


def draw_submark(canvas: Image.Image, kind: str):
    """서브 브랜드 마크 (해 아래 작게)."""
    d = ImageDraw.Draw(canvas)
    if kind == "roof":
        # 집 지붕 (삼각형) — 시니어
        cx, cy = CANVAS // 2, 830
        size = 90
        d.polygon(
            [(cx - size, cy + size // 2), (cx, cy - size // 2), (cx + size, cy + size // 2)],
            fill=WHITE,
        )


def generate_icon(variant_name: str, size: int = CANVAS) -> Image.Image:
    """아이콘 1개 생성 → PIL Image (size x size)."""
    cfg = VARIANTS[variant_name]
    # 1024 기준으로 그리고 마지막에 다운스케일 (라인 품질 ↑)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), cfg["bg"] + (255,))
    center = (CANVAS // 2, CANVAS // 2)

    draw_sun(canvas, center, cfg)
    if cfg.get("submark"):
        draw_submark(canvas, cfg["submark"])

    if size != CANVAS:
        canvas = canvas.resize((size, size), Image.LANCZOS)

    return canvas


def generate_adaptive_fg(variant_name: str, size: int = 432) -> Image.Image:
    """Android 13+ Adaptive Icon foreground (투명 배경)."""
    cfg = VARIANTS[variant_name]
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    center = (CANVAS // 2, CANVAS // 2)
    draw_sun(canvas, center, cfg)
    if cfg.get("submark"):
        draw_submark(canvas, cfg["submark"])
    return canvas.resize((size, size), Image.LANCZOS)


def generate_adaptive_bg(variant_name: str, size: int = 432) -> Image.Image:
    cfg = VARIANTS[variant_name]
    return Image.new("RGBA", (size, size), cfg["bg"] + (255,))


def generate_feature_graphic() -> Image.Image:
    """Play Store Feature Graphic 1024×500."""
    W, H = 1024, 500
    img = Image.new("RGBA", (W, H), PRIMARY + (255,))

    # 그라데이션 효과 (세로 방향으로 밝아짐)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for y in range(H):
        alpha = int(60 * (y / H))  # 아래로 갈수록 살짝 어둡게
        for x in range(W):
            pass  # 간단히 스킵, 복잡하면 numpy로
    # numpy 없이 간단히: 오른쪽에 원 오브젝트만 배치
    img = img.filter(ImageFilter.GaussianBlur(0))  # no-op

    # 오른쪽에 해 아이콘 (축소판)
    icon_sm = generate_icon("master", 280)
    # 둥근 마스크 적용해서 동그랗게
    mask = Image.new("L", (280, 280), 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), (279, 279)], fill=255)
    icon_rounded = Image.new("RGBA", (280, 280), (0, 0, 0, 0))
    icon_rounded.paste(icon_sm, (0, 0), mask)
    img.paste(icon_rounded, (W - 360, H // 2 - 140), icon_rounded)

    # 텍스트
    draw = ImageDraw.Draw(img)
    # 한글 폰트 경로 시도
    font_candidates = [
        "C:/Windows/Fonts/malgunbd.ttf",     # 맑은 고딕 Bold (Windows)
        "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]
    title_font = sub_font = None
    for p in font_candidates:
        try:
            title_font = ImageFont.truetype(p, 100)
            sub_font = ImageFont.truetype(p, 28)
            break
        except Exception:
            continue
    if not title_font:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    draw.text((80, 140), "하루메이트", font=title_font, fill=WHITE)
    draw.text((80, 290), "발달장애인과 보호자를\n위한 하루 도우미",
              font=sub_font, fill=WHITE, spacing=10)

    return img


def export_android_mipmaps(out_dir: Path, variant_name: str):
    """Android 해상도별 mipmap 출력."""
    sizes = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
    for label, px in sizes.items():
        img = generate_icon(variant_name, px)
        mipmap_dir = out_dir / f"mipmap-{label}"
        mipmap_dir.mkdir(parents=True, exist_ok=True)
        img.save(mipmap_dir / "ic_launcher.png")

        # 둥근 버전도 (일부 런처용)
        mask = Image.new("L", (px, px), 0)
        ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (px - 1, px - 1)],
                                                radius=int(px * 0.22), fill=255)
        rounded = Image.new("RGBA", (px, px), (0, 0, 0, 0))
        rounded.paste(img, (0, 0), mask)
        rounded.save(mipmap_dir / "ic_launcher_round.png")


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "master"
    if variant not in VARIANTS and variant != "all":
        print(f"[X] Unknown variant: {variant}")
        print(f"    Available: {', '.join(VARIANTS)}, all")
        sys.exit(1)

    variants_to_build = list(VARIANTS) if variant == "all" else [variant]

    root = Path(__file__).resolve().parent.parent
    out_root = root / "assets" / "brand" / "icons"
    out_root.mkdir(parents=True, exist_ok=True)

    for v in variants_to_build:
        print(f"\n[+] Generating variant: {v}")
        print(f"    {VARIANTS[v]['description']}")
        vout = out_root / v
        vout.mkdir(parents=True, exist_ok=True)

        # 1024 master
        master_img = generate_icon(v, 1024)
        master_img.save(vout / "icon_1024.png")

        # 512 Play Store
        generate_icon(v, 512).save(vout / "icon_512.png")

        # Adaptive
        generate_adaptive_fg(v, 432).save(vout / "adaptive_fg.png")
        generate_adaptive_bg(v, 432).save(vout / "adaptive_bg.png")

        # Rounded preview (1024, iOS 스타일)
        mask = Image.new("L", (1024, 1024), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [(0, 0), (1023, 1023)], radius=230, fill=255
        )
        rounded = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        rounded.paste(master_img, (0, 0), mask)
        rounded.save(vout / "icon_1024_rounded.png")

        # Android mipmaps
        export_android_mipmaps(vout, v)
        print(f"    → {vout.relative_to(root)}/")

    # Feature graphic (only for master)
    if "master" in variants_to_build:
        fg = generate_feature_graphic()
        fg.save(out_root / "feature_graphic_1024x500.png")
        print(f"\n[+] Feature graphic: {(out_root / 'feature_graphic_1024x500.png').relative_to(root)}")

    print("\n[OK] Done.")


if __name__ == "__main__":
    main()
