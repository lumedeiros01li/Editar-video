"""Escolhe os takes: transcreve cada trecho do keep.json e mantem so os que voce indicar.
uso:
  python3 takes.py listar <video> <dir>            # imprime '#k inicio-fim nivel texto' de cada trecho (leva ~1s por trecho)
  python3 takes.py manter <dir> 15,19,29,50-55     # grava keep.json so com esses trechos (o original fica em keep_todos.json)
Rode 'listar' depois de cortes.py e antes de build.py transcrever."""
import json, os, subprocess, sys
modo = sys.argv[1]
if modo == "listar":
    import numpy as np
    from faster_whisper import WhisperModel
    video, S = sys.argv[2:4]
    todos = S + "/keep_todos.json"
    if not os.path.exists(todos): json.dump(json.load(open(S + "/keep.json")), open(todos, "w"))
    keep = json.load(open(todos))
    a = np.fromfile(S + "/a.raw", dtype=np.int16).astype(np.float32) / 32768
    m = WhisperModel("medium", compute_type="int8")
    for k, (s, e) in enumerate(keep):
        i0 = max(0, s - 0.15)
        x = np.concatenate([np.zeros(8000, np.float32), a[int(i0 * 16000):int((e + 0.15) * 16000)], np.zeros(8000, np.float32)])
        segs, _ = m.transcribe(x, language="pt", condition_on_previous_text=False)
        nivel = 20 * np.log10(np.sqrt((a[int(s * 16000):int(e * 16000)] ** 2).mean()) + 1e-9)
        print(f"#{k} {s:.2f}-{e:.2f} ({e - s:.1f}s) {nivel:.0f}dB  " + " ".join(g.text.strip() for g in segs), flush=True)
else:
    S, lista = sys.argv[2:4]
    keep = json.load(open(S + "/keep_todos.json"))
    idx = []
    for p in lista.split(","):
        a, _, b = p.partition("-"); idx += range(int(a), int(b or a) + 1)
    json.dump([keep[i] for i in sorted(set(idx))], open(S + "/keep.json", "w"))
    print(len(set(idx)), "trechos,", round(sum(keep[i][1] - keep[i][0] for i in set(idx)), 1), "s")
