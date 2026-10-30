"""Reel brutalista: cortes + rosto centralizado + zooms graduais nos impactos + legenda e elementos no topo + sfx.

uso: python3 reel.py <master.mp4> <dir> <config.json> <saida.mp4> [--range ini fim]   (ini/fim em segundos da linha do tempo final)
O <dir> precisa ter keep.json, face.json e palavras_final.json."""
import json, math, re, subprocess, sys, os, difflib, unicodedata, bisect
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elementos as ET

SRC, S, CFGP, OUT = sys.argv[1:5]
RNG = None
if "--range" in sys.argv:
    k = sys.argv.index("--range"); RNG = (float(sys.argv[k + 1]), float(sys.argv[k + 2]))
CFG = json.load(open(CFGP))
FPS, W, H = 30, 1080, 1920
keep = json.load(open(S + "/keep.json"))
Q = lambda d: max(1, math.ceil(d * 30 - 1e-6)) / 30
starts, acc = [], 0.0
for s, e in keep: starts.append(acc); acc += Q(e - s)
TOTAL = acc
NF = int(round(TOTAL * FPS))

# ---------------------------------------------------------------- palavras / roteiro (igual a skill)
norm = lambda t: re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", t.lower()).encode("ascii", "ignore").decode())
rec = json.load(open(S + "/palavras_final.json"))
roteiro = CFG.get("roteiro")
cores = {"roxo": "#9B6BFF", "lima": "#E4FF6B", **CFG.get("cores", {})}
corc = lambda c: ET.hexc(cores.get(c, c)) if c else None

def alinhar():
    if not roteiro: return [{"p": w["p"], "w": w["w"], "s": w["s"], "e": max(w["e"], w["s"] + 0.08)} for w in rec]
    sw = [(pi, w) for pi, t in enumerate(roteiro) for w in t.split()]
    sn = [norm(w) for _, w in sw]; vocab = sorted(set(sn)); rn = []
    for r in rec:
        n = norm(r["w"]); c = difflib.get_close_matches(n, vocab, n=1, cutoff=0.8); rn.append(c[0] if c else n)
    t = [None] * len(sw)
    for i, j, size in difflib.SequenceMatcher(None, sn, rn, autojunk=False).get_matching_blocks():
        for k in range(size):
            if size >= 2 or len(sn[i + k]) >= 5: t[i + k] = (rec[j + k]["s"], rec[j + k]["e"])
    out = [None] * len(sw); i = 0; prev_end = 0.0
    while i < len(sw):
        if t[i]: out[i] = t[i]; prev_end = t[i][1]; i += 1; continue
        j = i
        while j < len(sw) and not t[j]: j += 1
        nxt = t[j][0] if j < len(sw) else TOTAL
        wts = [len(sn[k]) + 2 for k in range(i, j)]; span = max(nxt - prev_end, 0.06 * (j - i)); a = prev_end
        for k, wt in zip(range(i, j), wts):
            d = span * wt / sum(wts); out[k] = (a, a + d); a += d
        prev_end = a; i = j
    res = []; last = 0.0
    for (pi, w), (s, e) in zip(sw, out):
        s = max(s, last); e = max(e, s + 0.08); res.append({"p": pi, "w": w, "s": float(s), "e": float(e)}); last = s
    return res
PAL = alinhar()
tstart = lambda p: min(x["s"] for x in PAL if x["p"] == p)

# ---------------------------------------------------------------- mapa saida -> mestre
seg_of = []      # por frame de saida: indice do corte
src_idx = []     # por frame de saida: frame do mestre
for i, (s, e) in enumerate(keep):
    n = int(round(Q(e - s) * FPS)); b = int(round(s * FPS))
    for j in range(n): seg_of.append(i); src_idx.append(b + j)
seg_of = np.array(seg_of[:NF]); src_idx = np.array(src_idx[:NF])
NF = len(src_idx)

# ---------------------------------------------------------------- rosto (suavizado no tempo do mestre)
fd = json.load(open(S + "/face.json")); pts = np.array(fd["pts"]); ff = fd["fps"]
def gsmooth(v, sigma):
    k = int(sigma * ff * 3); x = np.arange(-k, k + 1); g = np.exp(-0.5 * (x / (sigma * ff)) ** 2); g /= g.sum()
    p = np.pad(v, k, mode="edge"); return np.convolve(p, g, "valid")
fx = gsmooth(pts[:, 0], 0.35); fy = gsmooth(pts[:, 1], 0.5)
def face_at(tm):
    i = tm * ff; i0 = int(min(max(i, 0), len(fx) - 2)); a = min(max(i - i0, 0), 1)
    return fx[i0] * (1 - a) + fx[i0 + 1] * a, fy[i0] * (1 - a) + fy[i0 + 1] * a

# ---------------------------------------------------------------- impactos e cenas (zoom)
def tempo_de(d):
    if "t" in d: return d["t"]
    return tstart(d["frase"]) + d.get("dt", 0.0)
impactos = sorted(tempo_de(d) for d in CFG.get("impactos", []))
seg_t = np.array(starts)
cut_before = lambda t: int(max(0, bisect.bisect_right(starts, t + 0.05) - 1))
brk = {0}
last_b = 0.0
for i in range(1, len(keep)):
    if starts[i] - last_b >= CFG.get("cena_min", 3.4): brk.add(i); last_b = starts[i]
for ti in impactos:                     # o impacto comeca sempre num corte
    i = cut_before(ti)
    if ti - starts[i] < 2.5: brk.add(i)
brk = sorted(brk)
scene_of_seg = np.zeros(len(keep), int)
for i in range(len(keep)): scene_of_seg[i] = bisect.bisect_right(brk, i) - 1
sc_start = [starts[b] for b in brk]; sc_end = sc_start[1:] + [TOTAL]
WIDE, TIGHT = CFG.get("zoom_aberto", 1.30), CFG.get("zoom_fechado", 1.42)
base = lambda k: WIDE if k % 2 == 0 else TIGHT
IMP_AMT, IMP_DUR, PUSH = CFG.get("zoom_impacto", 0.17), 1.7, 0.04
ease = lambda x: x * x * (3 - 2 * x)
def zoom_at(t, seg):
    k = scene_of_seg[seg]; a, b = sc_start[k], sc_end[k]
    u = min(1.0, (t - a) / max(min(b - a, 8.0), 1.0))
    z = base(k) * (1 + PUSH * ease(u))
    for ti in impactos:
        if a - 0.01 <= ti < b and t >= ti:
            d = min(IMP_DUR, max(0.5, b - ti))
            z *= 1 + IMP_AMT * ease(min(1.0, (t - ti) / d)) + 0.06 * math.exp(-(t - ti) / 0.13)
    return min(z, 1.85)

# ---------------------------------------------------------------- elementos
def faixa(texto, cor, y, ang):
    L = 1700; h = 118; im = Image.new("RGBA", (L, h + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 8, L, 8 + h), fill=cor, outline=ET.BLK, width=7)
    t = f"[ {texto.upper()} ]"; size = 64
    while ET.tw(d, t, ET.inter("Black", size)) > 940 and size > 30: size -= 2
    f = ET.inter("Black", size); d.text((L / 2 - ET.tw(d, t, f) / 2, 8 + (h - size) / 2 - 8), t, font=f, fill=ET.BLK)
    r = im.rotate(ang, resample=Image.BICUBIC, expand=True)
    out = ET.canvas(); out.alpha_composite(r, (int(W / 2 - r.width / 2), int(y - r.height / 2)))
    return ET.shadow(out, 2, (10, 10), 255)
def numero(topo, valor, base_, cor, y, ang=-3):
    cw, chh = 880, 380; im = Image.new("RGBA", (cw + 60, chh + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0 = 20, 20
    d.rectangle((x0 + 18, y0 + 18, x0 + cw + 18, y0 + chh + 18), fill=cor)
    d.rectangle((x0, y0, x0 + cw, y0 + chh), fill=(255, 255, 255, 255), outline=ET.BLK, width=8)
    ft = ET.mono(36); t = f"[ {topo.upper()} ]"; d.text((x0 + 36, y0 + 30), t, font=ft, fill=ET.BLK)
    size = 190
    while ET.tw(d, valor.upper(), ET.inter("Black", size)) > cw - 80 and size > 60: size -= 6
    fv = ET.inter("Black", size); d.text((x0 + cw / 2 - ET.tw(d, valor.upper(), fv) / 2, y0 + 96), valor.upper(), font=fv, fill=ET.BLK)
    if base_:
        fb = ET.mono(38); bw = ET.tw(d, base_, fb) + 44; bx = x0 + cw - 36 - bw; by = y0 + chh - 86
        d.rectangle((bx, by, bx + bw, by + 56), fill=ET.LIMA, outline=ET.BLK, width=5); d.text((bx + 22, by + 8), base_, font=fb, fill=ET.BLK)
    r = im.rotate(ang, resample=Image.BICUBIC, expand=True)
    out = ET.canvas(); out.alpha_composite(r, (int(W / 2 - r.width / 2), int(y)))
    return out

els = CFG.get("elementos", [])
inicio = [e["inicio"] if "inicio" in e else max(0.1, tstart(e["frase"]) - 0.15) for e in els]
ELEM = []
os.makedirs(S + "/el", exist_ok=True)
for k, e in enumerate(els):
    a = inicio[k] + 0.05
    b = e["fim"] if "fim" in e else ((inicio[k + 1] if k + 1 < len(els) else TOTAL) - 0.05)
    tipo = e["tipo"]
    if tipo == "instagram": img = ET.sticker_ig(e["titulo"], e["corpo"], e.get("y", 170))
    elif tipo == "impacto": img = ET.impacto(e["linhas"], e.get("y", 150), corc(e.get("cor", "roxo")))
    elif tipo == "brutalista":
        img = ET.brutal_c(e["tag"], e["preto"], e["roxo"], [tuple(x) + (False,) * (4 - len(x)) for x in e.get("linhas", [])], e.get("y", 0),
                          {"roxo": corc(cores["roxo"]), "lima": corc(cores["lima"])})
    elif tipo == "faixa": img = faixa(e["texto"], corc(e.get("cor", "lima")), e.get("y", 250), e.get("ang", -4))
    elif tipo == "numero": img = numero(e["topo"], e["valor"], e.get("base", ""), corc(e.get("cor", "roxo")), e.get("y", 90), e.get("ang", -3))
    else: raise SystemExit("tipo de elemento desconhecido: " + tipo)
    bb = img.split()[3].getbbox()
    c = img.crop(bb); arr = np.array(c)
    rgb = arr[..., 2::-1].astype(np.float32) if False else arr[..., [2, 1, 0]].astype(np.float32)   # BGR
    al = arr[..., 3].astype(np.float32) / 255.0
    ELEM.append({"a": a, "b": b, "x": bb[0], "y": bb[1], "rgb": rgb, "al": al[..., None]})
ELEM_A = [x["a"] for x in ELEM]

def blit(fr, rgb, al, x, y, mult=1.0):
    h, w = al.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    r = rgb[y0 - y:y1 - y, x0 - x:x1 - x]; a = al[y0 - y:y1 - y, x0 - x:x1 - x] * mult
    reg = fr[y0:y1, x0:x1].astype(np.float32)
    fr[y0:y1, x0:x1] = (reg * (1 - a) + r * a).astype(np.uint8)

# ---------------------------------------------------------------- legenda brutalista (uma linha, palavra ativa destacada)
LEG = {"max_caracteres": 24, "tamanho": 50, "centro_y": 1680, **CFG.get("legenda", {})}
chunks, cur = [], []
for w in PAL:
    if cur and (w["p"] != cur[-1]["p"] or len(" ".join(x["w"] for x in cur + [w])) > LEG["max_caracteres"] or
                (cur[-1]["w"][-1] in ",.?!:" and len(" ".join(x["w"] for x in cur)) >= 11) or cur[-1]["w"][-1] in ".?!"):
        chunks.append(cur); cur = []
    cur.append(w)
if cur: chunks.append(cur)
for n, ch in enumerate(chunks):
    ch[0]["_a"] = ch[0]["s"]; b = ch[-1]["e"] + 0.15
    if n + 1 < len(chunks): b = min(b, chunks[n + 1][0]["s"])
    ch[0]["_b"] = max(b, ch[0]["s"] + 0.25)
CH_A = [c[0]["_a"] for c in chunks]
fcap = ET.inter("Black", LEG["tamanho"]); _d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
cap_cache = {}
def cap_img(ci, wi):
    key = (ci, wi)
    if key in cap_cache: return cap_cache[key]
    ws = [x["w"].upper() for x in chunks[ci]]; sp = ET.tw(_d, " ", fcap)
    widths = [ET.tw(_d, w, fcap) for w in ws]; tw_ = sum(widths) + sp * (len(ws) - 1); pad = 34
    bw, bh = int(tw_ + 2 * pad), int(LEG["tamanho"] * 1.55)
    im = Image.new("RGBA", (bw + 30, bh + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((14, 14, 14 + bw, 14 + bh), fill=corc("roxo"))
    d.rectangle((0, 0, bw, bh), fill=(255, 255, 255, 255), outline=ET.BLK, width=6)
    x = pad
    for i, (w, wd) in enumerate(zip(ws, widths)):
        if i == wi: d.rectangle((x - 9, 12, x + wd + 9, bh - 12), fill=corc("lima"))
        d.text((x, (bh - LEG["tamanho"]) / 2 - 6), w, font=fcap, fill=ET.BLK); x += wd + sp
    arr = np.array(im); rgb = arr[..., [2, 1, 0]].astype(np.float32); al = arr[..., 3:4].astype(np.float32) / 255
    cap_cache[key] = (rgb, al, bw); return cap_cache[key]

# ---------------------------------------------------------------- sfx
SR = 48000
def sfx_thump():
    t = np.arange(int(0.45 * SR)) / SR; f = 38 + 90 * np.exp(-t * 14)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 0.9).astype(np.float32)
def sfx_whoosh(d=0.42):
    n = int(d * SR); rng = np.random.default_rng(7); x = rng.standard_normal(n).astype(np.float32)
    k = np.ones(24) / 24; lo = np.convolve(x, k, "same"); x = x - lo * 0.7
    t = np.arange(n) / n; env = np.sin(np.pi * t) ** 2 * (0.3 + 0.7 * t); return (x * env * 0.25).astype(np.float32)
def sfx_click():
    t = np.arange(int(0.12 * SR)) / SR; return (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 60) * 0.35).astype(np.float32)

def montar_audio(path):
    fc = ";".join(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,aformat=sample_rates={SR}:channel_layouts=mono,apad=whole_dur={Q(e - s):.4f}[a{i}]" for i, (s, e) in enumerate(keep))
    fc += ";" + "".join(f"[a{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=0:a=1[o]"
    open(S + "/af2.txt", "w").write(fc)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex_script", S + "/af2.txt", "-map", "[o]", "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"],
                         check=True, stdout=subprocess.PIPE).stdout
    a = np.frombuffer(raw, np.float32).copy()
    a = np.pad(a, (0, max(0, int(TOTAL * SR) - len(a))))[:int(TOTAL * SR)]
    def put(t, s, g=1.0):
        i = int(t * SR); n = min(len(s), len(a) - i)
        if n > 0: a[i:i + n] += s[:n] * g
    th, wh, ck = sfx_thump(), sfx_whoosh(), sfx_click()
    for ti in impactos: put(max(0, ti - 0.12), wh, 0.9); put(ti, th, 0.95)
    for e in ELEM: put(max(0, e["a"] - 0.02), ck, 0.8)
    for b in sc_start[1:]:
        if not any(abs(b - ti) < 0.6 for ti in impactos): put(max(0, b - 0.10), wh, 0.35)
    a = np.clip(a, -0.98, 0.98)
    pcm = (a * 32767).astype(np.int16).tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "aac", "-b:a", "192k", path], input=pcm, check=True)

# ---------------------------------------------------------------- render
f0, f1 = 0, NF
if RNG: f0, f1 = int(RNG[0] * FPS), min(NF, int(RNG[1] * FPS))
vid_tmp = OUT + ".v.mp4"
dec = None; FB = W * H * 3; cur_i = -10 ** 9; cur = None
def abre(idx):
    global dec, cur_i
    if dec: dec.kill()
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{idx / FPS:.4f}", "-i", SRC, "-an", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE, bufsize=FB * 4)
    cur_i = idx - 1
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", CFG.get("preset", "medium"), "-crf", str(CFG.get("crf", 18)), "-pix_fmt", "yuv420p", vid_tmp],
                       stdin=subprocess.PIPE)
def get_frame(idx):
    global cur_i, cur
    if idx < cur_i - 1 or idx - cur_i > 120: abre(idx)          # salto para outro ponto do mestre
    while cur_i < idx:
        b = dec.stdout.read(FB)
        if len(b) < FB: break
        cur = np.frombuffer(b, np.uint8).reshape(H, W, 3); cur_i += 1
    return cur
SHARP = CFG.get("nitidez", 0.55)
Y_T = CFG.get("rosto_y", 800)
rngs = np.random.default_rng(3)
n_imp = [int(round(t * FPS)) for t in impactos]
for fi in range(f0, f1):
    t = fi / FPS; seg = seg_of[fi]
    fr = get_frame(src_idx[fi])
    ts = src_idx[fi] / FPS
    cx, cy = face_at(ts); cx *= W; cy *= H
    z = zoom_at(t, seg); cw, chh = W / z, H / z
    left = min(max(cx - cw / 2, 0), W - cw); top = min(max(cy - Y_T / z, 0), H - chh)
    tx = ty = 0.0
    for ni in n_imp:                                    # tremor curto no impacto
        if 0 <= fi - ni < 7:
            k = (1 - (fi - ni) / 7) * 14; tx += rngs.uniform(-k, k); ty += rngs.uniform(-k, k)
    M = np.float32([[z, 0, -left * z + tx], [0, z, -top * z + ty]])
    out = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    if SHARP:
        bl = cv2.GaussianBlur(out, (0, 0), 1.4); out = cv2.addWeighted(out, 1 + SHARP, bl, -SHARP, 0)
    for ni in n_imp:
        j = fi - ni
        if 0 <= j < 6:                                   # separacao RGB
            dx = int(16 * (1 - j / 6)); out[..., 2] = np.roll(out[..., 2], dx, axis=1); out[..., 0] = np.roll(out[..., 0], -dx, axis=1)
        if 0 <= j < 2: out = cv2.addWeighted(out, 1 - 0.5 / (j + 1), np.full_like(out, 255), 0.5 / (j + 1), 0)
    # elementos
    for e in ELEM:
        if e["a"] <= t < e["b"]:
            j = (t - e["a"]) * FPS
            if j < 8: dy = int(-70 * (1 - ease(j / 8)) ** 2); m = min(1.0, j / 3)
            elif e["b"] - t < 0.12: dy = 0; m = max(0.0, (e["b"] - t) / 0.12)
            else: dy = 0; m = 1.0
            blit(out, e["rgb"], e["al"], e["x"], e["y"] + dy, m)
    # legenda
    ci = bisect.bisect_right(CH_A, t) - 1
    if ci >= 0 and t < chunks[ci][0]["_b"]:
        ch = chunks[ci]; wi = max(0, bisect.bisect_right([x["s"] for x in ch], t) - 1)
        rgb, al, bw = cap_img(ci, wi)
        blit(out, rgb, al, int(W / 2 - bw / 2 - 15), int(LEG["centro_y"] - al.shape[0] / 2))
    enc.stdin.write(out.tobytes())
    if (fi - f0) % 300 == 0: print(f"frame {fi - f0}/{f1 - f0}  z={z:.2f}", flush=True)
enc.stdin.close(); enc.wait(); dec.kill()
if RNG:
    os.replace(vid_tmp, OUT); print("preview", OUT); sys.exit()
montar_audio(S + "/audio_final.m4a")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid_tmp, "-i", S + "/audio_final.m4a", "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", OUT], check=True)
os.remove(vid_tmp); print("pronto", OUT, f"{TOTAL:.1f}s")
