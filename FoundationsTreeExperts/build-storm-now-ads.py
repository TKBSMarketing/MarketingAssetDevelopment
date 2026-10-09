"""
Foundations Tree Experts — STORM NOW: 10 simple emergency variations.

Built for an active storm. Deliberately stripped back compared to the full emergency
set: hook question, action line, phone number. Nothing else competing for the two
seconds a person gives an ad while their driveway is blocked.

    python build-storm-now-ads.py
"""

import os
import base64

from PIL import Image, ImageFilter
from playwright.sync_api import sync_playwright

SRC = r"A:\TKBS Marketing - Git\Web-Hosting\foundations-tree-expertsv3\images"
OUT = r"A:\TKBS Marketing - Git\MarketingAssetDevelopment\FoundationsTreeExperts\ads\storm-now"
TMP = r"C:\Users\joshh\AppData\Local\Temp\claude\a--TKBS-Marketing---Git-MarketingAssetDevelopment\54865f58-956f-49af-a813-341e90b6ca98\scratchpad\fte-emergency"

ACCENT = "#DC3228"
ACCENT_BRIGHT = "#FF4A3D"
DARK = "#0C0C0C"

PHONE = "1-833-TREE-365"

# Meta auto-crops whatever you give it to fit a placement it has no asset for, and it
# crops to the CENTRE -- so a phone number sitting at the bottom edge of a 4:5 gets
# sliced in half in right column, Marketplace and search results. Ship a real asset for
# every shape instead of letting it crop.
FORMATS = {
    "4x5": {"w": 1080, "h": 1350, "safe_top": 40, "safe_bottom": 40, "scale": 1.00},
    "9x16": {"w": 1080, "h": 1920, "safe_top": 250, "safe_bottom": 340, "scale": 1.10},
    "1x1": {"w": 1080, "h": 1080, "safe_top": 30, "safe_bottom": 30, "scale": 0.94},
    # Right column, Marketplace, search results, in-stream. Short and wide, so the
    # phone goes on ONE line -- a stacked block is unreadable at right-column size.
    "191x1": {"w": 1200, "h": 628, "safe_top": 18, "safe_bottom": 18,
              "scale": 0.60, "wide": True},
}


def prepped_source(path, need_w, need_h):
    img = Image.open(path)
    iw, ih = img.size
    factor = max(need_w / iw, need_h / ih)
    if factor <= 1.0:
        return path

    os.makedirs(TMP, exist_ok=True)
    out_path = os.path.join(TMP, f"up_{need_w}x{need_h}_{os.path.basename(path)}.png")
    if not os.path.exists(out_path):
        img = img.convert("RGB").resize(
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

    src_path = os.path.join(SRC, ad["src"])
    if not os.path.exists(src_path):
        print(f"  !! missing source: {src_path}")
        return None

    photo = data_uri(prepped_source(src_path, w, h))
    logo = data_uri(os.path.join(SRC, "logo-transparent.png"))

    fx = int(ad.get(f"focus_x_{fmt_name}", ad.get("focus_x", 0.5)) * 100)
    fy = int(ad.get(f"focus_y_{fmt_name}", ad.get("focus_y", 0.5)) * 100)
    hl_size = int(ad.get(f"hl_{fmt_name}", ad["hl"]) * s)

    wide = fmt.get("wide", False)

    headline_html = "".join(
        f"<div>{line.upper()}</div>" for line in ad["headline"].split("\n")
    )

    # Wide placements render small, so the two-tier CTA block collapses into one
    # legible line and the copy sits in the left half clear of the photo's subject.
    if wide:
        cta_html = f'<div class="cta-wide">{ad["cta"]} &nbsp;·&nbsp; {PHONE}</div>'
        # Darken from the left instead of the bottom, so the copy column has a bed
        # and the photo still reads on the right.
        scrim_css = ("linear-gradient(90deg, rgba(0,0,0,.92) 0%, rgba(0,0,0,.82) 38%, "
                     "rgba(0,0,0,.45) 62%, rgba(0,0,0,.15) 100%)")
        frame_extra = "max-width:70%;"
    else:
        cta_html = (f'<div class="cta"><div class="cta-top">{ad["cta"]}</div>'
                    f'<div class="cta-phone">{PHONE}</div></div>')
        scrim_css = ("linear-gradient(180deg, rgba(0,0,0,.68) 0%, rgba(0,0,0,.24) 20%, "
                     "rgba(0,0,0,.06) 38%, rgba(0,0,0,.60) 64%, rgba(0,0,0,.95) 100%)")
        frame_extra = ""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ width:{w}px; height:{h}px; overflow:hidden;
          font-family:'Inter','Segoe UI',sans-serif; background:{DARK}; }}
  .container {{ position:relative; width:{w}px; height:{h}px; }}

  .photo {{ position:absolute; inset:0; background-image:url('{photo}');
            background-size:cover; background-position:{fx}% {fy}%; }}
  .scrim {{ position:absolute; inset:0; background:{scrim_css}; }}

  .frame {{ position:absolute; left:0; right:0;
            top:{fmt["safe_top"]}px; bottom:{fmt["safe_bottom"]}px;
            padding:{int(34*s)}px {int(52*s)}px;
            display:flex; flex-direction:column; {frame_extra} }}
  .spacer {{ flex:1; }}

  .top-row {{ display:flex; align-items:center; justify-content:space-between; }}
  .logo {{ height:{int(94*s)}px; filter:drop-shadow(0 4px 14px rgba(0,0,0,.7)); }}
  .badge {{ display:flex; align-items:center; gap:{int(11*s)}px;
            background:rgba(10,10,10,.72); border:2px solid {ACCENT};
            border-radius:999px; padding:{int(11*s)}px {int(22*s)}px;
            font-size:{int(21*s)}px; font-weight:800; color:#fff; letter-spacing:.15em; }}
  .badge .pulse {{ width:{int(13*s)}px; height:{int(13*s)}px; border-radius:50%;
                   background:{ACCENT_BRIGHT};
                   box-shadow:0 0 0 {int(5*s)}px rgba(220,50,40,.32); }}

  h1 {{ font-family:'Anton',Impact,sans-serif; font-weight:400;
        font-size:{hl_size}px; line-height:.93; color:#fff; text-transform:uppercase;
        letter-spacing:.005em; text-shadow:0 8px 34px rgba(0,0,0,.85);
        margin-bottom:{int(30*s)}px; }}

  .cta {{ background:{DARK}; border-radius:{int(16*s)}px; overflow:hidden;
          box-shadow:0 {int(24*s)}px {int(64*s)}px rgba(0,0,0,.6); }}
  .cta-top {{ background:{ACCENT}; color:#fff; text-align:center;
              padding:{int(15*s)}px 0; font-size:{int(30*s)}px; font-weight:800;
              letter-spacing:.14em; }}
  .cta-phone {{ padding:{int(22*s)}px 0 {int(26*s)}px; text-align:center;
                font-family:'Anton',Impact,sans-serif; font-size:{int(84*s)}px;
                color:#fff; line-height:1; letter-spacing:.02em; }}

  .cta-wide {{ align-self:flex-start; background:{ACCENT}; color:#fff;
               border-radius:{int(10*s)}px; padding:{int(16*s)}px {int(28*s)}px;
               font-family:'Anton',Impact,sans-serif; font-size:{int(58*s)}px;
               line-height:1; letter-spacing:.02em; white-space:nowrap;
               box-shadow:0 {int(16*s)}px {int(44*s)}px rgba(0,0,0,.55); }}
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
      <div class="spacer"></div>
      <h1>{headline_html}</h1>
      {cta_html}
    </div>
  </div>
</body></html>"""


# Ten hooks covering the situations people actually search during a storm:
# tree down, tree on the house, limb on the roof, blocked driveway, needing a crew tonight.
ads = [
    {"id": "V01", "name": "emergency-tree-service", "src": "storm-damage-tree.jpg",
     "headline": "Emergency tree\nservice in\nAnn Arbor?", "cta": "CALL US",
     "hl": 96, "focus_x": 0.62, "focus_y": 0.5},

    {"id": "V02", "name": "emergency-removal", "src": "storm-damage.webp",
     "headline": "Emergency tree\nremoval?", "cta": "WE'VE GOT YOU",
     "hl": 104, "focus_x": 0.5, "focus_y": 0.4},

    {"id": "V03", "name": "247-tree-service", "src": "excavator-clearing.jpg",
     "headline": "24/7 emergency\ntree service", "cta": "CALL NOW",
     "hl": 100, "focus_x": 0.55, "focus_y": 0.55},

    {"id": "V04", "name": "tree-down", "src": "storm-damage-tree.jpg",
     "headline": "Tree down near\nAnn Arbor?", "cta": "CALL US",
     "hl": 104, "focus_x": 0.3, "focus_y": 0.6},

    {"id": "V05", "name": "tree-on-house", "src": "storm-damage.webp",
     "headline": "Tree on\nyour house?", "cta": "WE'RE OUT NOW",
     "hl": 116, "focus_x": 0.42, "focus_y": 0.45},

    # climber-cutting.jpg is a bright blue autumn sky -- it flatly contradicts
    # "storm damage" while a storm is actually running. Third crop of the storm photo.
    {"id": "V06", "name": "storm-damage", "src": "storm-damage.webp",
     "headline": "Storm damage\nin Ann Arbor?", "cta": "WE ANSWER 24/7",
     "hl": 104, "focus_x": 0.9, "focus_y": 0.34},

    {"id": "V07", "name": "limb-on-roof", "src": "climber-rigging.jpg",
     "headline": "Limb on\nyour roof?", "cta": "CALL US",
     "hl": 116, "focus_x": 0.5, "focus_y": 0.42},

    # The literal version of this ad: cut logs across a wet driveway, overcast,
    # dump truck already on site.
    {"id": "V08", "name": "blocked-driveway", "src": "crew-cleanup.jpg",
     "headline": "Driveway\nblocked?", "cta": "WE'LL CLEAR IT TODAY",
     "hl": 118, "focus_x": 0.5, "focus_y": 0.55},

    {"id": "V09", "name": "crew-tonight", "src": "excavator-clearing.jpg",
     "headline": "Need a tree\ncrew tonight?", "cta": "WE'RE AWAKE",
     "hl": 104, "focus_x": 0.28, "focus_y": 0.5},

    {"id": "V10", "name": "tree-emergency", "src": "storm-damage-tree.jpg",
     "headline": "Tree\nemergency?", "cta": "CALL NOW — WE ANSWER",
     "hl": 124, "focus_x": 0.52, "focus_y": 0.42},

    # Two takes on the tree-on-car photo. V11 frames the whole car so the situation
    # reads instantly; V12 sits tighter on the trunk across the roof.
    {"id": "V11", "name": "tree-on-car", "src": "storm-damage.webp",
     "headline": "Tree on\nyour car?", "cta": "WE'LL LIFT IT OFF TODAY",
     "hl": 116, "focus_x": 0.58, "focus_y": 0.46},

    {"id": "V12", "name": "tree-on-car-alt", "src": "storm-damage.webp",
     "headline": "Tree on\nyour car?", "cta": "CALL US — WE'RE OUT NOW",
     "hl": 116, "focus_x": 0.28, "focus_y": 0.38},
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
                print(f"  {fname}")
                built += 1
        browser.close()

    print(f"\n{built} creatives -> {OUT}")


if __name__ == "__main__":
    main()
