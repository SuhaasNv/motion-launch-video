"""Tiny synthesiser for launch-film scores: no samples, no network, deterministic.

Import it from a film's score.py:

    import sys; sys.path.insert(0, "<skill>/scripts")
    from score_engine import *
    s = Score(dur=20.0, bpm=120)
    s.drums(start=2.0, end=17.5, skip=[(15.7, 16.95)])
    s.harmony(start=2.0, end=18.0, roots=[45, 41, 48, 43], chords=[[57,60,64],[53,57,60],[55,60,64],[55,59,62]])
    s.place(bell(88), 5.95, 0.4, rev=0.5)   # a visual event
    s.render("score.wav")

Times are seconds on the film's clock. MIDI note numbers for pitch (60 = middle C, 69 = A4).
"""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
_rng = np.random.default_rng(7)


def seed(n):
    global _rng
    _rng = np.random.default_rng(n)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(d):
    return np.arange(int(d * SR)) / SR


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype='low', fs=SR, output='sos'), x)


def noise(n):
    return _rng.standard_normal(n)


# ---------------------------------------------------------------- instruments
def kick(big=1.0):
    t = tt(0.55)
    f = 44 + 130 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (6.5 / big))
    click = hp(noise(len(t)), 2500) * np.exp(-t * 300) * 0.25
    return np.tanh((body + click) * 1.6) * 0.9


def snare():
    t = tt(0.35)
    n = bp(noise(len(t)), 900, 7000) * np.exp(-t * 16)
    return (n * 0.8 + np.sin(2 * np.pi * 185 * t) * np.exp(-t * 28) * 0.5) * 0.7


def clap():
    t = tt(0.4)
    n = bp(noise(len(t)), 1000, 5000)
    e = np.zeros(len(t))
    for k, d in enumerate([0, 0.011, 0.022]):
        i = int(d * SR)
        e[i:] += np.exp(-(t[: len(t) - i]) * (90 if k < 2 else 14)) * (0.6 if k < 2 else 1)
    return n * e * 0.5


def hat(open_=False):
    t = tt(0.25 if open_ else 0.06)
    return hp(noise(len(t)), 7000, 4) * np.exp(-t * (14 if open_ else 70)) * 0.35


def _saw(f, t, cutoff, detune=0.0):
    out = np.zeros(len(t))
    k = 1
    while k * f < cutoff and k < 60:
        out += np.sin(2 * np.pi * k * f * (1 + detune) * t + k * 0.7) / k
        k += 1
    return out


def bass(m, d=0.24):
    t = tt(d)
    f = mtof(m)
    s = _saw(f, t, 900) * 0.55 + np.sin(2 * np.pi * f * t) * 0.8
    return lp(s * np.minimum(1, t / 0.005) * np.exp(-t * 5.5), 700) * 0.55


def pad(ms, d):
    t = tt(d)
    out = np.zeros(len(t))
    for m in ms:
        for dt in (-0.004, 0.0, 0.005):
            out += _saw(mtof(m), t, 2400, dt)
    env = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.4)
    return lp(out * env, 1800) * 0.05


def pluck(m, d=0.45, bright=1.0):
    t = tt(d)
    f = mtof(m)
    out = np.zeros(len(t))
    for k in range(1, 14):
        if k * f > 12000:
            break
        out += np.sin(2 * np.pi * k * f * t) / k * np.exp(-t * (7 + k * 3.5 / bright))
    return out * np.minimum(1, t / 0.002) * 0.35


def bell(m, d=1.4):
    t = tt(d)
    f = mtof(m)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 3.2)
         + 0.45 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 5)
         + 0.25 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 9)
         + 0.12 * np.sin(2 * np.pi * f * 5.43 * t) * np.exp(-t * 14))
    return s * np.minimum(1, t / 0.001) * 0.35


def tick(f=3200, d=0.03, g=0.4):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 180) * g


def whoosh(d=0.55, lo=300, hi=6000, rise=True):
    n = int(d * SR)
    out = np.zeros(n)
    src = noise(n + SR)
    grains = 24
    g = max(1, n // grains)
    for k in range(grains):
        x = k / (grains - 1)
        c = lo * (hi / lo) ** (x if rise else 1 - x)
        seg = bp(src[k * g: k * g + 3 * g], max(40, c * 0.6), min(20000, c * 1.6))
        a, b = k * g, min(n, k * g + len(seg))
        out[a:b] += (seg * np.hanning(len(seg)))[: b - a]
    return out * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5 * 0.5


def riser(d):
    t = tt(d)
    n = noise(len(t))
    out = np.zeros(len(t))
    seg = int(0.05 * SR)
    for i in range(0, len(t), seg):
        c = 300 * (9000 / 300) ** (i / len(t))
        chunk = out[i:i + seg]
        chunk[:] = bp(n[max(0, i - seg): i + seg], c * 0.7, min(20000, c * 1.4))[-len(chunk):]
    f = 80 * (2 ** np.linspace(0, 3, len(t)))
    sweep = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    return (out * 0.6 + sweep) * (t / d) ** 2.2 * 0.5


def impact(d=2.2):
    t = tt(d)
    f = 34 + 70 * np.exp(-t * 14)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    n = lp(noise(len(t)), 2500) * np.exp(-t * 7) * 0.5
    return np.tanh((sub + n) * 1.8) * 0.8


def chord_tail(ms, d=2.4):
    t = tt(d)
    out = np.zeros(len(t))
    for m in ms:
        out += _saw(mtof(m), t, 3000, 0.002) * np.exp(-t * 1.6) * 0.06
    return lp(out, 3000)


# ---------------------------------------------------------------- the mix
def _in(t, spans):
    return any(a <= t < b for a, b in spans)


class Score:
    def __init__(self, dur, bpm=120):
        self.dur, self.bpm, self.beat = dur, bpm, 60.0 / bpm
        self.N = int(SR * dur)
        self.L, self.R = np.zeros(self.N), np.zeros(self.N)
        self.send = np.zeros(self.N)
        self.kicks = np.zeros(self.N)
        self.duck = np.ones(self.N)

    def place(self, sig, t, gain=1.0, pan=0.0, rev=0.0):
        """Drop a sound at film time t. pan -1..1, rev = reverb send."""
        i = int(t * SR)
        if i >= self.N or i < 0:
            return
        s = sig[: self.N - i] * gain
        gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.L[i:i + len(s)] += s * gl * 1.414
        self.R[i:i + len(s)] += s * gr * 1.414
        self.send[i:i + len(s)] += s * rev

    def kick_at(self, t, big=1.0, gain=1.0):
        """Kick on its own bus, and duck everything else under it (sidechain)."""
        i = int(t * SR)
        if i >= self.N:
            return
        k = kick(big)[: self.N - i] * gain
        self.kicks[i:i + len(k)] += k
        env = 1 - 0.65 * np.exp(-np.linspace(0, 1, int(0.3 * SR)) * 9)
        seg = self.duck[i:i + len(env)]
        seg[:] = np.minimum(seg, env[: len(seg)])

    def drums(self, start, end, skip=(), claps_from=None, hats_from=None, shaker=None):
        """Four-on-the-floor from start to end; claps on 2 and 4, off-beat hats, optional 16th shaker span."""
        b = self.beat
        claps_from = start + 4 * b if claps_from is None else claps_from
        hats_from = start + 4 * b if hats_from is None else hats_from
        n = 0
        t = start
        while t < end - 1e-9:
            if not _in(t, skip):
                self.kick_at(t, 1.3 if n == 0 else 1.0)
                if t >= claps_from and n % 2 == 1:
                    self.place(clap(), t, 0.9, rev=0.25)
                    self.place(snare(), t, 0.35)
            for h in (0.5,):
                th = t + h * b
                if th >= hats_from and th < end and not _in(th, skip):
                    self.place(hat(n % 4 == 3), th, 0.8, pan=0.35)
            n += 1
            t = start + n * b
        if shaker:
            a, z = shaker
            k = 0
            while a + k * b / 4 < z:
                tt_ = a + k * b / 4 + b / 8
                if not _in(tt_, skip):
                    self.place(hat() * 0.5, tt_, 0.25, pan=0.6)
                k += 1

    def harmony(self, start, end, roots, chords, bar_beats=4, arp=None, skip=()):
        """Bass eighths on each root, a pad chord per bar, optional 16th arpeggio span (a, b)."""
        bar = bar_beats * self.beat
        i = 0
        t = start
        while t < end - 1e-9:
            root, ch = roots[i % len(roots)] - 12, chords[i % len(chords)]
            for e in range(bar_beats * 2):
                tn = t + e * self.beat / 2
                if tn < end and not _in(tn, skip):
                    self.place(bass(root + (12 if e % 4 == 3 else 0)), tn, 0.9)
            self.place(pad(ch, min(bar + 0.1, end - t + 0.4)), t, 1.0, rev=0.5)
            if arp and arp[0] <= t < arp[1]:
                notes = ch + [ch[0] + 12]
                pat = [0, 1, 2, 1, 2, 3, 2, 1]
                for s in range(bar_beats * 4):
                    tn = t + s * self.beat / 4
                    if tn < arp[1] and not _in(tn, skip):
                        self.place(pluck(notes[pat[s % 8]] + 12, 0.3, 0.8), tn, 0.22, pan=(-0.5 if s % 2 else 0.5), rev=0.35)
            i += 1
            t = start + i * bar

    def render(self, path="score.wav", fade=0.4, headroom=0.89):
        L = self.L * self.duck ** 0.6
        R = self.R * self.duck ** 0.6
        ir_t = tt(2.2)
        ir = lp(noise(len(ir_t)) * np.exp(-ir_t * 3.0), 6000)
        ir /= np.sqrt(np.sum(ir ** 2))
        L = L + fftconvolve(self.send, ir)[: self.N] * 0.35 + self.kicks
        R = R + fftconvolve(self.send, np.roll(ir, 331))[: self.N] * 0.35 + self.kicks
        mix = hp(np.stack([L, R]), 28)
        peak = np.max(np.abs(mix)) or 1.0
        mix = np.tanh(mix / (peak * 0.8) * 1.1)
        mix /= np.max(np.abs(mix)) / headroom
        fn = int(fade * SR)
        if fn:
            mix[:, -fn:] *= np.linspace(1, 0, fn) ** 2
        wavfile.write(path, SR, (mix.T * 32767).astype(np.int16))
        seg = int(SR * 2)
        report = []
        for a in range(0, self.N, seg):
            x = mix[:, a:a + seg]
            report.append(f"{a / SR:5.1f}s rms {np.sqrt((x ** 2).mean()):.3f} peak {np.abs(x).max():.3f}")
        print(f"wrote {path} ({self.dur}s, {SR} Hz stereo)\n" + "\n".join(report))
