"""Score for the template film. Copy to <work>/score.py, then retime every cue to your film's events.

Every visual event gets a sound at the same time as it happens in seek(t): read the times straight
out of film.html (the A(t, start, end) calls) so picture and sound share one clock.
Run:  python3 score.py   -> score.wav
"""
import os
import sys

SKILL = os.environ.get("SKILL_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from score_engine import (Score, bell, chord_tail, impact, pluck, riser,  # noqa: E402
                          tick, whoosh)

DUR = 10.0
s = Score(dur=DUR, bpm=120)          # 120 BPM: a beat every 0.5 s, so cuts on half-seconds land on the beat

# --- music bed: intro riser, drop at 2.0 s, band out before the end card chord
s.place(riser(2.0), 0.0, 0.55, rev=0.3)
s.drums(start=2.0, end=6.5, shaker=(3.0, 6.4))
s.harmony(start=2.0, end=6.5,
          roots=[45, 41, 48, 43],                                   # A F C G
          chords=[[57, 60, 64], [53, 57, 60], [55, 60, 64], [55, 59, 62]],
          arp=(3.0, 6.5))

# --- scene A: the mark builds itself
s.place(tick(2400, 0.05, 0.6), 0.08)                 # dot pops
s.place(whoosh(0.35, 400, 5000), 0.28, 0.6, pan=-0.3)  # line stretches
for i, (tm, m) in enumerate([(0.9, 81), (1.04, 84)]):  # glyph strokes draw
    s.place(pluck(m, 0.4, 1.5), tm, 0.5, pan=-0.3 + i * 0.6, rev=0.4)
s.place(impact(1.2) * 0.6, 1.45, 0.9, rev=0.3)        # burst
s.place(whoosh(0.5, 200, 3000, rise=False), 1.45, 0.5)

# --- wipe A -> B
s.place(whoosh(0.6, 250, 8000), 2.72, 1.0, pan=0.4, rev=0.2)

# --- scene B: rows complete (rising notes), status changes, zoom-through
for i, tm in enumerate([4.2, 4.6, 5.0]):
    s.place(pluck(76 + [0, 4, 7][i], 0.5, 2.0), tm, 0.55, pan=0.3, rev=0.4)
    s.place(tick(4200, 0.02, 0.25), tm)
s.place(bell(88, 1.2), 5.4, 0.4, rev=0.5)
s.place(whoosh(0.5, 6000, 300, rise=False), 6.45, 0.9, rev=0.2)

# --- scene C: end card lands on a chord with a long tail
s.place(chord_tail([45, 57, 64, 69, 72, 76]), 6.8, 1.0, rev=0.8)
s.place(impact(2.0) * 0.8, 6.8, 0.9, rev=0.3)
for i, m in enumerate([81, 84, 88, 93]):
    s.place(bell(m, 1.6), 7.35 + i * 0.08, 0.25, pan=-0.45 + i * 0.3, rev=0.7)
s.place(tick(2200, 0.04, 0.4), 7.9)                   # url appears

s.render(os.path.join(os.path.dirname(os.path.abspath(__file__)), "score.wav"))
