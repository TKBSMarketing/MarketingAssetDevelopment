from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

SRC = r"A:\TKBS Marketing - Git\Web-Hosting\foundations-tree-expertsv3\images"
OUT_V1 = r"A:\TKBS Marketing - Git\MarketingAssetDevelopment\FoundationsTreeExperts\ads\v1-raw"
OUT_V2 = r"A:\TKBS Marketing - Git\MarketingAssetDevelopment\FoundationsTreeExperts\ads\v2-split"
OUT_V3 = r"A:\TKBS Marketing - Git\MarketingAssetDevelopment\FoundationsTreeExperts\ads\v3-magazine"
for d in [OUT_V1, OUT_V2, OUT_V3]:
    os.makedirs(d, exist_ok=True)

TARGET_W, TARGET_H = 1080, 1350

BRAND_BLUE = (0, 153, 255)
DARK_BG = (12, 12, 12)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
ACCENT_RED = (220, 50, 40)

def load_font(name, size):
    paths = {
        "impact": r"C:\Windows\Fonts\impact.ttf",
        "arial_bold": r"C:\Windows\Fonts\arialbd.ttf",
        "arial": r"C:\Windows\Fonts\arial.ttf",
        "arial_black": r"C:\Windows\Fonts\ariblk.ttf",
        "segoe_bold": r"C:\Windows\Fonts\segoeuib.ttf",
        "segoe": r"C:\Windows\Fonts\segoeui.ttf",
    }
    path = paths.get(name)
    if path and os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def tw(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def th(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]

def crop_focus(img, w, h, fy=0.5, fx=0.5, zoom=1.15):
    iw, ih = img.size
    scale = max(w / iw, h / ih) * zoom
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = max(0, min(int((nw - w) * fx), nw - w))
    top = max(0, min(int((nh - h) * fy), nh - h))
    return img.crop((left, top, left + w, top + h))

def load_logo(size=100):
    logo = Image.open(os.path.join(SRC, "logo-transparent.png")).convert("RGBA")
    r = size / logo.height
    return logo.resize((int(logo.width * r), size), Image.LANCZOS)

def shadow_text(draw, pos, text, font, fill=WHITE, shadow=(0,0,0), offset=3, blur=False):
    x, y = pos
    for dx in range(-offset, offset+1):
        for dy in range(-offset, offset+1):
            draw.text((x+dx, y+dy), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)

def outline_text(draw, pos, text, font, fill=WHITE, outline=(0,0,0), width=4):
    x, y = pos
    for dx in range(-width, width+1):
        for dy in range(-width, width+1):
            if dx*dx + dy*dy <= width*width:
                draw.text((x+dx, y+dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


# ============================================================
# VARIATION 1: RAW — Full bleed photo, text overlaid directly
# No panels. Massive text with heavy outline. Raw and authentic.
# ============================================================
def build_v1_raw(ad):
    print(f"  V1-RAW: {ad['id']}...")

    src_path = ad.get("src_override") or os.path.join(SRC, ad["src"])
    if not os.path.exists(src_path):
        print(f"    Skipping - file not found")
        return

    photo = Image.open(src_path).convert("RGB")
    img = crop_focus(photo, TARGET_W, TARGET_H,
                     fy=ad.get("focus_y", 0.5), fx=ad.get("focus_x", 0.5), zoom=1.2)
    img = img.convert("RGBA")

    # Darken the whole image slightly for text contrast
    dark = Image.new("RGBA", img.size, (0, 0, 0, 60))
    img = Image.alpha_composite(img, dark)

    # Bottom vignette for subhead area
    vig = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for y in range(TARGET_H - 300, TARGET_H):
        alpha = int(180 * ((y - (TARGET_H - 300)) / 300))
        vd.line([(0, y), (TARGET_W, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img, vig)

    draw = ImageDraw.Draw(img)

    # Headline — massive, centered, with heavy outline
    hl_size = ad.get("headline_size", 72)
    # Scale up for this raw style
    raw_size = int(hl_size * 1.3)
    font_hl = load_font("impact", raw_size)
    lines = ad["headline"].split("\n")
    line_h = raw_size + 10

    total_h = len(lines) * line_h
    start_y = (TARGET_H - total_h) // 2 - 60

    accent = ACCENT_RED if ad.get("urgent") else BRAND_BLUE

    for line in lines:
        upper = line.upper()
        lw = tw(draw, upper, font_hl)
        lx = (TARGET_W - lw) // 2
        outline_text(draw, (lx, start_y), upper, font_hl, fill=WHITE, outline=(0,0,0), width=5)
        start_y += line_h

    # Subhead — bottom area
    font_sub = load_font("arial_bold", 34)
    sub = ad["subhead"]
    sw = tw(draw, sub, font_sub)
    sx = (TARGET_W - sw) // 2
    shadow_text(draw, (sx, TARGET_H - 140), sub, font_sub, fill=accent, shadow=(0,0,0), offset=2)

    # CTA — very bottom
    font_cta = load_font("arial_bold", 30)
    cta = ad["cta"]
    cw = tw(draw, cta, font_cta)
    cx = (TARGET_W - cw) // 2
    shadow_text(draw, (cx, TARGET_H - 90), cta, font_cta, fill=WHITE, shadow=(0,0,0), offset=2)

    # Logo top-left
    logo = load_logo(100)
    img.paste(logo, (20, 20), logo)

    # Thin accent line at very bottom
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, TARGET_H - 6), (TARGET_W, TARGET_H)], fill=accent)

    img.convert("RGB").save(os.path.join(OUT_V1, f"{ad['id']}-{ad['name']}.png"), "PNG")


# ============================================================
# VARIATION 2: SPLIT — Angled split, photo + color block
# Photo on top-right, brand color block bottom-left with text
# ============================================================
def build_v2_split(ad):
    print(f"  V2-SPLIT: {ad['id']}...")

    src_path = ad.get("src_override") or os.path.join(SRC, ad["src"])
    if not os.path.exists(src_path):
        print(f"    Skipping - file not found")
        return

    photo = Image.open(src_path).convert("RGB")
    img = crop_focus(photo, TARGET_W, TARGET_H,
                     fy=ad.get("focus_y", 0.5), fx=ad.get("focus_x", 0.5), zoom=1.3)

    canvas = Image.new("RGBA", (TARGET_W, TARGET_H), DARK_BG)
    canvas.paste(img.convert("RGBA"), (0, 0))

    # Create angled color block overlay on bottom portion
    accent = ACCENT_RED if ad.get("urgent") else BRAND_BLUE
    overlay = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # Angled polygon — covers bottom-left ~45% of image
    split_y = int(TARGET_H * 0.52)
    skew = 120
    od.polygon([
        (0, split_y + skew),       # top-left (lower)
        (TARGET_W, split_y - skew), # top-right (higher)  -- creates the angle
        (TARGET_W, TARGET_H),       # bottom-right
        (0, TARGET_H),              # bottom-left
    ], fill=(*accent, 230))

    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    # Thin white line along the diagonal edge
    for i in range(3):
        draw.line([
            (0, split_y + skew - i),
            (TARGET_W, split_y - skew - i)
        ], fill=WHITE, width=1)

    # Logo on the color block
    logo = load_logo(90)
    logo_y = split_y + skew + 15
    canvas.paste(logo, (40, logo_y), logo)

    # Headline on the color block
    hl_size = ad.get("headline_size", 72)
    font_hl = load_font("impact", int(hl_size * 1.1))
    lines = ad["headline"].split("\n")
    line_h = int(hl_size * 1.1) + 8

    hl_y = logo_y + 100
    for line in lines:
        upper = line.upper()
        lw = tw(draw, upper, font_hl)
        lx = (TARGET_W - lw) // 2
        draw.text((lx, hl_y), upper, font=font_hl, fill=WHITE)
        hl_y += line_h

    # Subhead
    font_sub = load_font("arial_bold", 30)
    sub = ad["subhead"]
    sw = tw(draw, sub, font_sub)
    sx = (TARGET_W - sw) // 2
    draw.text((sx, hl_y + 20), sub, font=font_sub, fill=DARK_BG)

    # CTA at bottom
    cta_h = 56
    cta_top = TARGET_H - cta_h
    draw.rectangle([(0, cta_top), (TARGET_W, TARGET_H)], fill=DARK_BG)
    font_cta = load_font("arial_bold", 28)
    cta = ad["cta"]
    cw = tw(draw, cta, font_cta)
    cx = (TARGET_W - cw) // 2
    draw.text((cx, cta_top + 14), cta, font=font_cta, fill=WHITE)

    canvas.convert("RGB").save(os.path.join(OUT_V2, f"{ad['id']}-{ad['name']}.png"), "PNG")


# ============================================================
# VARIATION 3: MAGAZINE — Breaking-news style banner across photo
# Full bleed photo with a bold horizontal band across the center
# ============================================================
def build_v3_magazine(ad):
    print(f"  V3-MAG: {ad['id']}...")

    src_path = ad.get("src_override") or os.path.join(SRC, ad["src"])
    if not os.path.exists(src_path):
        print(f"    Skipping - file not found")
        return

    photo = Image.open(src_path).convert("RGB")
    img = crop_focus(photo, TARGET_W, TARGET_H,
                     fy=ad.get("focus_y", 0.5), fx=ad.get("focus_x", 0.5), zoom=1.15)
    canvas = img.convert("RGBA")

    accent = ACCENT_RED if ad.get("urgent") else BRAND_BLUE
    draw = ImageDraw.Draw(canvas)

    # Measure headline to size the banner
    hl_size = ad.get("headline_size", 72)
    mag_size = int(hl_size * 1.15)
    font_hl = load_font("impact", mag_size)
    lines = ad["headline"].split("\n")
    line_h = mag_size + 8
    headline_block_h = len(lines) * line_h

    # Banner — horizontal band across upper-center
    banner_pad = 24
    banner_h = headline_block_h + banner_pad * 2
    banner_top = int(TARGET_H * 0.12)

    # Semi-transparent dark banner
    banner = Image.new("RGBA", (TARGET_W, banner_h), (0, 0, 0, 210))
    canvas.paste(banner, (0, banner_top), banner)

    # Accent lines top and bottom of banner
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0, banner_top), (TARGET_W, banner_top + 5)], fill=accent)
    draw.rectangle([(0, banner_top + banner_h - 5), (TARGET_W, banner_top + banner_h)], fill=accent)

    # Headline text centered in banner
    hl_y = banner_top + banner_pad
    for line in lines:
        upper = line.upper()
        lw = tw(draw, upper, font_hl)
        lx = (TARGET_W - lw) // 2
        draw.text((lx, hl_y), upper, font=font_hl, fill=WHITE)
        hl_y += line_h

    # Logo — top-left above the banner
    logo = load_logo(90)
    canvas.paste(logo, (20, 16), logo)

    # Bottom section — dark bar with subhead + CTA
    bottom_h = 130
    bottom_top = TARGET_H - bottom_h

    # Gradient into bottom bar
    grad = Image.new("RGBA", (TARGET_W, 60), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(60):
        alpha = int(220 * (y / 60))
        gd.line([(0, y), (TARGET_W, y)], fill=(12, 12, 12, alpha))
    canvas.paste(grad, (0, bottom_top - 60), grad)

    # Solid bottom
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0, bottom_top), (TARGET_W, TARGET_H)], fill=DARK_BG)

    # Subhead
    font_sub = load_font("arial_bold", 32)
    sub = ad["subhead"]
    sw = tw(draw, sub, font_sub)
    sx = (TARGET_W - sw) // 2
    draw.text((sx, bottom_top + 12), sub, font=font_sub, fill=accent)

    # CTA bar
    cta_h = 56
    cta_top = TARGET_H - cta_h
    draw.rectangle([(0, cta_top), (TARGET_W, TARGET_H)], fill=accent)
    font_cta = load_font("arial_bold", 28)
    cta = ad["cta"]
    cw = tw(draw, cta, font_cta)
    cx = (TARGET_W - cw) // 2
    draw.text((cx, cta_top + 14), cta, font=font_cta, fill=WHITE)

    canvas.convert("RGB").save(os.path.join(OUT_V3, f"{ad['id']}-{ad['name']}.png"), "PNG")


# ============================================================
# AD DEFINITIONS (same as main build)
# ============================================================

ads = [
    {
        "id": "A4",
        "name": "is-that-tree-safe",
        "src": "climber-chainsaw.JPEG",
        "headline": "Is That Tree Safe?",
        "headline_size": 80,
        "subhead": "GET AN ARBORIST ASSESSMENT  ·  ANN ARBOR",
        "cta": "BOOK YOUR ASSESSMENT",
        "focus_y": 0.4,
        "focus_x": 0.4,
    },
    {
        "id": "B1",
        "name": "not-a-diy-job",
        "src": "climber-rigging.jpg",
        "headline": "This Isn't\na DIY Job.",
        "headline_size": 80,
        "subhead": "ANN ARBOR'S TRUSTED TREE EXPERTS",
        "cta": "FREE ESTIMATES",
        "focus_y": 0.4,
        "focus_x": 0.5,
    },
    {
        "id": "B2",
        "name": "make-the-call",
        "src": "climber-cutting.jpg",
        "headline": "You've Waited Long Enough.\nMake the Call.",
        "headline_size": 62,
        "subhead": "ANN ARBOR  ·  FREE ESTIMATES",
        "cta": "CALL NOW",
        "focus_y": 0.6,
        "focus_x": 0.4,
    },
    {
        "id": "B4",
        "name": "zero-mess",
        "src": "crew-working.jpg",
        "headline": "Tree Removal.\nZero Mess Left Behind.",
        "headline_size": 70,
        "subhead": "ANN ARBOR  ·  CLEANUP INCLUDED",
        "cta": "FREE ESTIMATE",
        "focus_y": 0.4,
        "focus_x": 0.5,
    },
    {
        "id": "C1",
        "name": "storm-emergency",
        "src": "storm-damage.webp",
        "headline": "We Answer. 24/7.",
        "headline_size": 88,
        "subhead": "ANN ARBOR  ·  EMERGENCY TREE REMOVAL",
        "cta": "CALL NOW",
        "focus_y": 0.4,
        "focus_x": 0.5,
        "urgent": True,
    },
    {
        "id": "R2",
        "name": "retargeting-testimonial",
        "src": "climber-action.jpg",
        "headline": "Join Your Neighbors",
        "headline_size": 80,
        "subhead": "FREE ESTIMATE  ·  ANN ARBOR",
        "cta": "GET YOUR FREE QUOTE",
        "focus_y": 0.35,
        "focus_x": 0.55,
    },
]

print("=== Building V1: RAW ===")
for ad in ads:
    build_v1_raw(ad)

print("\n=== Building V2: SPLIT ===")
for ad in ads:
    build_v2_split(ad)

print("\n=== Building V3: MAGAZINE ===")
for ad in ads:
    build_v3_magazine(ad)

print(f"\nDone! 3 variations x {len(ads)} ads = {len(ads)*3} total")
