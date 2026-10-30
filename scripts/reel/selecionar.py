"""Seleciona as melhores tomadas. Entrada: d/keep.json (linha do tempo cortada) + lista de trechos [ini, fim] nessa linha do tempo.
Saida: d2/keep.json (trechos em tempo do mestre, na ordem escolhida) e d2/audio16.raw para transcrever."""
import json, math, sys, os, subprocess
S, S2, SRC = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(S2, exist_ok=True)
keep = json.load(open(S + "/keep.json"))
Q = lambda d: max(1, math.ceil(d * 30 - 1e-6)) / 30
starts, acc = [], 0.0
for s, e in keep: starts.append(acc); acc += Q(e - s)
pieces = json.load(open(sys.argv[4]))
new = []
for c0, c1 in pieces:
    for j, (s, e) in enumerate(keep):
        a, b = starts[j], starts[j] + (e - s)
        lo, hi = max(a, c0), min(b, c1)
        if hi - lo < 0.12: continue
        new.append([round(s + (lo - a), 3), round(s + (hi - a), 3)])
json.dump(new, open(S2 + "/keep.json", "w"))
print(len(new), "trechos, duracao", round(sum(Q(e - s) for s, e in new), 1))
fc = ";".join(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,aformat=sample_rates=16000:channel_layouts=mono,apad=whole_dur={Q(e - s):.4f}[a{i}]" for i, (s, e) in enumerate(new))
fc += ";" + "".join(f"[a{i}]" for i in range(len(new))) + f"concat=n={len(new)}:v=0:a=1[o]"
open(S2 + "/af.txt", "w").write(fc)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex_script", S2 + "/af.txt", "-map", "[o]", "-ar", "16000", "-ac", "1", "-f", "s16le", S2 + "/final.raw"], check=True)
