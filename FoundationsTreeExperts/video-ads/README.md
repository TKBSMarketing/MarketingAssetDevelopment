# Foundations Tree Experts — Video Ads (Remotion)

React-based video ad creative. First build: **B1 Testimonial Reel** (9:16 Reels/Stories).

## Preview live
```bash
npm run dev          # opens Remotion Studio — scrub, edit props live
```

## Render
```bash
# 9:16 Reels/Stories
npx remotion render B1-TestimonialReel out/B1-TestimonialReel.mp4

# 4:5 Feed (same template, different aspect)
npx remotion render B1-TestimonialReel-Feed out/B1-Feed.mp4
```

## Add background music
Drop a licensed track into `public/` as `music.mp3`, then render with:
```bash
npx remotion render B1-TestimonialReel out/B1-music.mp4 --props='{"musicSrc":"music.mp3"}'
```
Captions/text carry the message, so it also works silent for muted autoplay.

## Batch variants — the agency superpower
The composition is fully parameterized. Render different testimonials, phone, or
website from one template by passing `--props`:
```bash
npx remotion render B1-TestimonialReel out/variant.mp4 --props='{
  "website":"foundationstreeexperts.com",
  "phone":"(734) 474-3336",
  "testimonials":[
    {"quote":"They were perfect. Cleaned everything up. I love these guys!","name":"Dominique B.","stars":5}
  ]
}'
```
All 6 verified Google reviews live in `src/brand.ts` — swap which 3 you feature there.

## Brand source of truth
Colors, fonts (Source Serif 4 + DM Sans), phone, and website are in `src/brand.ts`,
pulled from the live website's `global.css` and `testimonials.json`.
