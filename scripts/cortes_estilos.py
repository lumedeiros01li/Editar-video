"""Analisa o audio, remove pausas/respiracoes (>0,1s) e salva keep.json.palavras.json.
uso: python3 cortes_estilos.py <a.wav 16k mono> <saida_dir>"""
import numpy as np, json, sys
wav, S = sys.argv[1], sys.argv[2]
sr, hop, win, dt = 16000, 160, 480, 0.01
a = np.fromfile(wav, dtype=np.int16, offset=44).astype(np.float32) / 32768
n = (len(a) - win) // hop
fr = np.lib.stride_tricks.sliding_window_view(a, win)[::hop][:n]
db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
fr0 = fr - fr.mean(1, keepdims=True)
ac = np.fft.irfft(np.abs(np.fft.rfft(fr0, n=1024)) ** 2)[:, :win]
ac = ac / (ac[:, :1] + 1e-9)
voi = ac[:, int(sr / 400):int(sr / 75)].max(1)
P = np.abs(np.fft.rfft(fr * np.hanning(win), n=512)) ** 2
f = np.fft.rfftfreq(512, 1 / sr)
cen = (P * f).sum(1) / (P.sum(1) + 1e-12)
t = np.arange(n) * hop / sr + win / 2 / sr
floor = np.percentile(db, 5); thr = max(floor + 14, -54)
print("piso de ruido", round(floor, 1), "dB, limiar", round(thr, 1))
active = db > thr
runs = []; i = 0
while i < n:
    if active[i]:
        j = i
        while j < n and active[j]: j += 1
        runs.append([i, j]); i = j
    else: i += 1
# histerese: estende cada trecho enquanto o som ainda decai (fim de palavra), ate 0,15s
low = db > thr - 4
for r in runs:
    k = 0
    while r[1] < n and low[r[1]] and k < 15: r[1] += 1; k += 1
    k = 0
    while r[0] > 0 and low[r[0] - 1] and k < 6: r[0] -= 1; k += 1
m = []
for r in runs:
    if m and (r[0] - m[-1][1]) * dt <= 0.10: m[-1][1] = r[1]
    else: m.append(list(r))
voiced = (voi > 0.5) & (db > thr + 2)
breathy = (voi < 0.5) & (db < thr + 14) & (cen < 3000)
seg = []
for a0, b0 in m:
    if voiced[a0:b0].sum() < 3: continue
    h = a0
    while h < b0 and breathy[h]: h += 1
    if (h - a0) * dt > 0.10: a0 = h - 4
    e = b0
    while e > a0 and breathy[e - 1]: e -= 1
    if (b0 - e) * dt > 0.10: b0 = e + 4
    seg.append([t[a0], t[b0 - 1]])
out = []
for k, (s, e) in enumerate(seg):
    ps = 0.05 if k == 0 else min(0.05, (s - seg[k - 1][1]) / 2)
    pe = 0.08 if k == len(seg) - 1 else min(0.08, (seg[k + 1][0] - e) / 2)
    out.append([round(max(0, s - ps), 3), round(e + pe, 3)])
json.dump(out, open(S + "/keep.json", "w"))
print("segmentos", len(out), "duracao final", round(sum(e - s for s, e in out), 2), "de", round(t[-1], 2))
