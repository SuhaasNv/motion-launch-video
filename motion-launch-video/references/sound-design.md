# Sound design

The score is synthesised by `scripts/score_engine.py` (numpy + scipy, deterministic, no samples). It is written
cue by cue against the film's own clock, so every sound lands on the frame that causes it.

## Structure (20 s, 120 BPM, 4-chord loop, one chord per 2 s bar)

| Time | Music | Why |
|---|---|---|
| 0 to 2 s | Riser only (filtered noise + rising sweep) | Tension while the mark builds |
| 2.0 s | The drop: first kick is bigger, white flash on the picture | Identity lands with the wordmark |
| 2 to 16 s | Kick every beat, claps on 2 and 4 from bar 2, off-beat hats, bass eighths, pad per bar | Drive under the idea scenes |
| busiest stretch | 16th arpeggio + 16th shaker | Energy while the most happens on screen |
| about 1.2 s before the payoff | Drums drop out, sustained pad + riser | A breath so the payoff hits harder |
| payoff | Impact + snare + bell, drums back | Weight |
| end card | Band out, one chord with a long tail, a few bells, a tick on the URL | Resolution; quiet enough to read |

Default harmony: A minor, `roots=[45, 41, 48, 43]` (A F C G), chords `[[57,60,64],[53,57,60],[55,60,64],[55,59,62]]`.
For a brighter product use C major (`roots=[48,43,45,41]`, chords C G Am F); for a darker, technical one, stay in A minor and drop the arp.

## Mapping visual events to sounds

| On screen | Sound (engine call) |
|---|---|
| Dot appears, UI click, value tick | `tick(f, 0.02..0.05)` |
| Line or card sweeps in, wipe, whip, zoom | `whoosh(d, lo, hi, rise)`; falling (`rise=False`) for zoom-outs and exits |
| Strokes drawing, rows completing | `pluck(m)` rising through the chord (76, 79, 83, 88...) |
| Verified, resolved, success | `bell(m)` high (84 to 93), a little reverb |
| Warning, issue found | two `pluck`s a semitone apart, low (62, 63), plus a soft kick |
| Burst, stamp, big landing | `impact()` (+ `snare()` for a stamp) |
| Counters rolling | a `tick` per step, pitch rising slightly |
| Status nodes along a timeline | `pluck` climbing an arpeggio, one per node |

Gains that balanced well: ticks 0.2 to 0.6, plucks 0.5, bells 0.25 to 0.45, whooshes 0.6 to 1.0, impacts 0.6 to 1.1.
Pan things with where they are on screen (left card, negative pan).

## Honesty about the result

The model cannot listen. Check levels (the engine prints RMS and peak per 2 s; peaks sit near 0.89, no clipping, the intro
and outro quieter than the middle) and say plainly that nobody has listened to it yet, so the owner does before sharing.
If the owner has a licensed track or a voice-over, drop the synthesised bed and keep only the cue sound effects,
or skip the score and mux their audio in `assemble.sh`.
