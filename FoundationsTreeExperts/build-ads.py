from PIL import Image, ImageDraw, ImageFont
import os

SRC = r"A:\TKBS Marketing - Git\Web-Hosting\foundations-tree-expertsv3\images"
OUT = r"A:\TKBS Marketing - Git\MarketingAssetDevelopment\FoundationsTreeExperts\ads"
os.makedirs(OUT, exist_ok=True)

TARGET_W, TARGET_H = 1080, 1350

BRAND_BLUE = (0, 153, 255)
DARK_BG = (12, 12, 12)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
ACCENT_RED = (220, 50, 40)

def load_font_by_name(name, size):
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

def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def text_height(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]

def crop_focus_fill(img, tw, th, focus_y=0.5, focus_x=0.5, zoom=1.0):
    iw, ih = img.size
    scale = max(tw / iw, th / ih) * zoom
    new_w, new_h = int(iw * scale), int(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = int((new_w - tw) * focus_x)
    left = max(0, min(left, new_w - tw))
    top = int((new_h - th) * focus_y)
    top = max(0, min(top, new_h - th))
    return img.crop((left, top, left + tw, top + th))


def build_ad(ad):
    print(f"Building {ad['id']} - {ad['name']}...")

    # --- LOAD FONTS ---
    hl_size = ad.get("headline_size", 72)
    font_headline = load_font_by_name("impact", hl_size)
    font_subhead = load_font_by_name("arial_bold", 32)
    font_cta = load_font_by_name("arial_bold", 28)
    font_test = load_font_by_name("segoe", 24)
    font_test_attr = load_font_by_name("segoe_bold", 22)

    # --- MEASURE TOP BAR HEIGHT ---
    # We need a temp draw to measure text
    tmp = Image.new("RGB", (TARGET_W, 100))
    tmp_draw = ImageDraw.Draw(tmp)

    headline_lines = ad["headline"].split("\n")
    line_sizes = ad.get("line_sizes", [hl_size] * len(headline_lines))
    line_spacing_list = [s + 8 for s in line_sizes]
    headline_block_h = sum(line_spacing_list)

    font_top_sub = load_font_by_name("arial_bold", 26)

    # Top bar: accent line + padding + headline + (optional subhead) + padding
    accent_thickness = 4
    top_pad = 20
    bot_pad = 16
    top_subhead_h = 0
    if ad.get("top_subhead"):
        top_subhead_h = 34
    top_bar_h = accent_thickness + top_pad + headline_block_h + top_subhead_h + bot_pad

    # Logo will be overlaid on the photo, not in the top bar
    logo_img = Image.open(os.path.join(SRC, "logo-transparent.png")).convert("RGBA")
    logo_h = 130
    logo_ratio = logo_h / logo_img.height
    logo_w = int(logo_img.width * logo_ratio)
    logo_img = logo_img.resize((logo_w, logo_h), Image.LANCZOS)

    # --- MEASURE BOTTOM BAR HEIGHT ---
    no_bottom = ad.get("no_bottom", False)
    if no_bottom:
        bottom_bar_h = 0
    else:
        cta_bar_h = 56
        subhead_h = 44
        bottom_pad = 22
        top_pad_bottom = 22
        bottom_bar_h = top_pad_bottom + subhead_h + bottom_pad + cta_bar_h

        if ad.get("testimonial"):
            test_lines = ad["testimonial_lines"]
            testimonial_block_h = len(test_lines) * 30 + 34 + 12
            bottom_bar_h += testimonial_block_h

    # --- PHOTO AREA ---
    photo_h = TARGET_H - top_bar_h - bottom_bar_h

    # --- LOAD AND CROP PHOTO ---
    src_path = ad.get("src_override") or os.path.join(SRC, ad["src"])
    if not os.path.exists(src_path):
        print(f"  Skipping - file not found: {src_path}")
        return
    photo = Image.open(src_path).convert("RGB")
    focus_y = ad.get("focus_y", 0.5)
    focus_x = ad.get("focus_x", 0.5)
    zoom = ad.get("zoom", 1.15)
    photo = crop_focus_fill(photo, TARGET_W, photo_h, focus_y=focus_y, focus_x=focus_x, zoom=zoom)

    # --- BUILD CANVAS ---
    canvas = Image.new("RGBA", (TARGET_W, TARGET_H), DARK_BG)

    # --- DRAW TOP BAR ---
    draw = ImageDraw.Draw(canvas)

    # Background
    draw.rectangle([(0, 0), (TARGET_W, top_bar_h)], fill=DARK_BG)

    # Accent line at very top
    accent_color = ACCENT_RED if ad.get("urgent") else BRAND_BLUE
    draw.rectangle([(0, 0), (TARGET_W, accent_thickness)], fill=accent_color)

    # Headline starts after accent + padding
    hl_y = accent_thickness + top_pad
    for i, line in enumerate(headline_lines):
        line_upper = line.upper()
        line_font = load_font_by_name("impact", line_sizes[i])
        lw = text_width(draw, line_upper, line_font)
        lx = (TARGET_W - lw) // 2
        draw.text((lx, hl_y), line_upper, font=line_font, fill=WHITE)
        hl_y += line_spacing_list[i]

    if ad.get("top_subhead"):
        ts_text = ad["top_subhead"]
        ts_w = text_width(draw, ts_text, font_top_sub)
        ts_x = (TARGET_W - ts_w) // 2
        draw.text((ts_x, hl_y + 4), ts_text, font=font_top_sub, fill=accent_color)

    # Accent line at bottom of top bar
    draw.rectangle([(0, top_bar_h - accent_thickness), (TARGET_W, top_bar_h)], fill=accent_color)

    # --- PASTE PHOTO ---
    canvas.paste(photo.convert("RGBA"), (0, top_bar_h))

    # --- LOGO overlaid on photo, top-left ---
    logo_x = 20
    logo_y = top_bar_h + 16
    if ad.get("logo_backdrop"):
        backdrop_pad = 12
        backdrop = Image.new("RGBA", (logo_w + backdrop_pad * 2, logo_h + backdrop_pad * 2), (0, 0, 0, 64))
        canvas.paste(backdrop, (logo_x - backdrop_pad, logo_y - backdrop_pad), backdrop)
    canvas.paste(logo_img, (logo_x, logo_y), logo_img)
    draw = ImageDraw.Draw(canvas)

    # --- DRAW BOTTOM BAR ---
    if not no_bottom:
        bottom_bar_top = top_bar_h + photo_h
        draw.rectangle([(0, bottom_bar_top), (TARGET_W, TARGET_H)], fill=DARK_BG)

        # Accent line at top of bottom bar
        draw.rectangle([(0, bottom_bar_top), (TARGET_W, bottom_bar_top + accent_thickness)], fill=accent_color)

        # Subhead centered
        subhead_y = bottom_bar_top + accent_thickness + top_pad_bottom
        sw = text_width(draw, ad["subhead"], font_subhead)
        sx = (TARGET_W - sw) // 2
        draw.text((sx, subhead_y), ad["subhead"], font=font_subhead, fill=accent_color)

        # Testimonial (if present)
        next_y = subhead_y + subhead_h
        if ad.get("testimonial"):
            test_y = next_y + 8
            for line in ad["testimonial_lines"]:
                tw = text_width(draw, line, font_test)
                tx = (TARGET_W - tw) // 2
                draw.text((tx, test_y), line, font=font_test, fill=LIGHT_GRAY)
                test_y += 30
            attr = ad["testimonial_attr"]
            aw = text_width(draw, attr, font_test_attr)
            ax = (TARGET_W - aw) // 2
            draw.text((ax, test_y + 2), attr, font=font_test_attr, fill=accent_color)
            next_y = test_y + 34

        # CTA button bar at very bottom
        cta_bar_top = TARGET_H - cta_bar_h
        draw.rectangle([(0, cta_bar_top), (TARGET_W, TARGET_H)], fill=accent_color)
        cta_text = ad["cta"]
        cta_tw = text_width(draw, cta_text, font_cta)
        cta_x = (TARGET_W - cta_tw) // 2
        cta_y = cta_bar_top + (cta_bar_h - 28) // 2
        draw.text((cta_x, cta_y), cta_text, font=font_cta, fill=WHITE)

    # --- SAVE ---
    out_path = os.path.join(OUT, f"{ad['id']}-{ad['name']}.png")
    canvas = canvas.convert("RGB")
    canvas.save(out_path, "PNG")
    print(f"  Saved: {out_path}")


# --- AD DEFINITIONS ---

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
        "id": "B2-alt",
        "name": "make-the-call-alt",
        "src": "crew-cleanup.jpg",
        "headline": "You've Waited Long Enough.\nMake the Call.",
        "headline_size": 62,
        "subhead": "ANN ARBOR  ·  FREE ESTIMATES",
        "cta": "CALL NOW",
        "focus_y": 0.3,
        "focus_x": 0.4,
    },
    {
        "id": "B2-alt2",
        "name": "make-the-call-fallen",
        "src_override": r"A:\TKBS Marketing - Git\MarketingAssetDevelopment\FoundationsTreeExperts\images\storm-damage-tree.jpg",
        "headline": "You've Waited Long Enough.\nMake the Call.",
        "headline_size": 62,
        "subhead": "ANN ARBOR  ·  FREE ESTIMATES",
        "cta": "CALL NOW",
        "focus_y": 0.5,
        "focus_x": 0.5,
    },
    {
        "id": "B4",
        "name": "zero-mess",
        "src": "crew-working.jpg",
        "headline": "Tree Removal.\nZero Mess Left Behind.",
        "headline_size": 90,
        "line_sizes": [90, 56],
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
        "testimonial": True,
        "testimonial_lines": [
            '"Professional, fast and polite.',
            'I will never use any other company."',
        ],
        "testimonial_attr": "-- Eddie K.  |  5-Star Review",
    },
    # --- 10% DISCOUNT PROMO (Expires June 15) ---
    {
        "id": "D1",
        "name": "save-10-percent",
        "src": "climber-chainsaw.JPEG",
        "headline": "Save 10%\nBook by June 15th",
        "headline_size": 80,
        "line_sizes": [80, 62],
        "top_subhead": "ANN ARBOR  ·  TREE REMOVAL & TRIMMING",
        "no_bottom": True,
        "focus_y": 0.4,
        "focus_x": 0.4,
    },
    {
        "id": "D2",
        "name": "10-off-tree-removal",
        "src": "crew-working.jpg",
        "headline": "10% Off\nTree Removal",
        "headline_size": 90,
        "line_sizes": [90, 70],
        "top_subhead": "BOOK BY JUNE 15TH  ·  ANN ARBOR",
        "no_bottom": True,
        "logo_backdrop": True,
        "focus_y": 0.4,
        "focus_x": 0.5,
    },
    {
        "id": "D3",
        "name": "dont-wait-save-10",
        "src": "climber-cutting.jpg",
        "headline": "Don't Wait.\nSave 10%.",
        "headline_size": 80,
        "line_sizes": [80, 80],
        "top_subhead": "TREE REMOVAL  ·  ENDS JUNE 15TH  ·  ANN ARBOR",
        "no_bottom": True,
        "logo_backdrop": True,
        "focus_y": 0.6,
        "focus_x": 0.4,
    },
    {
        "id": "D4",
        "name": "10-off-cleanup-included",
        "src": "crew-cleanup.jpg",
        "headline": "10% Off.\nCleanup Included.",
        "headline_size": 80,
        "line_sizes": [80, 56],
        "top_subhead": "BOOK BY JUNE 15TH  ·  ANN ARBOR",
        "no_bottom": True,
        "logo_backdrop": True,
        "focus_y": 0.3,
        "focus_x": 0.4,
    },
]

for ad in ads:
    build_ad(ad)

print(f"\nDone! {len(ads)} ads built.")
