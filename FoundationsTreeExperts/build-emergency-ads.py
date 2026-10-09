"""
Foundations Tree Experts — 24/7 Emergency ad creative builder.

Renders each concept in emergency-ad-copy.md at 4:5 (feed) and 9:16 (Reels/Stories).

Design rules specific to emergency creative:
  - The phone number is ON the image. Emergency intent converts on a call, and the
    reader may never make it to the CTA button.
  - Red accent throughout (#DC3228) — this set is visually distinct from the blue
    lead-gen creative so the two never look like the same ad.
  - 9:16 respects Meta safe zones: nothing critical in the top 250px or bottom 340px.

    python build-emergency-ads.py
"""

import os
import base64

from PIL import Image, ImageFilter
from playwright.sync_api import sync_playwright

SRC = r"A:\TKBS Marketing - Git\Web-Hosting\foundations-tree-expertsv3\images"
OUT = r"A:\TKBS Marketing - Git\MarketingAssetDevelopment\FoundationsTreeExperts\ads\emergency"
TMP = r"C:\Users\joshh\AppData\Local\Temp\claude\a--TKBS-Marketing---Git-MarketingAssetDevelopment\54865f58-956f-49af-a813-341e90b6ca98\scratchpad\fte-emergency"

ACCENT = "#DC3228"
ACCENT_BRIGHT = "#FF4A3D"
DARK = "#0C0C0C"

PHONE = "1-833-TREE-365"

# 4:5 feed and 9:16 story. safe_top / safe_bottom keep content clear of Meta's
# platform UI on the vertical placements.
FORMATS = {
    "4x5": {"w": 1080, "h": 1350, "safe_top": 40, "safe_bottom": 40, "scale": 1.00},
    "9x16": {"w": 1080, "h": 1920, "safe_top": 250, "safe_bottom": 340, "scale": 1.10},
}


def prepped_source(path, need_w, need_h, crop_box=None):
    """Return a path to an image at least need_w x need_h, optionally pre-cropped.

    crop_box is fractional (left, top, right, bottom) of the original. Use it when
    background-position alone can't save a composition -- e.g. a subject sitting at
    the very bottom edge that the CTA panel would otherwise cover.

    Several of the crew photos are only 800x800. Upscaling inside the browser
    leaves them mushy, so pre-scale with LANCZOS and an unsharp pass instead.
    """
    img = Image.open(path)

    tag = ""
    if crop_box:
        iw, ih = img.size
        l, t, r, b = crop_box
        img = img.crop((int(l * iw), int(t * ih), int(r * iw), int(b * ih)))
        tag = "c" + "-".join(str(v) for v in crop_box) + "_"

    iw, ih = img.size
    factor = max(need_w / iw, need_h / ih)
    if factor <= 1.0 and not crop_box:
        return path

    os.makedirs(TMP, exist_ok=True)
    out_path = os.path.join(TMP, f"up_{tag}{need_w}x{need_h}_{os.path.basename(path)}.png")
    if not os.path.exists(out_path):
        img = img.convert("RGB")
        if factor > 1.0:
            img = img.resize(
                (int(iw * factor * 1.05), int(ih * factor * 1.05)), Image.LANCZOS
            )
            img = img.filter(ImageFilter.UnsharpMask(radius=2.2, percent=115, threshold=3))
        img.save(out_path, "PNG")
    return out_path


def data_uri(path):
    mime = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
    }.get(os.path.splitext(path)[1].lower(), "image/jpeg")
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def build_html(ad, fmt_name):
    fmt = FORMATS[fmt_name]
    w, h, s = fmt["w"], fmt["h"], fmt["scale"]

    src_path = ad.get("src_override") or os.path.join(SRC, ad["src"])
    if not os.path.exists(src_path):
        print(f"  !! missing source: {src_path}")
        return None

    photo = data_uri(prepped_source(src_path, w, h, ad.get("crop_box")))
    logo = data_uri(os.path.join(SRC, "logo-transparent.png"))

    fx = int(ad.get(f"focus_x_{fmt_name}", ad.get("focus_x", 0.5)) * 100)
    fy = int(ad.get(f"focus_y_{fmt_name}", ad.get("focus_y", 0.5)) * 100)

    hl_size = int(ad.get(f"hl_{fmt_name}", ad["hl"]) * s)
    top_anchored = ad.get("headline_pos") == "top"

    # More weight at the end the headline sits on, so the type always has a bed.
    if top_anchored:
        scrim = ("linear-gradient(180deg, rgba(0,0,0,.86) 0%, rgba(0,0,0,.62) 26%, "
                 "rgba(0,0,0,.10) 48%, rgba(0,0,0,.30) 74%, rgba(0,0,0,.88) 100%)")
    else:
        scrim = ("linear-gradient(180deg, rgba(0,0,0,.70) 0%, rgba(0,0,0,.28) 20%, "
                 "rgba(0,0,0,.08) 38%, rgba(0,0,0,.58) 64%, rgba(0,0,0,.94) 100%)")

    headline_html = "".join(
        f"<div>{line.upper()}</div>" for line in ad["headline"].split("\n")
    )
    subline_html = f'<div class="subline">{ad["subline"]}</div>' if ad.get("subline") else ""

    block = f"""
      <div class="headline">
        <div class="eyebrow"><span class="dot"></span>{ad["eyebrow"].upper()}</div>
        <h1>{headline_html}</h1>
        <div class="rule"></div>
        {subline_html}
      </div>"""

    cta = f"""
      <div class="cta">
        <div class="cta-top">{ad.get("cta_top", "CALL NOW — WE ANSWER 24/7")}</div>
        <div class="cta-body">
          <div class="cta-phone">{PHONE}</div>
          <div class="cta-trust">{ad.get("trust", "LICENSED · INSURED · ISA CERTIFIED · 26 YEARS")}</div>
        </div>
      </div>"""

    if ad.get("cta_pos") == "top":
        body_order = f'{block}{cta}<div class="spacer"></div>'
    elif top_anchored:
        body_order = f'{block}<div class="spacer"></div>{cta}'
    else:
        body_order = f'<div class="spacer"></div>{block}{cta}'

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@500;600;700;800&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ width:{w}px; height:{h}px; overflow:hidden;
          font-family:'Inter','Segoe UI',sans-serif; background:{DARK}; }}
  .container {{ position:relative; width:{w}px; height:{h}px; }}

  .photo {{ position:absolute; inset:0;
            background-image:url('{photo}');
            background-size:cover; background-position:{fx}% {fy}%; }}
  .scrim {{ position:absolute; inset:0; background:{scrim}; }}

  .frame {{ position:absolute; left:0; right:0;
            top:{fmt["safe_top"]}px; bottom:{fmt["safe_bottom"]}px;
            padding:{int(34*s)}px {int(52*s)}px;
            display:flex; flex-direction:column; }}
  .spacer {{ flex:1; }}

  .top-row {{ display:flex; align-items:center; justify-content:space-between; }}
  .logo {{ height:{int(94*s)}px; filter:drop-shadow(0 4px 14px rgba(0,0,0,.7)); }}

  .badge {{ display:flex; align-items:center; gap:{int(11*s)}px;
            background:rgba(10,10,10,.72); border:2px solid {ACCENT};
            border-radius:999px; padding:{int(11*s)}px {int(22*s)}px;
            font-size:{int(21*s)}px; font-weight:800; color:#fff;
            letter-spacing:.15em; backdrop-filter:blur(4px); }}
  .badge .pulse {{ width:{int(13*s)}px; height:{int(13*s)}px; border-radius:50%;
                   background:{ACCENT_BRIGHT};
                   box-shadow:0 0 0 {int(5*s)}px rgba(220,50,40,.32); }}

  .headline {{ display:flex; flex-direction:column; }}
  .eyebrow {{ display:inline-flex; align-items:center; align-self:flex-start;
              gap:{int(12*s)}px; color:{ACCENT_BRIGHT}; font-size:{int(24*s)}px;
              font-weight:800; letter-spacing:.2em; margin-bottom:{int(20*s)}px;
              background:rgba(8,8,8,.78); border-radius:999px;
              padding:{int(10*s)}px {int(20*s)}px; backdrop-filter:blur(3px); }}
  .eyebrow .dot {{ width:{int(11*s)}px; height:{int(11*s)}px; border-radius:50%;
                   background:{ACCENT_BRIGHT}; flex:none; }}

  h1 {{ font-family:'Anton',Impact,sans-serif; font-weight:400;
        font-size:{hl_size}px; line-height:.93; color:#fff;
        letter-spacing:.005em; text-shadow:0 8px 34px rgba(0,0,0,.8); }}

  .rule {{ width:{int(112*s)}px; height:{int(9*s)}px; background:{ACCENT};
           margin:{int(24*s)}px 0 0; border-radius:2px; }}
  .subline {{ margin-top:{int(20*s)}px; font-size:{int(27*s)}px; font-weight:600;
              color:#EDEFF1; line-height:1.35; max-width:{int(760*s)}px;
              text-shadow:0 2px 14px rgba(0,0,0,.9); }}

  .cta {{ margin-top:{int(30*s)}px; background:{DARK}; border-radius:{int(16*s)}px;
          overflow:hidden; box-shadow:0 {int(24*s)}px {int(64*s)}px rgba(0,0,0,.6); }}
  .cta-top {{ background:{ACCENT}; color:#fff; text-align:center;
              padding:{int(13*s)}px 0; font-size:{int(22*s)}px; font-weight:800;
              letter-spacing:.17em; }}
  .cta-body {{ padding:{int(20*s)}px 0 {int(22*s)}px; text-align:center; }}
  .cta-phone {{ font-family:'Anton',Impact,sans-serif; font-size:{int(78*s)}px;
                color:#fff; line-height:1; letter-spacing:.012em; }}
  .cta-trust {{ margin-top:{int(13*s)}px; font-size:{int(19*s)}px; font-weight:700;
                letter-spacing:.11em; color:#9BA1A6; }}
</style></head>
<body>
  <div class="container">
    <div class="photo"></div>
    <div class="scrim"></div>
    <div class="frame">
      <div class="top-row">
        <img class="logo" src="{logo}">
        <div class="badge"><span class="pulse"></span>24/7 EMERGENCY</div>
      </div>
      {body_order}
    </div>
  </div>
</body></html>"""


ads = [
    # ---------- ALWAYS-ON ----------
    {
        "id": "E1", "name": "were-awake", "mode": "always-on",
        "src": "excavator-clearing.jpg",          # real dusk shot, work lights on
        "eyebrow": "when it happens at night",
        "headline": "Trees don't fall\non a schedule.",
        "subline": "Neither do we. Day, night, weekend, holiday.",
        "hl": 92, "hl_9x16": 96,
        "focus_x": 0.55, "focus_y": 0.55,
        "focus_y_9x16": 0.6,
    },
    {
        "id": "E2", "name": "real-person", "mode": "always-on",
        "src": "david-portrait.JPEG",
        "headline_pos": "top",
        "eyebrow": "call us at 2 a.m.",
        "headline": "A real person\nanswers.",
        "subline": "No voicemail. No callback queue.",
        "hl": 92, "hl_9x16": 96,
        "cta_pos": "top",
        "focus_x": 0.18, "focus_y": 0.5,
        "focus_x_9x16": 0.22, "focus_y_9x16": 0.62,
        "cta_top": "CALL NOW — A PERSON PICKS UP",
    },
    {
        "id": "E3", "name": "tree-on-your-house", "mode": "always-on",
        "src": "storm-damage-tree.jpg",
        "eyebrow": "emergency tree removal",
        "headline": "Tree on\nyour house?",
        "subline": "Save this number before you need it.",
        "hl": 108, "hl_9x16": 112,
        "focus_x": 0.62, "focus_y": 0.58,
        "focus_x_9x16": 0.66, "focus_y_9x16": 0.6,
    },
    {
        "id": "E4", "name": "not-a-storm-chaser", "mode": "always-on",
        "src": "crew-working.jpg",                # real crew, real Ann Arbor street
        "eyebrow": "26 years in ann arbor",
        "headline": "Not a\nstorm chaser.",
        "subline": "Local crew. Licensed. Insured. Cleanup included.",
        "hl": 104, "hl_9x16": 108,
        "focus_x": 0.45, "focus_y": 0.45,
        "trust": "LOCAL · LICENSED · INSURED · ISA CERTIFIED",
    },
    # ---------- STORM-TRIGGERED ----------
    {
        "id": "S1", "name": "ann-arbor-got-hit", "mode": "storm",
        "src": "storm-damage-tree.jpg",
        "eyebrow": "storm damage · ann arbor",
        "headline": "Our crews\nare out now.",
        "subline": "Tree down? Limb on the roof? Call.",
        "hl": 100, "hl_9x16": 104,
        "focus_x": 0.34, "focus_y": 0.62,          # different crop from E3
        "focus_x_9x16": 0.38, "focus_y_9x16": 0.64,
        "cta_top": "EMERGENCY LINE — ANSWERED 24/7",
    },
    {
        "id": "S2", "name": "today-not-next-week", "mode": "storm",
        "src": "excavator-clearing.jpg",
        "eyebrow": "emergency removals triaged first",
        "headline": "Today.\nNot next week.",
        "subline": "While everyone else is booking you for Friday.",
        "hl": 104, "hl_9x16": 108,
        "focus_x": 0.28, "focus_y": 0.5,           # different crop from E1
        "focus_x_9x16": 0.32, "focus_y_9x16": 0.55,
    },
    {
        "id": "S3", "name": "we-answer-247", "mode": "storm",
        "src": "storm-damage.webp",
        "eyebrow": "tree emergency?",
        "headline": "We answer.\n24/7.",
        "subline": "Licensed. Insured. 26 years in Ann Arbor.",
        "hl": 112, "hl_9x16": 116,
        "focus_x": 0.5, "focus_y": 0.42,
        "focus_y_9x16": 0.45,
    },
]


def main():
    os.makedirs(OUT, exist_ok=True)
    built = 0

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for ad in ads:
            for fmt_name, fmt in FORMATS.items():
                html = build_html(ad, fmt_name)
                if html is None:
                    continue

                page = browser.new_page(
                    viewport={"width": fmt["w"], "height": fmt["h"]},
                    device_scale_factor=1,
                )
                page.set_content(html, wait_until="networkidle")
                page.evaluate("document.fonts.ready")
                page.wait_for_timeout(400)

                fname = f"{ad['id']}-{ad['name']}-{fmt_name}.png"
                page.screenshot(path=os.path.join(OUT, fname))
                page.close()
                print(f"  {ad['mode']:>10}  {fname}")
                built += 1

        browser.close()

    print(f"\n{built} creatives -> {OUT}")


if __name__ == "__main__":
    main()
