"""Monta keep.json (tempo do mestre) a partir de trechos escolhidos por palavra (indices do asr_raw.json) ou por tempo.
Mantem o fim das palavras (cauda +0,30s) e remove silencios com a atividade de voz dilatada."""
import json, math, sys, os, subprocess
OUT, PICKS = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
asr = json.load(open("asr_raw.json")); W = [w for s in asr for w in s["w"]]
k0 = json.load(open("keep_energy.json"))
dil = []
for s, e in k0:
    s, e = s - 0.10, e + 0.30
    if dil and s <= dil[-1][1]: dil[-1][1] = max(dil[-1][1], e)
    else: dil.append([s, e])
picks = json.load(open(PICKS)); rngs = []
for p in picks:
    if len(p) == 2 and isinstance(p[0], int) and isinstance(p[1], int) and p[1] > 20 and p[0] > 5 or (len(p) == 2 and all(isinstance(x, int) for x in p)):
        a, b = p
        s = W[a][1] - 0.10; e = W[b][2] + 0.30
        if b + 1 < len(W): e = min(e, W[b + 1][1] - 0.03)
        rngs.append([max(0, s), e])
    else: rngs.append([float(p[0]), float(p[1])])
Q = lambda d: max(1, math.ceil(d * 30 - 1e-6)) / 30
new = []
for s, e in rngs:
    for a, b in dil:
        lo, hi = max(a, s), min(b, e)
        if hi - lo >= 0.12: new.append([round(lo, 3), round(hi, 3)])
json.dump(new, open(OUT + "/keep.json", "w"))
print(len(new), "trechos, duracao", round(sum(Q(e - s) for s, e in new), 1))
fc = ";".join(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,aformat=sample_rates=16000:channel_layouts=mono,apad=whole_dur={Q(e - s):.4f}[a{i}]" for i, (s, e) in enumerate(new))
fc += ";" + "".join(f"[a{i}]" for i in range(len(new))) + f"concat=n={len(new)}:v=0:a=1[o]"
open(OUT + "/af.txt", "w").write(fc)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "master.mp4", "-filter_complex_script", OUT + "/af.txt", "-map", "[o]", "-ar", "16000", "-ac", "1", "-f", "s16le", OUT + "/final.raw"], check=True)
