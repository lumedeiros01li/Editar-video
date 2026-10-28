"""Sound design sintetico: whooshes nos cortes e hits (sub + click) nas palavras-chave."""
import numpy as np, wave

SR = 44100


def _env_hit(n, tau):
    t = np.arange(n) / SR
    return np.exp(-t / tau)


def whoosh(dur=0.5, seed=0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = rng.standard_normal(n)
    a = np.linspace(0.015, 0.6, n) ** 1.3          # corte do filtro sobe: ruido abre
    y = np.zeros(n); p = 0.0
    for i in range(n):
        p += a[i] * (x[i] - p); y[i] = p
    lo = np.zeros(n); p = 0.0
    for i in range(n):
        p += 0.012 * (y[i] - p); lo[i] = p
    y = y - lo
    t = np.linspace(0, 1, n)
    env = np.where(t < 0.82, (t / 0.82) ** 2.2, np.exp(-(t - 0.82) * 30))
    y = y * env
    return y / (np.abs(y).max() + 1e-9)


def hit(size="m"):
    amp = {"s": 0.55, "m": 0.75, "l": 1.0}[size]
    tau = {"s": 0.10, "m": 0.16, "l": 0.24}[size]
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t / 0.045)                 # queda de pitch: thump de sub
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * _env_hit(n, tau)
    rng = np.random.default_rng(7)
    click = rng.standard_normal(n) * np.exp(-t / 0.006)
    p = 0.0; c2 = np.zeros(n)
    for i in range(n):
        p += 0.35 * (click[i] - p); c2[i] = p
    body = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.05) * 0.35
    y = np.tanh(2.2 * (sub + 0.5 * c2 + body)) * amp   # saturacao: textura bruta
    return y


def build(total, cuts, impacts, path, gain=0.2):
    n = int((total + 1.0) * SR)
    out = np.zeros(n)
    for k, c in enumerate(cuts):
        w = whoosh(0.5, seed=k)
        s = int(max(c - 0.4, 0) * SR)
        out[s:s + len(w)] += w[:n - s] * 0.55
    for t, size in impacts:
        h = hit(size)
        s = int(t * SR)
        out[s:s + len(h)] += h[:n - s]
    out = np.tanh(out * gain * 1.6)
    pcm = (out[: int(total * SR)] * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
