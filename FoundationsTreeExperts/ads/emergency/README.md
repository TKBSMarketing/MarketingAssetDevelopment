# 24/7 Emergency Creative — Asset Index

Built by `../../build-emergency-ads.py`. Copy lives in `../../emergency-ad-copy.md`.

Every creative carries the phone number, a 24/7 badge, and the red emergency accent —
deliberately distinct from the blue lead-gen creative so the two sets never blur together
in the feed.

| File | Copy block | Mode | Source photo |
|------|-----------|------|--------------|
| `E1-were-awake-{4x5,9x16}.png` | E1 | Always-on | `excavator-clearing.jpg` — real dusk shot, work lights on |
| `E2-real-person-{4x5,9x16}.png` | E2 | Always-on | `david-portrait.JPEG` — David on the job |
| `E3-tree-on-your-house-{4x5,9x16}.png` | E3 | Always-on | `storm-damage-tree.jpg` — snapped trunk beside a home |
| `E4-not-a-storm-chaser-{4x5,9x16}.png` | E4 | Always-on | `crew-working.jpg` — real crew, Ann Arbor street |
| `S1-ann-arbor-got-hit-{4x5,9x16}.png` | S1 | Storm | `storm-damage-tree.jpg` (different crop) |
| `S2-today-not-next-week-{4x5,9x16}.png` | S2 | Storm | `excavator-clearing.jpg` (different crop) |
| `S3-we-answer-247-{4x5,9x16}.png` | S3 | Storm | `storm-damage.webp` — tree on car |

`S3` replaces the old `C1-storm-emergency` in `_archive/` — same proven concept, now with
the phone number on the creative.

## Formats

- **4:5 — 1080×1350** — Facebook/Instagram feed
- **9:16 — 1080×1920** — Reels and Stories. Nothing critical sits in the top 250px or
  bottom 340px, so Meta's UI never covers the headline or the phone number.

## Rebuilding / editing

```bash
python build-emergency-ads.py
```

Everything is driven by the `ads` list at the bottom of that script — headline, eyebrow,
subline, source photo, crop focus, and per-format type sizes. Useful knobs:

- `focus_x` / `focus_y` (and `_4x5` / `_9x16` overrides) — crop focal point, 0–1
- `crop_box` — fractional `(l, t, r, b)` pre-crop for when focus alone can't save a frame
- `headline_pos: "top"` / `cta_pos: "top"` — move the text block or the phone panel up
  when the subject owns the bottom of the photo (this is why E2 works)
- `trust` / `cta_top` — per-ad overrides for the two strap lines

## Not yet built

Three AI source images cover gaps the photo library genuinely can't: night work at a
house, a tree through a roof, and a night arrival. Run `../../generate-emergency-images.sh`
after `hf auth login`, then point an ad at the result with `src_override`.
