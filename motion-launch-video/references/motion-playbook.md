# Motion playbook

Recipes for a code-driven launch film. Every snippet assumes the engine in `assets/film_template.html`
(`A`, `P`, `E`, `tf`, `dash`, `reveal`, `hide`, `scramble`, `pulse`, `hash`). Everything is a pure function of `t`.

## Contents
1. Storyboard grammar
2. Timing and easing
3. Transitions (wipe, zoom-through, whip pan, carry-over, zoom into a detail)
4. Moments inside a scene (mark build, decode, odometer, scan, status timeline, stamp, sheen, audit log)
5. Atmosphere
6. Review loop and the bugs that actually happened

---

## 1. Storyboard grammar

A 20 s film at 120 BPM is 40 beats. Cut on beats (multiples of 0.5 s) so the score and the picture agree.

| Beat range | Job | Typical content |
|---|---|---|
| 0 to 2 s | Cold open, no drums | The mark builds itself from a dot. A burst when it completes. |
| 2 to 4 s | Drop, identity | Wordmark rises letter by letter, category line decodes under it. |
| 4 to 16 s | 3 to 5 idea scenes, 2.5 to 3.5 s each | One headline (display face, one italic accent word) + one product surface rebuilt from the real UI doing one thing. |
| 16 to 18 s | Payoff | The outcome the product produces (a certificate, a report, a shipped state), landed with weight. |
| 18 to 20 s | End card | Mark + wordmark, tagline, URL, any legal line. Held still enough to read. |

Rules that made the PermitFlow reel work:
- **One idea per scene.** Headline says it, the UI shows it happening. If a scene needs two sentences, split it.
- **Headlines come from the product's own copy** (landing page, README, pitch). The italic accent word is the verb or promise ("once.", "flagged.", "on record.").
- **Rebuild UI in HTML, don't screenshot it.** Real labels, real statuses, real identifiers, the product's tokens. Rebuilt UI can animate (rows tick, badges swap, values roll); screenshots can only slide.
- **Carry objects across cuts.** The flagged document in scene 2 became the hero of scene 3. Continuity reads as craft.
- **Leave a beat of stillness** after each payoff (about 0.3 to 0.6 s) before the exit starts.
- **No persistent HUD** (corner labels, timecode, progress bars) unless asked. The owner of the PermitFlow reel had it removed; it reads as template chrome, not product.

## 2. Timing and easing

- Entrances: `outExpo` (fast in, long settle), 0.6 to 0.8 s for type, 0.5 to 0.9 s for cards.
- Exits: `inExpo`, 0.3 to 0.45 s. Exits are faster than entrances.
- Pops (badges, check circles, seals): `outBack` or `spring`, clamp scale to about 1.2 so overshoot never looks broken.
- Camera pans that must keep things in view: `inOutCubic`/`inOutSine`. Avoid `inOutQuart`/`inOutExpo` for anything that has markers along it: the middle rushes and the markers fire almost at once.
- Stagger text at 0.03 to 0.04 s per character, 0.05 to 0.08 s per word.
- Slow push-in on every scene: `s: 1 + 0.03..0.05 * A(t, start, end, 'lin')`. Static frames look dead.

## 3. Transitions

### Diagonal slab wipe (clip both scenes, or the new scene shows through early)
Wrap each scene in a full-frame `div` without transforms (`#wA`, `#wB`) and clip the wrappers, not the scenes (a scene's own scale/blur would move the clip). With `skewX(-14deg)` around the slab's centre (y = 540), an edge at translate `x` runs from `x + 134.6` at the top to `x - 134.6` at the bottom.
```js
const lead=Math.min(x1,x2,x3), trail=Math.max(x1+w1,x2+w2,x3+w3), k=134.6;
wOut.style.clipPath=`polygon(0 0,${lead+k}px 0,${lead-k}px 1080px,0 1080px)`;
wIn.style.clipPath =`polygon(${trail+k}px 0,1920px 0,1920px 1080px,${trail-k}px 1080px)`;
```
Three slabs (neutral, brand, thin accent) staggered by about 0.05 s look layered.

### Zoom-through
Outgoing: `s *= 1 + ex*0.35`, `blur: ex*14`, opacity out over the last 0.14 s. Incoming: `s` from 0.85 to 1, blur 12 to 0.
**Delay the incoming headline** until the outgoing one is gone (about 0.1 s after its opacity reaches 0), or the two headlines overlap mid-zoom.

### Whip pan
Outgoing `x: -ex*1500`, incoming `x: (1-en)*1500`, both with `blur: sin(ex*PI)*16`. The 120 to 60 fps frame blend turns this into real motion blur. Nudge the background dot grid by a few hundred px too, so the world moves, not just the cards.

### Carry an object across the cut (FLIP-style)
Interpolate the element from its old rect to the new scene's rect (translate + scale, `inOutExpo`, about 0.6 s) while the rest of the old scene falls away, then cross-fade into the new scene's version of it over the last 0.2 s. Aspect changes are hidden by the cross-fade.

### Zoom into a detail
Set the scene's `transform-origin` to the detail's on-screen position (account for any pan), then `s: 1 + ex*2.4` with `inExpo`. The next scene lands with a spring.

## 4. Moments inside a scene

### The mark builds itself
Dot (`outBack` pop), stretches into a line (width, `inOutExpo`), grows into the rounded square (height, `outExpo`), radius eases from pill to the logo's radius. Then the glyph strokes draw with `dash()` on `pathLength="1"` paths, 0.1 to 0.14 s apart. On completion: `pulse()` squash, a ring (`scale 0.55 to 2.6`, fading), 18 rays with `hash()` jitter. Then slide and scale into the lockup position measured after fonts load.

### Decode (scramble)
`el.textContent = scramble('FEL-2026-000005', t, start, 0.03, 30)`. Mono font only (widths must not jump). Good for identifiers, category lines, scene labels.

### Odometer
A container `overflow:hidden; height: <row>px`, containing an **absolutely positioned** column of digit rows with explicit pixel heights; translate the column, never the container.
```css
.odo{display:block;overflow:hidden;height:40px;line-height:40px;width:.62em;position:relative}
.odo .col{position:absolute;left:0;top:0;width:100%} .odo span{display:block;height:40px}
```
Give the strip enough rows for the whole roll (48 to 62 passes row 22; build 30).

### Scan beam
A 3 px line with a coloured glow (`box-shadow: 0 0 18px 4px`) moving down a preview area, a translucent fill following it, status line swapping Queued, Checking (spinner rotated by `t*720`, indeterminate bar), result. Cascade several items 0.35 s apart. A failing item: amber outline, a glow `pulse()`, a short horizontal shake `sin(t*90)*9*pulse`, and a highlighter wiping over the offending line.

### Status timeline with camera follow
A track wider than the frame; a white rule draws with `inOutSine`; each node fires when the eased rule reaches it (invert the easing by bisection); the track pans with `inOutCubic` so the head stays in view. Nodes pop a badge above, a caption below, a halo ring. A log list beside it adds one line per node, scrolling so the newest four stay visible.

### Stamp / seal
Scale 2.6 to 1, rotate -40 to -10, blur 6 to 0 with `inExpo` (it accelerates into the paper), then a damped shake of the card `exp(-(t-t0)*9)*sin((t-t0)*60)`, a white overlay flash, and an impact in the score.

### Sheen
A rotated 260 px band with a white gradient, `mix-blend-mode: soft-light`, sweeping across a card once after it lands.

## 5. Atmosphere

Dark stage from the brand's darkest neutral; two blurred radial glows in the brand colour drifting on slow sines; a 48 px dot grid at 7 % opacity drifting; a vignette (about 0.42 at the corners, stronger makes white cards look grey); canvas grain at 960x540 upscaled, `overlay` at about 7.5 %, reseeded per frame. A white `overlay` flash `pulse()` on the drop and on the payoff.

## 6. Review loop and the bugs that actually happened

Render stills at the risky moments (every transition start, middle and end; every payoff), tile them with `sheet.sh`, and read the sheet. Then sample the **final encode** with `sample.sh`, because the blend and the encoder can show things the page does not.

Bugs from the PermitFlow build, all caught on contact sheets:
- New scene visible before the wipe reached it: clip both scenes to the slab edges (section 3).
- Two headlines overlapping during a zoom-through: delay the incoming reveal.
- Glyph tops peeking out under their mask before the reveal: start hidden words at 150 % (not 110 %); the mask has 0.2 em of bottom padding for descenders.
- Odometer blank, then showing two digits: translate an inner column, not the clipped container; don't make the column a flex item (it shrinks); give it enough rows.
- Status badges firing almost together: the rule used `inOutQuart`; use `inOutSine`.
- Stray elements of the incoming scene over the outgoing one during a whip: acceptable if it is under 0.2 s and both are moving; otherwise delay the incoming scene's visibility.
- Headless Chromium from Playwright cannot decode H.264, so `<video>` checks there always fail: verify MP4s with ffprobe and sampled frames instead.
