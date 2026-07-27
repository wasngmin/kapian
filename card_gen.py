"""
Card image generator — cloud-compatible version.
Uses Pillow. Fonts auto-detected (Windows / Linux / macOS).
"""

import os
from PIL import Image, ImageDraw, ImageFont

# ── Colors ──────────────────────────────────────────────────────
BG_TOP    = (232, 244, 252)
BG_BOTTOM = (200, 228, 248)
WHITE     = (255, 255, 255, 255)
DARK      = (42, 50, 60)
GRAY      = (130, 138, 148)
LGRAY     = (180, 186, 194)
XLGRAY    = (210, 214, 220)

POINT_COLORS = {
    "blue":   {"accent": "#3B82F6", "bar": "#3B82F6"},
    "amber":  {"accent": "#D97706", "bar": "#F59E0B"},
    "coral":  {"accent": "#EA580C", "bar": "#F97316"},
    "teal":   {"accent": "#0D9488", "bar": "#14B8A6"},
    "purple": {"accent": "#7C3AED", "bar": "#8B5CF6"},
    "rose":   {"accent": "#E11D48", "bar": "#F43F5E"},
    "slate":  {"accent": "#475569", "bar": "#64748B"},
}

WEATHER_DOT = {
    "晴": (255, 185, 60), "少云": (255, 200, 80), "多云": (200, 200, 220),
    "阴": (160, 170, 190), "雨": (80, 150, 230), "雷": (80, 150, 230),
    "雪": (180, 200, 220), "雾": (170, 180, 195),
}

# ── Dimensions ──────────────────────────────────────────────────
W = 750
PAD = 28
CARD_W = W - PAD * 2
TOP_BAR_H = 52

# ── Font discovery ──────────────────────────────────────────────
FONT_PATHS = {
    "regular": [],
    "bold": [],
    "light": [],
}

def _discover_fonts():
    """Find available Chinese fonts on the system."""
    if os.name == "nt":  # Windows
        FONT_PATHS["regular"] = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc"]
        FONT_PATHS["bold"] = ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"]
        FONT_PATHS["light"] = ["C:/Windows/Fonts/msyhl.ttc", "C:/Windows/Fonts/msyh.ttc"]
    else:  # Linux / macOS
        FONT_PATHS["regular"] = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        FONT_PATHS["bold"] = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
            "/System/Library/Fonts/PingFang.ttc",
        ]
        FONT_PATHS["light"] = FONT_PATHS["regular"]

_discover_fonts()

_cache = {}

def _safe(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        pass

def _find_font(weight="regular"):
    for p in FONT_PATHS.get(weight, FONT_PATHS["regular"]):
        if os.path.exists(p):
            return p
    # Fallback: try the first regular font for all weights
    for p in FONT_PATHS["regular"]:
        if os.path.exists(p):
            return p
    return None

def f(size, w="regular"):
    k = (size, w)
    if k not in _cache:
        fp = _find_font(w)
        if fp:
            _cache[k] = ImageFont.truetype(fp, size)
        else:
            _cache[k] = ImageFont.load_default()
    return _cache[k]

def tw(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)[2]

def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if tw(draw, cur + ch, font) <= max_w:
            cur += ch
        else:
            if cur: lines.append(cur)
            cur = ch
    if cur: lines.append(cur)
    return lines

def _hex(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def gradient(draw, x0, y0, x1, y1, c1, c2):
    h = y1 - y0
    for i in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * i / h)
        g = int(c1[1] + (c2[1] - c1[1]) * i / h)
        b = int(c1[2] + (c2[2] - c1[2]) * i / h)
        draw.line([(x0, y0 + i), (x1, y0 + i)], fill=(r, g, b))


def generate(config, output_path):
    points = config.get("points", [])
    insight_lines = config.get("insight_lines", [])
    weather = config.get("weather") or {}

    # ── Height calculation ────────────────────────────────────
    # Use a dummy draw to measure text wrapping
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))

    point_content_h = 0
    for pt in points:
        cl = len(wrap(dummy, pt.get("content", ""), f(15), CARD_W - 90))
        ex = pt.get("example", "")
        el = len(wrap(dummy, f"e.g. {ex}", f(13), CARD_W - 90)) if ex else 0
        h = 16 + 22 + max(cl, 1) * 20 + (el * 18 + 4 if el else 0) + 14
        point_content_h += h

    card_pad_top, card_pad_bot = 20, 20
    content_card_h = card_pad_top + point_content_h + card_pad_bot

    insight_card_h = 0
    if insight_lines:
        insight_card_h = 16 + 24 + len(insight_lines) * 22 + 16

    gap1, gap2 = 16, 16
    title_area_h = 80
    content_card_y = TOP_BAR_H + title_area_h
    insight_y = content_card_y + content_card_h + gap1
    footer_y = insight_y + insight_card_h + (gap2 if insight_card_h else gap1)
    total_h = footer_y + 56 + 24

    # ── Canvas ────────────────────────────────────────────────
    img = Image.new("RGBA", (W, total_h), BG_TOP + (255,))
    draw = ImageDraw.Draw(img)
    gradient(draw, 0, 0, W, total_h, BG_TOP, BG_BOTTOM)

    # Decorative circles
    for cx, cy, r, a in [(80, 100, 120, 8), (680, 400, 80, 5), (40, 500, 60, 6)]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(180, 210, 240, a))

    # ── Top bar ───────────────────────────────────────────────
    cat = config.get("category", "")
    if cat:
        fc = f(14, "bold")
        cw = tw(draw, cat, fc) + 24
        ch, cy = 28, 14
        draw.rounded_rectangle([PAD, cy, PAD + cw, cy + ch], radius=14,
                               fill=(255, 255, 255, 90), outline=(255, 255, 255, 60), width=1)
        draw.text((PAD + 12, cy + 7), cat, fill=(42, 50, 60) + (200,), font=fc)

    # Date (right)
    date_str = config.get("date", "")
    if date_str:
        fdt = f(15, "light")
        draw.text((W - PAD - tw(draw, date_str, fdt), 15), date_str,
                  fill=(80, 90, 100) + (200,), font=fdt)

    # Weather (right, below date)
    if weather.get("text"):
        wx_text = weather.get("text", "")
        fwx = f(13, "light")
        cond = weather.get("icon", "")
        dot_color = (130, 160, 200)
        for k, v in WEATHER_DOT.items():
            if k in cond:
                dot_color = v
                break
        draw.ellipse([W - PAD - 4, 36, W - PAD + 4, 44], fill=dot_color + (220,))
        wf = f"{weather.get('city', '南宁')} {wx_text}"
        draw.text((W - PAD - tw(draw, wf, fwx) - 14, 35), wf,
                  fill=(100, 110, 120) + (180,), font=fwx)

    # ── Title (centered) ──────────────────────────────────────
    title = config.get("title", "")
    if title:
        ftt = f(38, "bold")
        tt_w = tw(draw, title, ftt)
        draw.text(((W - tt_w) // 2, TOP_BAR_H + 12), title, fill=DARK, font=ftt)

    # Subtitle (centered)
    subtitle = config.get("subtitle", "")
    if subtitle:
        fst = f(17, "light")
        st_w = tw(draw, subtitle, fst)
        if st_w > CARD_W - 40:
            subtitle = subtitle[:len(subtitle) // 2] + "..."
            st_w = tw(draw, subtitle, fst)
        draw.text(((W - st_w) // 2, TOP_BAR_H + 56), subtitle, fill=GRAY, font=fst)

    # ── Content card ──────────────────────────────────────────
    draw.rounded_rectangle([PAD + 2, content_card_y + 2, W - PAD + 2, content_card_y + content_card_h + 2],
                           radius=16, fill=(200, 210, 220, 100))
    draw.rounded_rectangle([PAD, content_card_y, W - PAD, content_card_y + content_card_h],
                           radius=16, fill=WHITE)

    py = content_card_y + card_pad_top
    for idx, pt in enumerate(points):
        pc = POINT_COLORS.get(pt.get("color", "blue"), POINT_COLORS["blue"])

        # Number badge
        draw.text((PAD + 22, py), f"{idx+1:02d}", fill=_hex(pc["accent"]), font=f(18, "bold"))

        # Point title
        draw.text((PAD + 56, py + 1), pt.get("title", ""), fill=DARK, font=f(18, "bold"))

        # Point content
        cl = wrap(draw, pt.get("content", ""), f(15), CARD_W - 90)
        for i, line in enumerate(cl[:2]):
            draw.text((PAD + 56, py + 27 + i * 20), line, fill=GRAY, font=f(15))

        # Example
        example = pt.get("example", "")
        if example:
            ex_y = py + 27 + min(len(cl), 2) * 20 + 2
            draw.text((PAD + 56, ex_y), f"e.g. {example}", fill=LGRAY, font=f(13))

        el = 1 if example else 0
        point_h = 16 + 22 + max(len(cl), 1) * 20 + (el * 18 + 4 if el else 0) + 10

        if idx < len(points) - 1:
            sep_y = py + point_h - 2
            draw.line([PAD + 56, sep_y, W - PAD - 24, sep_y], fill=XLGRAY, width=1)

        py += point_h

    # ── Insight card ──────────────────────────────────────────
    if insight_lines:
        draw.rounded_rectangle([PAD + 2, insight_y + 2, W - PAD + 2, insight_y + insight_card_h + 2],
                               radius=12, fill=(200, 210, 220, 80))
        draw.rounded_rectangle([PAD, insight_y, W - PAD, insight_y + insight_card_h],
                               radius=12, fill=WHITE)
        draw.rounded_rectangle([PAD, insight_y + 12, PAD + 4, insight_y + insight_card_h - 12],
                               radius=2, fill=_hex("#8B5CF6"))
        draw.text((PAD + 18, insight_y + 16),
                  config.get("insight_title", "核心洞察"), fill=_hex("#7C3AED"), font=f(17, "bold"))
        for i, line in enumerate(insight_lines):
            draw.text((PAD + 18, insight_y + 44 + i * 22), line, fill=DARK, font=f(15))

    # ── Footer ────────────────────────────────────────────────
    ff = f(13, "light")
    source = config.get("source", "")
    footer_label = config.get("footer", "每日房产知识卡片")
    if source:
        draw.text((PAD, footer_y + 10), source, fill=LGRAY, font=ff)
    if footer_label:
        fw = tw(draw, footer_label, ff)
        draw.text((W - PAD - fw, footer_y + 10), footer_label, fill=LGRAY, font=ff)

    ai_note = config.get("ai_note", "内容由 AI 精选生成")
    if ai_note:
        draw.text((PAD, footer_y + 32), ai_note, fill=(190, 195, 200) + (200,), font=f(12, "light"))

    # ── Save ──────────────────────────────────────────────────
    img = img.convert("RGB")
    img.save(output_path, "PNG", optimize=True)
    return output_path
