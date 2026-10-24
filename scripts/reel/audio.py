import json, sys, wave, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

W = sys.argv[1]
SR = 48000
C = json.load(open(W + "/cues.json"))
DUR = C["duration"] + 0.05
N = int(DUR * SR)
rng = np.random.default_rng(7)

def readwav(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a if w.getnchannels() == 1 else a.reshape(-1, w.getnchannels()).mean(1)

def writewav(p, a):
    a = np.clip(a, -1, 1)
    st = a if a.ndim == 2 else np.stack([a, a], 1)
    w = wave.open(p, "w"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes()); w.close()

# ---------------- voice ----------------
src = {v: readwav(f"{W}/{v}_enh.wav") for v in ("v1", "v2")}
voice = np.zeros(N, np.float32)
fade = int(0.008 * SR)
for s in C["segments"]:
    a = src[s["src"]][int(s["s"] * SR):int(s["e"] * SR)].copy()
    a[:fade] *= np.linspace(0, 1, fade); a[-fade:] *= np.linspace(1, 0, fade)
    i = int(s["t"] * SR); n = min(len(a), N - i); voice[i:i + n] += a[:n]

# ---------------- music ----------------
def midi(m): return 440 * 2 ** ((m - 69) / 12)
bpm = 82; beat = 60 / bpm; bar = 4 * beat
chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]   # Fmaj7 Em7 Dm7 Cmaj7
t = np.arange(N) / SR
pad = np.zeros(N); pl = np.zeros(N); bass = np.zeros(N); hat = np.zeros(N)
nb = int(DUR / bar) + 2
for b in range(nb):
    ch = chords[b % 4]; t0 = b * bar
    i0 = int(t0 * SR); i1 = min(N, int((t0 + bar + 1.2) * SR))
    if i0 >= N: break
    tt = t[i0:i1] - t0
    env = np.minimum(1, tt / 0.9) * np.where(tt < bar, 1, np.exp(-(tt - bar) / 0.4))
    for m in ch:
        for det in (-0.06, 0.06):
            f = midi(m + 12 + det)
            pad[i0:i1] += env * (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt + 1)) * 0.08
    fb = midi(ch[0] - 12)
    ib = min(N, i0 + int(bar * SR))
    tb = t[i0:ib] - t0
    bass[i0:ib] += np.sin(2 * np.pi * fb * tb) * np.exp(-tb / 1.4) * np.minimum(1, tb / 0.02) * 0.35
    # arpeggio (8th notes)
    arp = [ch[0] + 24, ch[2] + 12, ch[3] + 12, ch[1] + 24, ch[2] + 24, ch[3] + 12, ch[1] + 24, ch[2] + 12]
    for k, m in enumerate(arp):
        ts = t0 + k * beat / 2; j0 = int(ts * SR); j1 = min(N, j0 + int(0.9 * SR))
        if j0 >= N: break
        tp = t[j0:j1] - ts; f = midi(m)
        pl[j0:j1] += (np.sin(2 * np.pi * f * tp) + 0.3 * np.sin(6 * np.pi * f * tp)) * np.exp(-tp / 0.28) * np.minimum(1, tp / 0.004) * (0.16 if k % 2 == 0 else 0.11)
    for k in range(4):   # soft shaker on off-beats
        ts = t0 + k * beat + beat / 2; j0 = int(ts * SR); j1 = min(N, j0 + int(0.07 * SR))
        if j0 >= N: break
        hat[j0:j1] += rng.standard_normal(j1 - j0) * np.exp(-np.arange(j1 - j0) / SR / 0.018) * 0.05
pad = sosfilt(butter(2, 2200, "low", fs=SR, output="sos"), pad)
pl = sosfilt(butter(2, 3500, "low", fs=SR, output="sos"), pl)
hat = sosfilt(butter(2, 7000, "high", fs=SR, output="sos"), hat)
# simple reverb: exponentially decaying noise IR (stereo)
def reverb(x, dec=1.8, mix=0.35, seed=1):
    r = np.random.default_rng(seed); L = int(dec * SR)
    ir = r.standard_normal(L) * np.exp(-np.arange(L) / SR / (dec / 6.9)); ir /= np.sqrt((ir ** 2).sum())
    ir = sosfilt(butter(1, 4000, "low", fs=SR, output="sos"), ir)
    return (1 - mix) * x + mix * fftconvolve(x, ir)[:len(x)]
musL = reverb(pad + pl * 0.9 + bass + hat, seed=1); musR = reverb(pad + pl * 1.1 + bass + hat * 0.8, seed=2)
mus = np.stack([musL, musR], 1)
# arrangement: fade in/out, dip during the dramatic part
g = np.ones(N)
def ramp(a, b, v0, v1):
    i0, i1 = int(a * SR), int(b * SR); g[i0:i1] = np.linspace(v0, v1, i1 - i0)
g[:int(0.6 * SR)] = np.linspace(0, 1, int(0.6 * SR))
ramp(18.75, 19.0, 1, 0.35); g[int(19.0 * SR):int(22.1 * SR)] = 0.35; ramp(22.1, 22.6, 0.35, 1)
g[int((DUR - 1.6) * SR):] = np.linspace(1, 0, N - int((DUR - 1.6) * SR))
mus *= g[:, None]
# sidechain ducking from voice envelope
env = np.sqrt(np.convolve(voice ** 2, np.ones(int(0.05 * SR)) / int(0.05 * SR), "same"))
duck = 1 - 0.45 * np.clip(env / 0.05, 0, 1)
k = int(0.15 * SR); duck = np.convolve(duck, np.ones(k) / k, "same")
mus *= duck[:, None]

# ---------------- sfx ----------------
def noise(n): return rng.standard_normal(n)
def env_ar(n, a, r):
    x = np.arange(n) / SR; return np.minimum(1, x / max(a, 1e-4)) * np.exp(-np.maximum(0, x - a) / r)
def sweep_noise(dur, f0, f1, fpk=None, q=1.5):
    n = int(dur * SR); x = noise(n); out = np.zeros(n); blk = 512
    fs_ = np.geomspace(f0, f1, n // blk + 1)
    zi = None
    for i, f in enumerate(fs_):
        a, b = i * blk, min(n, (i + 1) * blk)
        if a >= n: break
        sos = butter(2, [f / q, min(f * q, SR / 2 - 100)], "band", fs=SR, output="sos")
        out[a:b] = sosfilt(sos, x[a:b])
    return out
def sfx_pop(p):
    n = int(0.16 * SR); x = np.arange(n) / SR
    f = (520 + 700 * np.exp(-x / 0.025)) * p
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.045) * 0.5
def sfx_whoosh(p, up=False):
    d = 0.5; n = int(d * SR); x = np.arange(n) / SR
    s = sweep_noise(d, 400 * p, 2600 * p) if up else sweep_noise(d, 1800 * p, 350 * p)
    e = np.sin(np.pi * np.clip(x / d, 0, 1)) ** 2
    return s * e * 0.9
def sfx_swish(p):
    d = 0.2; n = int(d * SR); x = np.arange(n) / SR
    return sweep_noise(d, 3000 * p, 900 * p) * np.sin(np.pi * x / d) ** 2 * 0.6
def sfx_boom(p):
    n = int(1.6 * SR); x = np.arange(n) / SR
    f = 38 + 30 * np.exp(-x / 0.12)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.55)
    s += sosfilt(butter(2, 180, "low", fs=SR, output="sos"), noise(n)) * np.exp(-x / 0.3) * 0.6
    return s * 0.9
def sfx_tick(p):
    out = np.zeros(int(1.0 * SR))
    for k in range(5):
        i = int(k * 0.19 * SR); n = int(0.025 * SR)
        c = sosfilt(butter(2, 3000, "high", fs=SR, output="sos"), noise(n)) * np.exp(-np.arange(n) / SR / 0.004)
        out[i:i + n] += c * (0.5 if k % 2 else 0.35)
    return out
def sfx_ding(p):
    n = int(1.6 * SR); x = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * x) * np.exp(-x / d) for f, a, d in [(1318.5, 0.5, 0.9), (1975.5, 0.3, 0.6), (2637, 0.18, 0.35), (3951, 0.08, 0.2)])
    return s * np.minimum(1, x / 0.003) * 0.6
def sfx_lock(p):
    out = np.zeros(int(0.2 * SR))
    for i0, g_ in [(0, 0.6), (int(0.07 * SR), 0.9)]:
        n = int(0.03 * SR); c = sosfilt(butter(2, [1800, 6000], "band", fs=SR, output="sos"), noise(n)) * np.exp(-np.arange(n) / SR / 0.006)
        out[i0:i0 + n] += c * g_
    return out
def sfx_notify(p):
    out = np.zeros(int(0.9 * SR))
    for k, f in enumerate([987.8, 1318.5]):
        i0 = int(k * 0.11 * SR); n = len(out) - i0; x = np.arange(n) / SR
        out[i0:] += (np.sin(2 * np.pi * f * x) + 0.2 * np.sin(4 * np.pi * f * x)) * np.exp(-x / 0.22) * np.minimum(1, x / 0.003) * 0.45
    return out
GEN = {"pop": (sfx_pop, 0.0, 0.32), "whoosh": (sfx_whoosh, -0.3, 0.28), "whooshup": (lambda p: sfx_whoosh(p, True), -0.15, 0.25),
       "swish": (sfx_swish, -0.08, 0.18), "boom": (sfx_boom, -0.05, 0.42), "tick": (sfx_tick, 0.0, 0.3), "ding": (sfx_ding, 0.0, 0.2),
       "lock": (sfx_lock, 0.0, 0.35), "notify": (sfx_notify, 0.0, 0.22)}
fx = np.zeros((N, 2))
for k, s in enumerate(C["sfx"]):
    fn, off, lvl = GEN[s["kind"]]
    x = fn(s["pitch"]); x = x / (np.abs(x).max() + 1e-9) * lvl * s.get("gain", 1.0)
    i = int((s["t"] + off) * SR)
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), N - i)
    pan = 0.5 + 0.25 * np.sin(k * 1.7)   # gentle stereo spread
    fx[i:i + n, 0] += x[:n] * (1 - pan) * 1.4; fx[i:i + n, 1] += x[:n] * pan * 1.4
fx = reverb(fx[:, 0], 1.0, 0.18, 3)[:, None] * [1, 0] + reverb(fx[:, 1], 1.0, 0.18, 4)[:, None] * [0, 1]

np.save(W + "/stems.npy", np.stack([np.stack([voice, voice], 1), mus, fx]).astype(np.float32))
for name, x in [("voice", np.stack([voice, voice], 1)), ("music", mus), ("sfx", fx)]:
    writewav(f"{W}/stem_{name}.wav", x / max(1, np.abs(x).max()))
print("ok", N / SR)
