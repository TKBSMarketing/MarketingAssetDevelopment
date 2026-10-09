#!/usr/bin/env bash
# Foundations Tree Experts — AI source images for the 24/7 emergency ad set.
#
# The photo library covers most of this set already (real dusk shot with work lights,
# real snapped trunk beside a house, real crew on an Ann Arbor street). These three
# fill the gaps nothing in the library can: night work AT a home, a tree through a
# roof, and a night arrival.
#
# PREREQ: hf session expires periodically. Run this first, in your own terminal:
#     hf auth login
#
# Then:
#     bash generate-emergency-images.sh
#
# Windows note: results are downloaded with curl.exe -4. IPv6 DNS to CloudFront
# flakes on this machine and the download silently fails without it.

set -uo pipefail

OUT="A:/TKBS Marketing - Git/MarketingAssetDevelopment/FoundationsTreeExperts/images/ai-emergency"
mkdir -p "$OUT"

# Text-to-image on gpt_image_2 — no reference upload, so this path avoids the
# flaky CloudFront upload PUT entirely.
gen() {
  local name="$1" ratio="$2" prompt="$3"
  echo ""
  echo "=== $name ($ratio) ==="
  local json
  json=$(hf generate create gpt_image_2 \
    --prompt "$prompt" \
    --aspect_ratio "$ratio" \
    --quality high \
    --resolution 2k \
    --batch_size 2 \
    --wait --json 2>&1) || { echo "$json"; return 1; }

  echo "$json" | grep -oE 'https://[^"]+\.(png|jpg|jpeg|webp)' | sort -u | nl -w2 -s' ' |
  while read -r i url; do
    curl.exe -4 -sSL "$url" -o "$OUT/${name}-v${i}.png" && echo "  -> $OUT/${name}-v${i}.png"
  done
}

STYLE="Photorealistic documentary photograph, shot on a full-frame DSLR at 35mm, natural imperfect framing like a real phone photo from the scene, no text, no logos, no watermarks, no visible brand names on clothing or vehicles."

# 1. Night work at a home — the gap the excavator dusk shot can't fill (that one is
#    in the woods; this one has to read as somebody's house).
gen "night-crew-at-house" "4:5" \
"A residential Michigan neighborhood at night after a storm. A large fallen oak limb rests across the roof of a single-story suburban house. Portable work floodlights on tripods light the scene, cutting through light rain and mist. Wet asphalt reflects the light. Two workers in high-visibility jackets and hard hats stand near the base of the limb assessing it. Dark sky, no moon. Cold blue ambient light against warm floodlight. $STYLE"

# 2. Tree through a roof — the visceral 'this is happening to my house' image.
#    storm-damage-tree.jpg shows a trunk beside a house, never through one.
gen "tree-through-roof" "4:5" \
"Storm aftermath at a two-story suburban Michigan home in early morning grey light. A large tree trunk has fallen directly into the roof, breaking through the shingles near the gable end, branches splayed across the siding and gutter. Debris and torn branches scattered on the wet lawn. Overcast sky, drizzle. No people in frame. $STYLE"

# 3. Night arrival — for the 'we show up tonight' angle.
gen "night-arrival" "9:16" \
"A tree service pickup truck with an equipment trailer pulling up on a dark residential street at night after a storm, headlights on, amber warning light bar glowing on the cab roof. Wet pavement, fallen branches across the road in the foreground, houses with lit windows in the background. Rain in the headlight beams. $STYLE"

echo ""
echo "Done. Review the outputs, pick the strongest of each pair, then wire them into"
echo "build-emergency-ads.py with a src_override pointing at the chosen file."
