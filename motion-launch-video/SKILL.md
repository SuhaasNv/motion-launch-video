---
name: motion-launch-video
description: Make a polished motion-graphics launch video, showreel, teaser or promo for a product, app, website or repo, built entirely in code (an HTML timeline rendered frame by frame in headless Chromium, 60 fps with motion blur, a synthesised score synced to every cut) in the product's own brand. Use this whenever someone wants a launch video, product video, promo, sizzle reel, trailer, animated demo, "a video like the PermitFlow one", or motion graphics for something they built, even if they only say "make a video for my app" or "a 20 second clip for the launch". Not for editing existing footage or screen recordings.
---

# Motion launch video

A launch film written as one HTML page whose every frame is a pure function of time, rendered at 120 fps, blended to
60 fps for real motion blur, scored with sounds placed on the exact frames that cause them. It comes out looking
designed rather than templated because it uses the product's real fonts, tokens, logo, copy and UI.

Output: `<name>.mp4` (1920x1080, 60 fps, H.264 + AAC), `<name>-poster.jpg`, `<name>-web.mp4` (720p30, a couple of MB for sites).

## Files in this skill

| Path | Use |
|---|---|
| `scripts/setup.sh` | Finds or installs ffmpeg (libx264), Chromium, playwright-core, numpy/scipy. `eval "$(bash scripts/setup.sh <work>)"` |
| `assets/film_template.html` | Runnable 10 s film: timeline engine, brand tokens, mark build, clipped wipe, UI card scene, zoom-through, end card. Start here. |
| `assets/score_template.py` | Score for the template film, cue by cue. Start here for sound. |
| `scripts/render.mjs` | `stills` (PNG per time) and `full` (120 fps chunks, parallel workers) |
| `scripts/sheet.sh`, `scripts/sample.sh` | Contact sheets from stills; frames sampled from the final MP4 |
| `scripts/assemble.sh` | Frame-pair blend to 60 fps, mux score, poster, web copy |
| `scripts/score_engine.py` | Instruments + `Score` (drums, harmony, sidechain, reverb, master) |
| `references/motion-playbook.md` | Storyboard grammar, easing, transition and moment recipes, the bugs to check for. Read before writing scenes. |
| `references/sound-design.md` | Music structure and the event-to-sound table. Read before writing the score. |
| `references/example-permitflow/` | The complete 20 s film and score this skill came from. Read when you want a full worked example. |

## Workflow

### 1. Study the product (before drawing anything)
Find, in the repo or site: the design tokens (colours, radii), the font files (woff2/ttf, check the licence allows
embedding; open fonts usually do), the logo SVG and its geometry, the landing-page headline and taglines, the real
screens and their labels, status names and identifiers, the URL, and any legal line (fictional service, beta).
Screenshots of the real product help you rebuild UI accurately. The film should only show things the product really does.

### 2. Storyboard on a beat grid and confirm it
Default 20 s at 120 BPM (a beat every 0.5 s). Use the grammar in `references/motion-playbook.md` section 1: cold open
with the mark building, the drop into the wordmark, three to five one-idea scenes (headline from the product's own copy,
one italic accent word, a rebuilt product surface doing one thing), a payoff, an end card. Write it as a short table
(time, scene, headline, what moves, transition). If the user is around, show the storyboard in a few lines before building;
if they asked you to just go, go.

### 3. Set up the work folder
```bash
WORK=<somewhere writable, e.g. the scratchpad>/film && mkdir -p $WORK/fonts
eval "$(bash <skill>/scripts/setup.sh $WORK)"          # exports FFMPEG, CHROME_PATH, NODE_PATH
cp <skill>/assets/film_template.html $WORK/film.html
cp <skill>/assets/score_template.py $WORK/score.py
cp <product fonts> $WORK/fonts/                         # and point the @font-face rules at them
```

### 4. Build the film
Edit `film.html`: brand tokens and fonts, the logo strokes (`pathLength="1"` so `dash()` draws them), then scenes.
Keep the contract, because the renderer depends on it: `window.DUR`, `window.seek(t, frame)`, `window.fontsReady`; every
visual property computed from `t`; no CSS transitions or animations, no `Date.now()`, no `Math.random()` (use `hash()`).
Any frame must render identically whether you visit it first or last, because four workers render out of order.
Wrap scenes that a wipe crosses in transform-free full-frame wrappers and clip those.

### 5. Review with contact sheets, fix, repeat
```bash
node <skill>/scripts/render.mjs stills film.html 0.5,1.5,2.4,... stills && bash <skill>/scripts/sheet.sh stills sheet.png
```
Pick times at every transition's start, middle and end and at every payoff, then read the sheet image. Go through the checklist at the
end of the playbook (early reveals under wipes, overlapping headlines, mask peeking, odometers, clustered markers).
Crop and read single frames at full size where text is small. Two or three rounds is normal.

### 6. Score it
Retime `score.py` to the film: read the start times out of the `A(t, a, b)` calls so each sound shares the frame of its
event. Structure and the event-to-sound table are in `references/sound-design.md`. `python3 score.py` prints RMS/peak
per 2 s: the intro and outro quieter than the middle, no clipping.

### 7. Render and assemble
```bash
node <skill>/scripts/render.mjs full film.html render 120 4      # about 2 to 5 min for 20 s on 4 cores
bash <skill>/scripts/assemble.sh render score.wav <name> [posterTime]
bash <skill>/scripts/sample.sh <name>.mp4 check 3.0,9.5,16.9 && bash <skill>/scripts/sheet.sh check check.png
```
Review the sampled frames from the encode itself: blur, blending and compression only show up there.

### 8. Deliver
Send the MP4 (and poster) to the user. Say what the film shows, scene by scene, in a few lines, and be plain about the
limits: nobody has listened to the score yet (you can't hear it), and headless Chromium here can't play H.264, so playback
was checked with ffprobe and sampled frames rather than a player. Offer the next steps rather than doing them unasked: committing the
film and its source to the repo (use Git LFS if the repo tracks video that way), a web copy on their site, a vertical 1080x1920
cut (set `window.SIZE`, re-lay the scenes), or a version with their own music.

## Design judgement

- The brand's rules outrank this skill's defaults. If the design system says no gradients, keep the glows subtle or drop them;
  if red means "error", don't flood the wipe with it; keep status colours and labels exactly as the product uses them.
- Prefer fewer, bigger things on screen. At 1080p a 22 px label is small; anything that must be read wants 26 px or more and time on screen.
- Motion should explain the product: a row completing, a document checked, a value changing, a status advancing. Decorative motion
  (particles, glows, grain) supports, never leads.
- Readability beats speed. Hold each headline for at least one beat after it lands.
- Don't add HUD chrome (timecodes, corner labels, progress bars) unless asked.
