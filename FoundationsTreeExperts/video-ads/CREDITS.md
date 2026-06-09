# Credits & Licenses

## Music
**"Sincerely"** — Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0 License
https://creativecommons.org/licenses/by/4.0/

> ⚠️ **Attribution required.** CC-BY means you must credit the artist wherever the
> video is published. Put this line in the post caption / video description:
>
> ```
> Music: "Sincerely" by Kevin MacLeod (incompetech.com) — CC BY 4.0
> ```
>
> To avoid the credit line entirely, you can buy a one-time "no attribution"
> license for this track at incompetech.com (~$30). Then this requirement goes away.

Source file trimmed to 14s with fade in/out → `public/music.mp3`.

### Swap the track
Two other pre-vetted warm instrumentals (same CC-BY terms) are ready to swap in:
- **"Carefree"** — lighter, friendly ukulele/acoustic
- **"Wholesome"** — warm, positive acoustic

```bash
curl.exe -4 -L -A "Mozilla/5.0" \
  "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Carefree.mp3" \
  -o public/music-source.mp3
ffmpeg -y -i public/music-source.mp3 -t 14 \
  -af "afade=t=in:st=0:d=0.5,afade=t=out:st=12.6:d=1.4" -ar 44100 -b:a 192k \
  public/music.mp3
```

## Brand assets
Logo, colors, fonts, and testimonials sourced from the live Foundations Tree
Experts website (`Single Hosted Websites/Foundations-Tree-Experts`).
