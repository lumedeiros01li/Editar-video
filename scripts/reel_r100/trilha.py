# Trilha cinematográfica sincronizada com o reel (120 BPM, batida = 0,5s)
import numpy as np, wave
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000; DUR = 32.5; N = int(SR * DUR)
rng = np.random.default_rng(11)
BUS = {k: np.zeros((N, 2)) for k in ['drums', 'music', 'fx', 'ui']}

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x, axis=0)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x, axis=0)
def bp(x, f1, f2, o=2): return sosfilt(butter(o, [f1, f2], 'band', fs=SR, output='sos'), x, axis=0)

def add(bus, sig, t, gain=1.0, pan=0.0):
    if sig.ndim == 1:
        sig = np.stack([sig * (1 - max(pan, 0)), sig * (1 + min(pan, 0))], 1)
    i = int(round(t * SR)); n = min(len(sig), N - i)
    if n > 0 and i >= 0: BUS[bus][i:i + n] += sig[:n] * gain

def adsr(n, a, d, s, r):
    t = np.arange(n) / SR; total = n / SR
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = np.clip((total - t) / max(r, 1e-4), 0, 1)
    return e * rel

def decay(n, d, a=0.002):
    t = np.arange(n) / SR; e = np.exp(-t / d); k = max(1, int(a * SR)); e[:k] *= np.linspace(0, 1, k); return e

# ---------- instrumentos ----------
def piano(m, dur=1.2, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    s = np.zeros(n)
    for k, a in enumerate([1, 0.5, 0.28, 0.16, 0.09, 0.05]):
        fk = f * (k + 1) * (1 + 0.0004 * k * k)
        s += a * np.sin(2 * np.pi * fk * t) * np.exp(-t * (1.8 + k * 1.4))
    s += 0.15 * rng.standard_normal(n) * np.exp(-t * 200)  # martelo
    return lp(s * decay(n, 0.9, 0.003), 5000) * vel

def supersaw(m, dur, a=0.4, r=0.6, cutoff=2200, voices=5, det=0.12):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros((n, 2))
    for v in range(voices):
        d = (v - (voices - 1) / 2) * det / (voices - 1) * 2
        f = mtof(m + d); ph = rng.random()
        x = 2 * ((t * f + ph) % 1) - 1
        pan = (v / (voices - 1)) * 2 - 1
        out[:, 0] += x * (1 - max(pan, 0) * 0.7); out[:, 1] += x * (1 + min(pan, 0) * 0.7)
    out = lp(out / voices, cutoff, 2)
    return out * adsr(n, a, 1.0, 1.0, r)[:, None]

def strings_lead(m, dur, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.4, 0, 1)
    ph = 2 * np.pi * np.cumsum(mtof(m) * vib) / SR
    x = sum(np.sin(ph * k) / k for k in range(1, 9))
    x2 = sum(np.sin(ph * k * 1.003) / k for k in range(1, 9))
    s = np.stack([x, x2], 1)
    s = lp(s, 3200, 2)
    return s * adsr(n, 0.09, 0.5, 0.85, 0.25)[:, None] * 0.35 * vel

def sub(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    return np.tanh(1.5 * x) * adsr(n, 0.01, 0.3, 0.8, 0.08)

def kick(g=1.0):
    n = int(0.5 * SR); t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t * 28); ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.tanh(2.2 * np.sin(ph)) * decay(n, 0.16, 0.001)
    s += 0.25 * hp(rng.standard_normal(n), 3000) * np.exp(-t * 300)
    return s * g

def taiko(g=1.0, pitch=1.0):
    n = int(1.2 * SR); t = np.arange(n) / SR
    f = (70 + 60 * np.exp(-t * 22)) * pitch; ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * decay(n, 0.35, 0.002)
    skin = lp(rng.standard_normal(n), 900) * np.exp(-t * 25) * 1.2
    return np.tanh(1.6 * (body + skin)) * g

def snare(g=1.0):
    n = int(0.35 * SR); t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    nz = bp(rng.standard_normal(n), 1500, 9000) * np.exp(-t * 16)
    return (0.6 * tone + nz) * g

def hat(g=1.0, open_=False):
    n = int((0.3 if open_ else 0.06) * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t * (12 if open_ else 70)) * g

def crash(g=1.0, dur=2.5):
    n = int(dur * SR); t = np.arange(n) / SR
    x = hp(rng.standard_normal((n, 2)), 4000) * np.exp(-t * 1.6)[:, None]
    return x * g

def boom(g=1.0, dur=2.5):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 32 + 90 * np.exp(-t * 6); ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.tanh(2 * np.sin(ph)) * decay(n, 0.9, 0.001)
    s += lp(rng.standard_normal(n), 400) * np.exp(-t * 4) * 0.8
    return s * g

def braam(root_m, dur=2.0, g=1.0):
    n = int(dur * SR); out = np.zeros((n, 2))
    t = np.arange(n) / SR
    for m in [root_m - 12, root_m, root_m + 7, root_m + 12]:
        for v in range(5):
            f = mtof(m + (v - 2) * 0.08)
            x = 2 * ((t * f + rng.random()) % 1) - 1
            pan = v / 4 * 2 - 1
            out[:, 0] += x * (1 - max(pan, 0) * 0.6); out[:, 1] += x * (1 + min(pan, 0) * 0.6)
    cut = 300 + 2200 * np.exp(-t * 2.5)
    # filtro com cutoff variável: aproximado em blocos
    res = np.zeros_like(out); blk = 2400
    for i in range(0, n, blk):
        res[i:i + blk] = lp(out[i:i + blk], cut[i], 2)
    res = np.tanh(res / 6 * 2.5)
    return res * adsr(n, 0.01, 0.8, 0.6, 0.6)[:, None] * g

def whoosh(dur=0.5, rev=False):
    n = int(dur * SR); x = rng.standard_normal((n, 2)); t = np.linspace(0, 1, n)
    res = np.zeros_like(x); blk = 1200
    for i in range(0, n, blk):
        fc = 400 + 7000 * (t[i] if not rev else 1 - t[i])
        res[i:i + blk] = bp(x[i:i + blk], fc * 0.6, min(fc * 1.6, 20000), 1)
    e = np.sin(np.pi * t) ** 2
    return res * e[:, None] * 1.5

def riser(dur, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; p = t / dur
    f = 120 * 2 ** (p * 4); ph = 2 * np.pi * np.cumsum(f) / SR
    s = 0.25 * (2 * ((ph / (2 * np.pi)) % 1) - 1)
    nz = whoosh(dur)[:, 0] * 0.6
    x = lp(s, 4000) + nz
    return np.stack([x, np.roll(x, 200)], 1) * (p ** 2.2)[:, None] * g

def reverse_cymbal(dur=1.0, g=1.0):
    c = crash(1.0, dur)[::-1]; return c * g

def bell(m, g=1.0, dur=1.6):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    s = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3)
         + 0.25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 6))
    return s * decay(n, 0.6, 0.001) * g

def tick(g=1.0, m=96):
    n = int(0.05 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t * 90) * g

# ---------- harmonia ----------
CH = {  # baixo, voicing (cordas), notas do arpejo
    'Am': (45, [57, 60, 64, 69], [69, 72, 76, 81, 76, 72]),
    'F':  (41, [57, 60, 65, 69], [65, 69, 72, 77, 72, 69]),
    'C':  (48, [55, 60, 64, 67], [67, 72, 76, 79, 76, 72]),
    'G':  (43, [55, 59, 62, 67], [67, 71, 74, 79, 74, 71]),
    'E':  (40, [56, 59, 64, 68], [68, 71, 76, 80, 76, 71]),
    'Dm': (38, [57, 62, 65, 69], [62, 65, 69, 74, 69, 65]),
}
TL = [  # (início, fim, acorde)
    (0, 2, 'Am'), (2, 4, 'F'), (4, 6, 'C'), (6, 8, 'G'), (8, 10, 'Am'), (10, 11.5, 'F'),
    (11.5, 12.5, 'E'), (12.5, 13.5, 'Am'), (13.5, 14.5, 'F'), (14.5, 15.5, 'G'), (15.5, 16.5, 'E'),
    (16.5, 17.5, 'F'), (17.5, 18.5, 'E'),
    (18.5, 20, 'Am'), (20, 22, 'Am'), (22, 24, 'F'), (24, 26, 'C'), (26, 27, 'G'), (27, 28, 'E'),
    (28, 29, 'F'), (29, 30, 'G'), (30, 30.5, 'E'), (30.5, 32.5, 'Am'),
]
MEL = {
    'Am': [(0, 76, 2), (2, 72, 1), (3, 74, 1)], 'F': [(0, 77, 2), (2, 76, 1), (3, 72, 1)],
    'C': [(0, 76, 2), (2, 74, 1), (3, 72, 1)], 'G': [(0, 74, 3), (3, 71, 1)],
    'E': [(0, 71, 2), (2, 68, 2)],
}
B = 0.5
def in_any(t, ranges): return any(a <= t < b for a, b in ranges)

# ---------- arranjo ----------
GAPS = [(16.38, 16.5), (30.38, 30.5)]  # silêncio antes das batidas fortes
for (a, b, c) in TL:
    bass, voic, arp = CH[c]
    # cordas (pad)
    padg = 0.55
    if 11.5 <= a < 12.5 or 27 <= a < 28: padg = 0.75
    if 16.5 <= a < 18.5: padg = 0.9
    if a >= 30.5: padg = 1.0
    for m in voic:
        add('music', supersaw(m, b - a + 0.5, a=0.25, r=0.5, cutoff=1600 if a < 20 else 2300), a, 0.05 * padg)
    # sub-baixo nas batidas
    if in_any(a, [(2, 11.5), (12.5, 16.38), (20, 27), (28, 30.38)]):
        t = a
        while t < b - 1e-6:
            if not in_any(t, GAPS): add('music', sub(bass, B * 0.95), t, 0.42)
            t += B
    elif a >= 30.5 or 16.5 <= a < 18.5:
        add('music', sub(bass, b - a), a, 0.4)
    # arpejo de piano em colcheias (0,25s)
    if not (16.5 <= a < 18.5):
        t = a; i = 0
        while t < b - 1e-6:
            if not in_any(t, GAPS):
                vel = 0.55 + 0.25 * (i % 2 == 0)
                if a >= 20 and a < 27: vel *= 1.15
                add('music', piano(arp[i % len(arp)], 1.0, vel), t, 0.22, pan=0.25 * (1 if i % 2 else -1))
                if a >= 20 and a < 27 and i % 2 == 0:
                    add('music', piano(arp[i % len(arp)] + 12, 0.8, 0.4), t, 0.12, pan=0.4)
            t += 0.25; i += 1
    # melodia de cordas nos trechos de maior emoção
    if in_any(a, [(6, 11.5), (20, 27), (30.5, 32.5)]):
        lvl = 1.0 if a >= 20 else 0.75
        for (bo, m, ln) in MEL[c]:
            ts = a + bo * B; te = min(b, ts + ln * B)
            if ts < b - 1e-6:
                add('music', strings_lead(m, te - ts + 0.3), ts, lvl)
                if a >= 20: add('music', strings_lead(m - 12, te - ts + 0.3), ts, 0.5 * lvl)
        if a >= 30.5:
            add('music', strings_lead(81, 2.0), a, 0.8)

# bateria
def beats(t0, t1, step=B): return list(np.arange(t0, t1 - 1e-6, step))
for t in beats(2, 11.5):           # parte 1: kick nos tempos, caixa no 2 e 4
    add('drums', kick(0.9), t)
    k = int(round((t - 2) / B))
    if k % 2 == 1: add('drums', snare(0.55), t, pan=0.05)
    add('drums', hat(0.18), t + 0.25, pan=0.3)
    if t >= 6: add('drums', hat(0.12), t + 0.125, pan=0.3); add('drums', hat(0.12), t + 0.375, pan=0.3)
for t in [4, 6, 8, 10]: add('drums', taiko(0.8), t, pan=-0.2)
for t in [7.5, 7.625, 7.75, 7.875, 10.75, 10.875]: add('drums', taiko(0.45, 1.3), t, pan=0.3)  # viradas
for t in beats(20, 27):            # parte 2: mais cheia
    add('drums', kick(1.0), t)
    k = int(round((t - 20) / B))
    if k % 2 == 1: add('drums', snare(0.65), t)
    for o in (0.125, 0.25, 0.375): add('drums', hat(0.14 if o != 0.25 else 0.2), t + o, pan=0.3)
for t in [20, 22, 24, 26]: add('drums', taiko(0.9), t, pan=-0.2); add('drums', crash(0.18, 1.5), t)
for t in [21.75, 21.875, 25.5, 25.625, 25.75, 25.875]: add('drums', taiko(0.45, 1.3), t, pan=0.3)
# suspense: batida de coração
for t in [11.5, 11.75, 12.0, 12.25, 27.0, 27.25, 27.5, 27.75]:
    add('drums', kick(0.75 if (t * 4) % 2 == 0 else 0.45), t)
# revelações: taiko + sino subindo
for i, t in enumerate([12.5, 13.1, 13.7, 14.3, 14.9]):
    add('drums', taiko(0.8 + 0.08 * i), t); add('drums', kick(0.8), t)
    add('ui', bell(81 + [0, 2, 3, 5, 7][i]), t, 0.32 if i < 4 else 0.45)
for i, t in enumerate([28.0, 28.5, 29.0, 29.5, 30.0]):
    add('drums', taiko(0.8 + 0.08 * i), t); add('drums', kick(0.8), t)
    add('ui', bell(81 + [0, 2, 3, 5, 7][i]), t, 0.32 if i < 4 else 0.45)
# rufo de caixa acelerando antes das batidas fortes
def roll(t0, t1, g0=0.15, g1=0.6):
    t = t0
    while t < t1:
        p = (t - t0) / (t1 - t0); add('drums', snare(g0 + (g1 - g0) * p), t, pan=0.1)
        t += 0.125 if p < 0.5 else (0.0625 if p < 0.85 else 0.03125)
roll(15.5, 16.38); roll(18.0, 18.48, 0.2, 0.5); roll(29.6, 30.38, 0.15, 0.55)
add('drums', kick(0.6), 1.0); add('drums', kick(0.7), 1.5)

# FX
add('fx', boom(1.0), 0.0); add('fx', crash(0.35), 0.0); add('fx', riser(2.0, 0.5), 0.0)
add('fx', reverse_cymbal(1.0, 0.5), 1.0)
for tf in [5.0, 8.0, 11.022, 20.554, 24.4, 26.822]:
    add('fx', whoosh(0.4), tf - 0.35, 0.5); add('fx', boom(0.45, 1.2), tf); add('fx', crash(0.15, 1.2), tf)
add('fx', riser(1.5, 0.9), 14.88); add('fx', reverse_cymbal(1.2, 0.7), 15.18)
# VIRADA 16,5s
add('fx', boom(1.3, 3.0), 16.5); add('fx', crash(0.55, 3.0), 16.5); add('fx', braam(41, 2.0, 0.55), 16.5)
add('drums', taiko(1.0), 16.5); add('drums', taiko(0.9, 0.8), 17.5); add('fx', braam(40, 1.0, 0.45), 17.5)
add('fx', riser(1.0, 0.6), 17.5); add('fx', reverse_cymbal(0.5, 0.6), 18.0)
add('fx', boom(1.0, 2.0), 18.5); add('fx', crash(0.35, 2.0), 18.5); add('drums', taiko(0.9), 18.5)
add('drums', kick(0.6), 19.0); add('drums', kick(0.6), 19.5); add('fx', riser(1.0, 0.5), 19.0)
add('fx', riser(1.5, 0.8), 28.88); add('fx', reverse_cymbal(1.0, 0.6), 29.38)
add('fx', boom(1.3, 3.0), 30.5); add('fx', crash(0.5, 2.0), 30.5); add('fx', braam(45, 2.0, 0.45), 30.5)
add('drums', taiko(1.0), 30.5)
add('ui', tick(0.08, 88), 23.502)
# ticks de ano (bem baixos)
def ease(p, mode=None):
    p = min(max(p, 0), 1); sm = p * p * (3 - 2 * p); return 1 - (1 - p) ** 3 if mode == 'out' else 0.7 * p + 0.3 * sm
def seg(t, segs):
    x = segs[0][2]
    for s in segs:
        t0, t1, x0, x1 = s[:4]; mode = s[4] if len(s) > 4 else None
        if t < t0: return x
        x = x0 + (x1 - x0) * ease((t - t0) / (t1 - t0), mode)
        if t <= t1: return x
    return x
for segs, a, b in [([(2, 5, 0, 8), (6, 8, 8, 15), (9, 11.5, 15, 25.75)], 2, 11.6),
                   ([(20, 22, 0, 8), (22, 23.5, 8, 10), (23.5, 24.7, 10, 15, 'out'), (25, 27, 15, 25.75)], 20, 27.1)]:
    prev = 0
    for t in np.arange(a, b, 0.002):
        k = int(np.floor(seg(t, segs) + 1e-6))
        if k > prev: add('ui', tick(0.05, 96 + (k % 5)), t, pan=0.3); prev = k

# ---------- mix ----------
# sidechain: cordas e baixo "respiram" com o bumbo
kick_times = [t for t in beats(2, 11.5) + beats(20, 27)]
duck = np.ones(N)
for t in kick_times:
    i = int(t * SR); n = int(0.22 * SR); e = 1 - 0.45 * np.exp(-np.arange(n) / SR / 0.07)
    j = min(N, i + n); duck[i:j] = np.minimum(duck[i:j], e[:j - i])
music = BUS['music'] * duck[:, None]
# silêncio dramático antes das batidas
gate = np.ones(N)
for a, b in GAPS:
    i, j = int(a * SR), int(b * SR); gate[i:j] = 0.0
    k = int(0.02 * SR); gate[i - k:i] = np.linspace(1, 0, k)
music *= gate[:, None]; drums = BUS['drums'] * gate[:, None]

# reverb por convolução (sala grande)
irn = int(2.6 * SR); t = np.arange(irn) / SR
ir = rng.standard_normal((irn, 2)) * np.exp(-t / 0.75)[:, None]
ir = lp(ir, 6000); ir[:int(0.02 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
def verb(x, mix):
    w = np.stack([fftconvolve(x[:, c], ir[:, c])[:N] for c in range(2)], 1)
    return x + w * mix
music = verb(music, 0.55)
drums = verb(drums, 0.22)
fx = verb(BUS['fx'], 0.6)
ui = verb(BUS['ui'], 0.7)

# automação de volume por trecho (dB): contraste entre suspense e explosões
AUTO = [(0,-7),(1.9,-7),(2.0,-5),(5.9,-4),(6.0,-2),(11.45,-1),(11.5,-13),(12.45,-13),(12.5,-9),(15.5,-4),(16.38,-3),
        (16.5,0),(18.4,0),(18.5,-6),(19.9,-6),(20.0,0),(26.95,0),(27.0,-13),(27.95,-13),(28.0,-8),(30.4,-3),(30.5,0),(32.5,0)]
ta=np.array([a for a,_ in AUTO]); da=np.array([d for _,d in AUTO])
auto=10**(np.interp(np.arange(N)/SR, ta, da)/20)
auto=np.convolve(auto, np.ones(1200)/1200, mode='same')
music*=auto[:,None]; drums*=auto[:,None]
mix = music * 1.0 + drums * 0.9 + fx * 0.8 + ui * 0.65
import sys
if '--stats' in sys.argv:
    def r(x,a,b): seg=x[int(a*SR):int(b*SR)]; return 20*np.log10(np.sqrt((seg**2).mean())+1e-9)
    for nm,x in [('music',music),('drums',drums*0.9),('fx',fx*0.8),('ui',ui*0.9),('MIX',mix)]:
        print(f'{nm:6s}', ' '.join(f'{r(x,a,a+1.5):6.1f}' for a in np.arange(0,32.5,1.5)))
    hf=hp(mix,6000); print('HF>6k ', ' '.join(f'{r(hf,a,a+1.5):6.1f}' for a in np.arange(0,32.5,1.5)))
    sys.exit()
mix = hp(mix, 28)
ref = mix[int(20*SR):int(27*SR)]
mix *= 10**(-10.5/20) / np.sqrt((ref**2).mean())   # trecho mais cheio em -10,5 dBFS RMS
mix = np.tanh(mix / 0.9) * 0.9                       # limita picos de forma suave
fo = int(0.4 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
with wave.open('trilha.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print('ok', 20 * np.log10(np.sqrt((mix ** 2).mean())))
