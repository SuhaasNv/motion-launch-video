"""Synthesised score for the PermitFlow showreel: 120 BPM, A minor, every hit on a visual event."""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
L = np.zeros(N)
R = np.zeros(N)
send = np.zeros(N)  # reverb bus (mono)
duck = np.ones(N)   # sidechain from kicks
KB = np.zeros(N)    # kick bus (not ducked)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(sig, t, gain=1.0, pan=0.0, rev=0.0):
    i = int(t * SR)
    if i >= N:
        return
    s = sig[: N - i] * gain
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(s)] += s * gl * 1.414
    R[i:i + len(s)] += s * gr * 1.414
    send[i:i + len(s)] += s * rev


def tt(d):
    return np.arange(int(d * SR)) / SR


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype='low', fs=SR, output='sos'), x)


# ---------- instruments ----------
def kick(big=1.0):
    t = tt(0.55)
    f = 44 + 130 * np.exp(-t * 32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * (6.5 / big))
    click = hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 300) * 0.25
    return np.tanh((body + click) * 1.6) * 0.9


def snare():
    t = tt(0.35)
    n = bp(rng.standard_normal(len(t)), 900, 7000) * np.exp(-t * 16)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 28) * 0.5
    return (n * 0.8 + tone) * 0.7


def clap():
    t = tt(0.4)
    n = bp(rng.standard_normal(len(t)), 1000, 5000)
    e = np.zeros(len(t))
    for k, d in enumerate([0, 0.011, 0.022]):
        i = int(d * SR)
        e[i:] += np.exp(-(t[: len(t) - i]) * (90 if k < 2 else 14)) * (0.6 if k < 2 else 1)
    return n * e * 0.5


def hat(open_=False):
    t = tt(0.25 if open_ else 0.06)
    n = hp(rng.standard_normal(len(t)), 7000, 4)
    return n * np.exp(-t * (14 if open_ else 70)) * 0.35


def saw_add(f, t, cutoff, detune=0.0):
    out = np.zeros(len(t))
    k = 1
    while k * f < cutoff and k < 60:
        out += np.sin(2 * np.pi * k * f * (1 + detune) * t + k * 0.7) / k
        k += 1
    return out


def bass_note(m, d):
    t = tt(d)
    f = mtof(m)
    s = saw_add(f, t, 900) * 0.55 + np.sin(2 * np.pi * f * t) * 0.8
    env = np.minimum(1, t / 0.005) * np.exp(-t * 5.5)
    return lp(s * env, 700) * 0.55


def pad_chord(ms, d):
    t = tt(d)
    out = np.zeros(len(t))
    for m in ms:
        for dt in (-0.004, 0.0, 0.005):
            out += saw_add(mtof(m), t, 2400, dt)
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
    """Noise swept through a moving band-pass (STFT-free: sum of short filtered grains)."""
    n = int(d * SR)
    out = np.zeros(n)
    noise = rng.standard_normal(n + SR)
    grains = 24
    g = n // grains
    for k in range(grains):
        x = k / (grains - 1)
        c = lo * (hi / lo) ** (x if rise else 1 - x)
        seg = bp(noise[k * g: k * g + 3 * g], max(40, c * 0.6), min(20000, c * 1.6))
        w = np.hanning(len(seg))
        a, b = k * g, min(n, k * g + len(seg))
        out[a:b] += (seg * w)[: b - a]
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    return out * env * 0.5


def riser(d):
    t = tt(d)
    n = rng.standard_normal(len(t))
    out = np.zeros(len(t))
    seg = int(0.05 * SR)
    for i in range(0, len(t), seg):
        x = i / len(t)
        c = 300 * (9000 / 300) ** x
        out[i:i + seg] = bp(n[max(0, i - seg): i + seg], c * 0.7, min(20000, c * 1.4))[-len(out[i:i + seg]):]
    f = 80 * (2 ** (np.linspace(0, 3, len(t))))
    sweep = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    env = (t / d) ** 2.2
    return (out * 0.6 + sweep) * env * 0.5


def impact(d=2.2):
    t = tt(d)
    f = 34 + 70 * np.exp(-t * 14)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    n = lp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 7) * 0.5
    return np.tanh((sub + n) * 1.8) * 0.8


# ---------- arrangement ----------
BEAT = 0.5
BARS = [(2.0 + 2 * i) for i in range(9)]  # 2..18
ROOTS = [45, 41, 36 + 12, 43]  # A2 F2 C3 G2 (bass octave below via -12)
CHORDS = [[57, 60, 64], [53, 57, 60], [55, 60, 64], [55, 59, 62]]  # Am F C G

# intro: riser + mark events
place(riser(2.0), 0.0, 0.55, rev=0.3)
place(tick(2400, 0.05, 0.6), 0.08, pan=0)                   # dot pop
place(whoosh(0.35, 400, 5000), 0.28, 0.6, pan=-0.3)          # line stretch
place(kick(0.6) * 0.5, 0.74)                                  # square lands
for i, (tm, m) in enumerate([(0.88, 81), (0.98, 84), (1.06, 88)]):
    place(pluck(m, 0.4, 1.5), tm, 0.5, pan=-0.4 + i * 0.4, rev=0.4)
place(bell(93, 1.6), 1.2, 0.35, rev=0.6)                     # check draws
place(impact(1.2) * 0.6, 1.45, 0.9, rev=0.3)                 # burst
place(whoosh(0.5, 200, 3000, rise=False), 1.45, 0.5)

# drums
kick_times = []
for b in range(4, 36):  # beats from t=2.0 to 17.5
    t0 = b * BEAT
    if 15.72 <= t0 < 16.95:
        continue  # breakdown before the stamp
    kick_times.append(t0)
    k = kick(1.3 if t0 == 2.0 else 1.0)
    i0 = int(t0 * SR)
    KB[i0:i0 + len(k)] += k[: N - i0]
for t0 in kick_times:
    i = int(t0 * SR)
    d = np.linspace(0, 1, int(0.3 * SR))
    env = 1 - 0.65 * np.exp(-d * 9)
    duck[i:i + len(env)] = np.minimum(duck[i:i + len(env)], env[: N - i])
for b in range(8, 36):
    t0 = b * BEAT
    if 15.72 <= t0 < 16.95:
        continue
    if b % 2 == 1:
        place(clap(), t0, 0.9, rev=0.25)
        place(snare(), t0, 0.35)
for k in range(8 * 2, 36 * 2):
    t0 = k * BEAT / 2
    if 15.72 <= t0 < 16.95:
        continue
    if k % 2 == 1:
        place(hat(k % 8 == 7), t0, 0.8, pan=0.35)
    elif t0 >= 6.5:
        place(hat(), t0, 0.35, pan=-0.35)
# 16th shaker in the busiest stretch
for k in range(int(6.5 * 8), int(15.6 * 8)):
    place(hat() * 0.5, k / 8 + 0.0625, 0.25, pan=0.6)

# bass + pads + arps
music = np.zeros(N)
for bi, t0 in enumerate(BARS):
    if t0 >= 18.0:
        break
    idx = bi % 4
    root = ROOTS[idx] - 12
    for e in range(4 * 2):  # eighths
        tn = t0 + e * BEAT / 2
        if 15.72 <= tn < 16.95:
            continue
        m = root + (12 if e % 4 == 3 else 0)
        place(bass_note(m, 0.24), tn, 0.9)
    place(pad_chord(CHORDS[idx], 2.1), t0, 1.0, rev=0.5)
    if 6.5 <= t0 < 16.0:
        pattern = [0, 1, 2, 1, 2, 3, 2, 1]
        notes = CHORDS[idx] + [CHORDS[idx][0] + 12]
        for s in range(16):
            tn = t0 + s * BEAT / 4
            if 15.72 <= tn < 16.95:
                continue
            place(pluck(notes[pattern[s % 8]] + 12, 0.3, 0.8), tn, 0.22, pan=(-0.5 if s % 2 else 0.5), rev=0.35)
# breakdown tension: sustained pad + riser into the stamp
place(pad_chord([57, 60, 64, 69], 1.4), 15.6, 1.2, rev=0.7)
place(riser(1.2), 15.75, 0.6, rev=0.2)

# ---------- sfx on the picture ----------
for tm in [3.48]:
    place(whoosh(0.6, 250, 8000), tm, 1.0, pan=0.4, rev=0.2)
place(impact(0.8) * 0.4, 3.95, 0.6)
# form rows complete (rising)
for i, tm in enumerate([4.55, 4.9, 5.25, 5.6]):
    place(pluck(76 + [0, 3, 7, 12][i], 0.5, 2.0), tm, 0.55, pan=0.3, rev=0.4)
    place(tick(4200, 0.02, 0.25), tm)
place(tick(1800, 0.04, 0.7), 5.93)                    # submit press
place(bell(88, 1.2), 5.95, 0.4, rev=0.5)
place(whoosh(0.5, 6000, 300, rise=False), 6.25, 0.9, rev=0.2)  # zoom-through
# tile entrances
for i in range(4):
    place(tick(2600 + i * 200, 0.025, 0.3), 6.62 + i * 0.07, pan=-0.6 + i * 0.4)
# scans + results
ST = [7.15, 7.5, 7.85, 8.2]
for i, a in enumerate(ST):
    place(whoosh(0.6, 1500, 5000) * 0.35, a, 0.6, pan=-0.6 + i * 0.4)
    if i < 3:
        place(bell(84 + [0, 4, 7][i], 1.0), a + 0.6, 0.45, pan=-0.6 + i * 0.4, rev=0.45)
# issue alert: low minor second pair
for k, m in enumerate([62, 63]):
    place(pluck(m, 0.6, 0.6) * 1.2, 8.8 + k * 0.09, 0.9, pan=0.6, rev=0.3)
place(kick(0.5) * 0.35, 8.8)
place(whoosh(0.7, 400, 4000), 9.35, 0.7, pan=0.3, rev=0.2)  # FLIP to fix
place(tick(1500, 0.05, 0.6), 10.75)                    # unlock
place(tick(900, 0.08, 0.4), 10.8)
for k in range(14):                                     # odometer
    place(tick(3000 + k * 60, 0.015, 0.18), 11.35 + k * 0.55 / 14, pan=-0.2)
place(bell(81, 1.0), 12.1, 0.35, rev=0.5)               # addressed
place(bell(88, 1.2), 12.55, 0.45, rev=0.5)              # resolved
place(bell(93, 1.4), 12.4, 0.25, pan=0.5, rev=0.5)      # doc verified
place(whoosh(0.55, 200, 9000), 12.72, 1.0, pan=-0.5, rev=0.2)  # whip pan
# status nodes
def rule_time(frac):
    lo, hi = 0.0, 1.0
    for _ in range(40):
        m = (lo + hi) / 2
        if -(np.cos(np.pi * m) - 1) / 2 < frac:
            lo = m
        else:
            hi = m
    return lo
for i, frac in enumerate([0, 0.25, 0.5, 0.75, 1.0]):
    tn = 13.35 + 2.0 * rule_time(frac)
    place(pluck([69, 72, 76, 79, 81][i] + 12, 0.5, 1.8), tn, 0.5, pan=-0.6 + i * 0.3, rev=0.5)
    place(tick(5000, 0.02, 0.2), tn)
place(bell(93, 2.0), 15.35, 0.35, rev=0.6)
place(whoosh(0.5, 300, 7000), 15.7, 0.8, rev=0.3)       # zoom into approved
# stamp
place(impact(2.6), 16.95, 1.1, rev=0.4)
place(snare() * 1.3, 16.95, 0.8, rev=0.5)
place(bell(81, 2.2), 16.97, 0.3, rev=0.7)
# sheen
place(whoosh(0.6, 3000, 12000) * 0.4, 17.15, 0.5, pan=0.5)
place(whoosh(0.5, 5000, 300, rise=False), 17.78, 0.7, rev=0.3)
# end card: final chord with long tail
end = np.zeros(int(2.4 * SR))
for m in [45, 57, 64, 69, 72, 76]:
    t = tt(2.4)
    end += saw_add(mtof(m), t, 3000, 0.002) * np.exp(-t * 1.6) * 0.06
place(lp(end, 3000), 18.0, 1.0, rev=0.8)
place(impact(2.0) * 0.8, 18.0, 0.9, rev=0.3)
for i, m in enumerate([81, 84, 88, 93]):
    place(bell(m, 1.6), 18.45 + i * 0.07, 0.25, pan=-0.45 + i * 0.3, rev=0.7)
place(tick(2200, 0.04, 0.4), 18.95)

# ---------- mix ----------
# apply sidechain to everything except kicks: approximate by ducking the whole bus lightly, kicks re-added
Lm, Rm = L * duck ** 0.6, R * duck ** 0.6
ir_t = tt(2.2)
ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 3.0)
ir = lp(ir, 6000)
ir /= np.sqrt(np.sum(ir ** 2))
wet = fftconvolve(send, ir)[:N] * 0.35
wetR = fftconvolve(send, np.roll(ir, 331))[:N] * 0.35
Lm += wet + KB
Rm += wetR + KB
mix = np.stack([Lm, Rm], 1)
mix = hp(mix.T, 28).T
mix = np.tanh(mix / (np.max(np.abs(mix)) * 0.8) * 1.1)
mix /= np.max(np.abs(mix)) / 0.89
fade = np.ones(N)
fn = int(0.4 * SR)
fade[-fn:] = np.linspace(1, 0, fn) ** 2
mix *= fade[:, None]
wavfile.write('score.wav', SR, (mix * 32767).astype(np.int16))
print('ok', mix.shape)
