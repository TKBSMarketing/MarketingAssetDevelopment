# Storm Now — Asset Index

Built by `../../build-storm-now-ads.py`. Copy lives in `../../storm-now-copy.md`.

12 concepts × 4 aspect ratios = 48 files.

## Why four ratios

**Meta crops to the centre.** If you upload only a 4:5 and Meta needs a 1.91:1 for right
column, Marketplace, search results or in-stream, it takes the middle band of your image and
throws away the top and bottom. A phone number sitting at the bottom edge gets sliced in half
— which is exactly what happened to `V04-tree-down` in right column on 4 Sept 2026.

| Ratio | Pixels | Placements |
|---|---|---|
| `4x5` | 1080×1350 | Facebook + Instagram feed |
| `9x16` | 1080×1920 | Reels, Stories |
| `1x1` | 1080×1080 | Marketplace, Explore, some feed variants |
| `191x1` | 1200×628 | Right column, search results, in-stream, Audience Network |

In Ads Manager: **Edit per placement** on the creative, and assign the matching ratio to each.
Uploading one asset and letting Advantage+ crop is what causes this.

## The design rules that follow from it

1. **Never put the phone number in the outer 15% of a tall creative** if there's any chance
   it gets auto-cropped. The 4:5 and 9:16 here still bottom-anchor it, which is correct for
   feed — but only because dedicated wide assets exist so they're never cropped.
2. **Wide formats get a one-line CTA.** The stacked red-bar-over-phone block is unreadable at
   right-column size (~254px wide displayed). `191x1` collapses it to
   `CALL US · 1-833-TREE-365` on a single line.
3. **Wide formats scrim from the left, not the bottom** — the copy needs a bed on the left
   half while the photo still reads on the right.

## Rebuilding

```bash
python build-storm-now-ads.py
```

The `ads` list at the bottom drives everything. `FORMATS` at the top controls ratios; a format
with `"wide": True` gets the single-line CTA and left-weighted scrim automatically.

## Still to do

The 14 creatives in `../emergency/` have the same flaw — 4:5 and 9:16 only, phone number at the
bottom edge. They'll crop the same way if they run on right column. `build-emergency-ads.py`
needs the same `FORMATS` treatment.
