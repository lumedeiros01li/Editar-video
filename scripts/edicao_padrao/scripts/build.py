"""Monta o video final: cortes + legenda em caixa (1 linha) alinhada a fala + elementos no topo.

uso:
  python3 build.py transcrever <video> <dir>                    # lista as frases com tempo (linha do tempo ja cortada)
  python3 build.py montar <video> <dir> <config.json> <saida>   # renderiza
O <dir> precisa ter o keep.json gerado por cortes.py."""
import json, math, re, subprocess, sys, os, difflib, unicodedata
from PIL import ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elementos as ET
MODO, SRC, S = sys.argv[1:4]
keep = json.load(open(S + "/keep.json"))
Q = lambda d: max(1, math.ceil(d * 30 - 1e-6)) / 30      # o corte fecha em frames de 1/30s
starts, acc = [], 0.0
for s, e in keep: starts.append(acc); acc += Q(e - s)
TOTAL = acc

# ---------- palavras com tempo (whisper no audio ja cortado)
def audio_final(path):
    fc = ";".join(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,aformat=sample_rates=16000:channel_layouts=mono,apad=whole_dur={Q(e - s):.4f}[a{i}]" for i, (s, e) in enumerate(keep))
    fc += ";" + "".join(f"[a{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=0:a=1[o]"
    open(S + "/af.txt", "w").write(fc)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex_script", S + "/af.txt", "-map", "[o]", "-ar", "16000", "-ac", "1", "-f", "s16le", path], check=True)
def reconhecidas():
    cache = S + "/palavras_final.json"
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(S + "/keep.json"): return json.load(open(cache))
    import numpy as np
    from faster_whisper import WhisperModel
    audio_final(S + "/final.raw")
    a = np.fromfile(S + "/final.raw", dtype=np.int16).astype(np.float32) / 32768
    segs, _ = WhisperModel("medium", compute_type="int8").transcribe(a, language="pt", word_timestamps=True, condition_on_previous_text=False)
    w = [{"p": i, "w": x.word.strip(), "s": x.start, "e": x.end} for i, s in enumerate(segs) for x in s.words]
    json.dump(w, open(cache, "w"), ensure_ascii=False); return w
norm = lambda t: re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", t.lower()).encode("ascii", "ignore").decode())
mmss = lambda t: f"{int(t // 60)}:{t % 60:04.1f}"

if MODO == "transcrever":
    rec = reconhecidas(); ps = sorted({w["p"] for w in rec})
    print(f"duracao final {TOTAL:.1f}s")
    for p in ps:
        ws = [w for w in rec if w["p"] == p]
        print(f"[{p}] {mmss(ws[0]['s'])}-{mmss(ws[-1]['e'])}  " + " ".join(w["w"] for w in ws))
    sys.exit()

CFG = json.load(open(sys.argv[4])); OUT = sys.argv[5]
roteiro = CFG.get("roteiro")                 # frases corrigidas; sem isso usa o texto do whisper
cores = {"roxo": "#9B6BFF", "lima": "#E4FF6B", **CFG.get("cores", {})}
corc = lambda c: ET.hexc(cores.get(c, c)) if c else None

def alinhar():
    rec = reconhecidas()
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
    while i < len(sw):          # o que nao casou e interpolado entre as ancoras, proporcional ao tamanho da palavra
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
def tword(p, palavra):          # inicio da 1a ocorrencia da palavra na frase p
    for x in PAL:
        if x["p"] == p and norm(x["w"]) == norm(palavra): return x["s"]
    raise SystemExit(f"palavra {palavra!r} nao encontrada na frase {p}")

# ---------- legenda em caixa, uma linha curta por vez
LEG = {"max_caracteres": 24, "tamanho": 46, "centro_y": 1700, **CFG.get("legenda", {})}
chunks, cur = [], []
for w in PAL:
    if cur and (w["p"] != cur[-1]["p"] or len(" ".join(x["w"] for x in cur + [w])) > LEG["max_caracteres"] or
                (cur[-1]["w"][-1] in ",.?!:" and len(" ".join(x["w"] for x in cur)) >= 11) or cur[-1]["w"][-1] in ".?!"):
        chunks.append(cur); cur = []
    cur.append(w)
if cur: chunks.append(cur)
FONT_PX, CY = LEG["tamanho"], LEG["centro_y"]
pil = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", FONT_PX)
ts = lambda t: f"{int(max(0, t) // 3600)}:{int(max(0, t) % 3600 // 60):02d}:{max(0, t) % 60:05.2f}"
def rr(w, h, r):
    k = 0.5523 * r
    return (f"m {r} 0 l {w - r} 0 b {w - r + k:.1f} 0 {w} {r - k:.1f} {w} {r} l {w} {h - r} b {w} {h - r + k:.1f} {w - r + k:.1f} {h} {w - r} {h} "
            f"l {r} {h} b {r - k:.1f} {h} 0 {h - r + k:.1f} 0 {h - r} l 0 {r} b 0 {r - k:.1f} {r - k:.1f} 0 {r} 0")
ev = []
for n, ch in enumerate(chunks):
    a = ch[0]["s"]; b = ch[-1]["e"] + 0.15
    if n + 1 < len(chunks): b = min(b, chunks[n + 1][0]["s"])
    b = max(b, a + 0.25)
    txt = " ".join(x["w"] for x in ch).replace("{", "(")
    w = pil.getlength(txt) + 68; h = FONT_PX * 1.5 + 6
    ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\an7\\pos({540 - w / 2:.0f},{CY - h / 2:.0f})\\bord0\\shad0\\1c&H000000&\\1a&H55&\\fad(70,70)\\p1}}{rr(int(w), int(h), 22)}")
    ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\an5\\pos(540,{CY})\\fad(70,70)}}{txt}")
HDR = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
"""
STY = f"Style: Cap,Inter SemiBold,{FONT_PX},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,20,20,20,1"
open(S + "/legenda.ass", "w").write(HDR + STY + "\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n" + "\n".join(ev) + "\n")

# ---------- elementos do topo: cada um vai do seu inicio ate o inicio do proximo
els = CFG.get("elementos", [])
inicio = [e["inicio"] if "inicio" in e else max(0.1, tstart(e["frase"]) - 0.15) for e in els]
ELEM = []
os.makedirs(S + "/el", exist_ok=True)
for k, e in enumerate(els):
    a = inicio[k] + 0.1
    b = e["fim"] if "fim" in e else ((inicio[k + 1] if k + 1 < len(els) else TOTAL) - 0.05)
    tipo = e["tipo"]
    if tipo == "instagram": img = ET.sticker_ig(e["titulo"], e["corpo"], e.get("y", 170))
    elif tipo == "impacto": img = ET.impacto(e["linhas"], e.get("y", 150), corc(e.get("cor", "roxo")))
    elif tipo == "brutalista":
        img = ET.brutal_c(e["tag"], e["preto"], e["roxo"], [tuple(x) + (False,) * (4 - len(x)) for x in e.get("linhas", [])], e.get("y", 0),
                          {"roxo": corc(cores["roxo"]), "lima": corc(cores["lima"])})
    else: raise SystemExit(f"tipo de elemento desconhecido: {tipo}")
    p = f"{S}/el/e{k}.png"; img.save(p); ELEM.append((p, a, b))

# ---------- cartoes laterais (idade -> valor), a esquerda e grandes
LC = {"x": 24, "y": 500, "largura": 336, "altura": 240, "espaco": 28, **CFG.get("laterais_cfg", {})}
LAT = []
for k, l in enumerate(CFG.get("laterais", [])):
    ta = l["inicio"] if "inicio" in l else max(0.1, tword(l["frase"], l["palavra_idade"]) - 0.1)
    tv = l["valor_em"] if "valor_em" in l else tword(l["frase"], l["palavra_valor"])
    y = LC["y"] + k * (LC["altura"] + LC["espaco"])
    for est, (a, b) in (("a", (ta, tv)), ("b", (tv, TOTAL))):
        img = ET.lateral(l["idade"], l["valor"], est == "b", LC["x"], y, LC["largura"], LC["altura"], {"roxo": corc(cores["roxo"])})
        p = f"{S}/el/l{k}{est}.png"; img.save(p); LAT.append((p, a, b, est))

# ---------- filtro e render (1080x1920, 30fps)
n = len(keep); fc = []
for i in range(n):
    fc.append(f"[{i}:v]setpts=PTS-STARTPTS,fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p[v{i}]")
    fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][aout]")
last = "vc"
R = int(CFG.get("reenquadrar", 0))          # desce o video e preenche o topo com o proprio fundo desfocado
if R:
    fc.append(f"[vc]split[m1][m2];[m1]crop=1080:{1920 - R}:0:0[body];[m2]crop=1080:{R}:0:0,vflip,gblur=sigma=30[top];[top][body]vstack[vr]"); last = "vr"
for k, (png, a, b) in enumerate(ELEM):
    idx = n + k; d = b - a
    fc.append(f"[{idx}:v]format=rgba,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st={max(0, d - 0.2):.3f}:d=0.2:alpha=1,setpts=PTS+{a:.3f}/TB[el{k}]")
    fc.append(f"[{last}][el{k}]overlay=x=0:y='34*(1-min(1,max(0,(t-{a:.3f})/0.3)))':eof_action=pass[o{k}]"); last = f"o{k}"
for j, (png, a, b, est) in enumerate(LAT):
    idx = n + len(ELEM) + j
    if est == "a":
        fc.append(f"[{idx}:v]format=rgba,fade=t=in:st=0:d=0.2:alpha=1,setpts=PTS+{a:.3f}/TB[lt{j}]")
        fc.append(f"[{last}][lt{j}]overlay=x='-90*(1-min(1,max(0,(t-{a:.3f})/0.25)))':y=0:eof_action=pass[l{j}]")
    else:
        fc.append(f"[{idx}:v]format=rgba,setpts=PTS+{a:.3f}/TB[lt{j}]")
        fc.append(f"[{last}][lt{j}]overlay=x=0:y=0:eof_action=pass[l{j}]")
    last = f"l{j}"
fc.append(f"[{last}]ass={S}/legenda.ass[vf]")
AMAP = "[aout]"
if CFG.get("tratar_voz"):                    # limpa e nivela a voz: sem ruido, EQ, de-esser, compressor, -14 LUFS
    fc.append("[aout]pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,highpass=f=85,afftdn=nr=14:nf=-38:tn=1,"
              "equalizer=f=230:t=q:w=1:g=-2.5,equalizer=f=120:t=q:w=0.8:g=1.5,equalizer=f=3200:t=q:w=1:g=3,"
              "equalizer=f=8000:t=h:w=0.7:g=2,deesser=i=0.25:m=0.5:f=0.5,"
              "acompressor=threshold=0.1:ratio=3.2:attack=6:release=90:makeup=3,"
              "loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.84:level=0[aov]"); AMAP = "[aov]"
open(S + "/filtro.txt", "w").write(";\n".join(fc))
ins = [x for s, e in keep for x in ("-ss", str(s), "-t", f"{e - s:.3f}", "-i", SRC)]
for png, a, b in ELEM: ins += ["-loop", "1", "-framerate", "30", "-t", f"{b - a + 0.1:.3f}", "-i", png]
for png, a, b, est in LAT: ins += ["-loop", "1", "-framerate", "30", "-t", f"{b - a + 0.1:.3f}", "-i", png]
print(f"duracao {TOTAL:.1f}s, {n} cortes, {len(ELEM)} elementos, {len(LAT)} laterais")
subprocess.run(["ffmpeg", "-v", "error", "-nostats", "-y", *ins, "-filter_complex_script", S + "/filtro.txt", "-map", "[vf]", "-map", AMAP,
                "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT], check=True)
