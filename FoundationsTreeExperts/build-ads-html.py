import os
import base64
from playwright.sync_api import sync_playwright

SRC = r"A:\TKBS Marketing - Git\Web-Hosting\foundations-tree-expertsv3\images"
LOCAL_IMG = r"A:\TKBS Marketing - Git\MarketingAssetDevelopment\FoundationsTreeExperts\images"
OUT = r"A:\TKBS Marketing - Git\MarketingAssetDevelopment\FoundationsTreeExperts\ads\html"
os.makedirs(OUT, exist_ok=True)

WIDTH, HEIGHT = 1080, 1350

BRAND_BLUE = "#0099FF"
ACCENT_RED = "#DC3228"


def img_to_data_uri(path):
    ext = os.path.splitext(path)[1].lower()
    mime = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
    }.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


def build_html(ad):
    src_path = ad.get("src_override") or os.path.join(SRC, ad["src"])
    if not os.path.exists(src_path):
        print(f"  Skipping {ad['id']} - file not found: {src_path}")
        return None

    logo_path = os.path.join(SRC, "logo-transparent.png")
    photo_uri = img_to_data_uri(src_path)
    logo_uri = img_to_data_uri(logo_path)

    accent = ACCENT_RED if ad.get("urgent") else BRAND_BLUE
    focus_x = int(ad.get("focus_x", 0.5) * 100)
    focus_y = int(ad.get("focus_y", 0.5) * 100)

    headline_lines = ad["headline"].split("\n")
    line_sizes = ad.get("line_sizes", [ad.get("headline_size", 72)] * len(headline_lines))

    headline_html = ""
    for i, line in enumerate(headline_lines):
        size = line_sizes[i]
        headline_html += f'<div class="hl-line" style="font-size:{size}px; line-height:{size + 6}px;">{line.upper()}</div>\n'

    top_subhead_html = ""
    if ad.get("top_subhead"):
        top_subhead_html = f'<div class="top-subhead"><span class="subhead-pill">{ad["top_subhead"]}</span></div>'

    show_logo = not ad.get("no_logo", False)

    testimonial_html = ""
    if ad.get("testimonial"):
        lines_html = "".join(f'<div class="test-line">{l}</div>' for l in ad["testimonial_lines"])
        testimonial_html = f"""
        <div class="testimonial-badge">
            {lines_html}
            <div class="test-attr">{ad["testimonial_attr"]}</div>
        </div>"""

    no_bottom = ad.get("no_bottom", False)
    bottom_html = ""

    gradient_top = "rgba(0,0,0,0.85)"
    gradient_bottom = "rgba(0,0,0,0.0)"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Inter:wght@500;600;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: {WIDTH}px;
    height: {HEIGHT}px;
    overflow: hidden;
    font-family: 'Inter', sans-serif;
  }}

  .container {{
    width: {WIDTH}px;
    height: {HEIGHT}px;
    position: relative;
    background: #0c0c0c;
  }}

  .photo {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: url('{photo_uri}');
    background-size: cover;
    background-position: {focus_x}% {focus_y}%;
  }}

  .photo-overlay {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(
      to bottom,
      {gradient_top} 0%,
      rgba(0,0,0,0.5) 22%,
      rgba(0,0,0,0.05) 40%,
      rgba(0,0,0,0.0) 60%,
      {gradient_bottom} 100%
    );
  }}

  .top-section {{
    position: absolute;
    top: 0; left: 0; right: 0;
    padding: 60px 48px 20px;
    text-align: center;
    z-index: 10;
  }}

  .accent-line {{
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 5px;
    background: {accent};
  }}

  .hl-line {{
    font-family: 'Oswald', Impact, sans-serif;
    font-weight: 700;
    color: white;
    text-transform: uppercase;
    letter-spacing: 2px;
    text-shadow:
      0 2px 8px rgba(0,0,0,0.7),
      0 0 40px rgba(0,0,0,0.5);
  }}

  .top-subhead {{
    margin-top: 12px;
    text-align: center;
  }}

  .subhead-pill {{
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 20px;
    color: white;
    letter-spacing: 3px;
    background: rgba(0,0,0,0.45);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    padding: 8px 20px;
    border-radius: 8px;
    border: 1px solid {accent}40;
    display: inline-block;
  }}

  .logo-container {{
    position: absolute;
    top: 200px;
    left: 24px;
    z-index: 20;
  }}

  .logo-backdrop {{
    background: rgba(0,0,0,0.35);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-radius: 16px;
    padding: 12px;
    display: inline-block;
    border: 1px solid rgba(255,255,255,0.08);
  }}

  .logo-backdrop img {{
    width: 100px;
    height: auto;
    display: block;
  }}

  .testimonial-badge {{
    position: absolute;
    bottom: 220px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0,0,0,0.5);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 18px 32px;
    text-align: center;
    z-index: 10;
    border: 1px solid rgba(255,255,255,0.1);
    max-width: 90%;
  }}

  .test-line {{
    font-family: 'Inter', sans-serif;
    font-size: 20px;
    color: #e0e0e0;
    line-height: 1.5;
    font-style: italic;
  }}

  .test-attr {{
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 18px;
    color: {accent};
    margin-top: 8px;
    font-style: normal;
  }}
</style>
</head>
<body>
  <div class="container">
    <div class="photo"></div>
    <div class="photo-overlay"></div>

    <div class="accent-line"></div>

    <div class="top-section">
      {headline_html}
      {top_subhead_html}
    </div>

    {'<div class="logo-container"><div class="logo-backdrop"><img src="' + logo_uri + '" alt="logo"></div></div>' if show_logo else ''}

    {testimonial_html}
  </div>
</body>
</html>"""


ads = [
    {
        "id": "A4",
        "name": "is-that-tree-safe",
        "src": "climber-chainsaw.JPEG",
        "headline": "Is That Tree Safe?",
        "headline_size": 80,
        "top_subhead": "GET AN ARBORIST ASSESSMENT  ·  ANN ARBOR",
        "no_bottom": True,
        "focus_y": 0.4,
        "focus_x": 0.4,
    },
    {
        "id": "B1",
        "name": "not-a-diy-job",
        "src": "climber-rigging.jpg",
        "headline": "This Isn't\na DIY Job.",
        "headline_size": 80,
        "top_subhead": "ANN ARBOR'S TRUSTED TREE EXPERTS",
        "no_bottom": True,
        "focus_y": 0.4,
        "focus_x": 0.5,
    },
    {
        "id": "B2",
        "name": "make-the-call",
        "src": "climber-cutting.jpg",
        "headline": "You've Waited Long Enough.\nMake the Call.",
        "headline_size": 62,
        "top_subhead": "ANN ARBOR  ·  FREE ESTIMATES",
        "no_bottom": True,
        "focus_y": 0.6,
        "focus_x": 0.4,
    },
    {
        "id": "B2-alt",
        "name": "make-the-call-alt",
        "src": "crew-cleanup.jpg",
        "headline": "You've Waited Long Enough.\nMake the Call.",
        "headline_size": 62,
        "top_subhead": "ANN ARBOR  ·  FREE ESTIMATES",
        "no_bottom": True,
        "focus_y": 0.3,
        "focus_x": 0.4,
    },
    {
        "id": "B2-alt2",
        "name": "make-the-call-fallen",
        "src_override": os.path.join(LOCAL_IMG, "storm-damage-tree.jpg"),
        "headline": "You've Waited Long Enough.\nMake the Call.",
        "headline_size": 62,
        "top_subhead": "ANN ARBOR  ·  FREE ESTIMATES",
        "no_bottom": True,
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
        "top_subhead": "ANN ARBOR  ·  CLEANUP INCLUDED",
        "no_bottom": True,
        "focus_y": 0.4,
        "focus_x": 0.5,
    },
    {
        "id": "C1",
        "name": "storm-emergency",
        "src": "storm-damage.webp",
        "headline": "We Answer. 24/7.",
        "headline_size": 88,
        "top_subhead": "ANN ARBOR  ·  EMERGENCY TREE REMOVAL",
        "no_bottom": True,
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
        "top_subhead": "FREE ESTIMATE  ·  ANN ARBOR",
        "no_bottom": True,
        "focus_y": 0.35,
        "focus_x": 0.55,
        "testimonial": True,
        "testimonial_lines": [
            '"Professional, fast and polite.',
            'I will never use any other company."',
        ],
        "testimonial_attr": "-- Eddie K.  |  5-Star Review",
    },
    # --- 10% DISCOUNT PROMO ---
    {
        "id": "D1",
        "name": "save-10-percent",
        "src": "climber-chainsaw.JPEG",
        "headline": "Save 10%\nBook by June 15th",
        "headline_size": 80,
        "line_sizes": [80, 62],
        "top_subhead": "ANN ARBOR  ·  TREE REMOVAL & TRIMMING",
        "no_bottom": True,
        "no_logo": True,
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
        "no_logo": True,
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
        "no_logo": True,
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
        "no_logo": True,
        "focus_y": 0.3,
        "focus_x": 0.4,
    },
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})

        for ad in ads:
            print(f"Building {ad['id']} - {ad['name']}...")
            html = build_html(ad)
            if html is None:
                continue

            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(500)

            out_path = os.path.join(OUT, f"{ad['id']}-{ad['name']}.png")
            page.screenshot(path=out_path, type="png")
            print(f"  Saved: {out_path}")

        browser.close()

    print(f"\nDone! {len(ads)} ads built.")


if __name__ == "__main__":
    main()
