"""Monta o video: cortes + legenda em caixa (1 linha) alinhada a fala + elementos no topo.
uso: python3 build_estilos.py <video_original> <dir de trabalho com keep.json> <saida.mp4>"""
import json, math, re, subprocess, sys, os, difflib, unicodedata
from PIL import ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elementos_topo as ET
SRC, S, OUT = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
keep = json.load(open(S + "/keep.json"))
roteiro = json.load(open(HERE + "/roteiro_estilos.json"))
Q = lambda d: max(1, math.ceil(d * 30 - 1e-6)) / 30      # o corte fecha em frames de 1/30s
starts, acc = [], 0.0
for s, e in keep: starts.append(acc); acc += Q(e - s)
TOTAL = acc

# ---------- palavras com tempo (whisper no audio ja cortado)
def audio_final(path):
    fc = ";".join(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,aformat=sample_rates=16000:channel_layouts=mono,apad=whole_dur={Q(e - s):.4f}[a{i}]" for i, (s, e) in enumerate(keep))
    fc += ";" + "".join(f"[a{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=0:a=1[o]"
    open(S + "/af.txt", "w").write(fc)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex_script", S + "/af.txt", "-map", "[o]", "-ar", "16000", "-ac", "1", path], check=True)
def palavras_reconhecidas():
    cache = S + "/palavras_final.json"
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(S + "/keep.json"): return json.load(open(cache))
    import numpy as np
    from faster_whisper import WhisperModel
    audio_final(S + "/final.wav")
    a = np.fromfile(S + "/final.wav", dtype=np.int16, offset=44).astype(np.float32) / 32768
    segs, _ = WhisperModel("medium", compute_type="int8").transcribe(a, language="pt", word_timestamps=True, condition_on_previous_text=False)
    w = [{"w": x.word.strip(), "s": x.start, "e": x.end} for s in segs for x in s.words]
    json.dump(w, open(cache, "w"), ensure_ascii=False); return w
norm = lambda t: re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", t.lower()).encode("ascii", "ignore").decode())

def alinhar():
    rec = palavras_reconhecidas()
    sw = [(pi, w) for pi, t in enumerate(roteiro) for w in t.split()]
    sn = [norm(w) for _, w in sw]; vocab = sorted(set(sn))
    rn = []
    for r in rec:
        n = norm(r["w"]); c = difflib.get_close_matches(n, vocab, n=1, cutoff=0.8); rn.append(c[0] if c else n)
    t = [None] * len(sw)
    for i, j, size in difflib.SequenceMatcher(None, sn, rn, autojunk=False).get_matching_blocks():
        for k in range(size):
            if size >= 2 or len(sn[i + k]) >= 5: t[i + k] = (rec[j + k]["s"], rec[j + k]["e"])
    # interpola o que nao casou, proporcional ao tamanho da palavra
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
        s = max(s, last); e = max(e, s + 0.08); res.append({"p": pi, "w": w, "s": s, "e": e}); last = s
    return res
PAL = alinhar()

# ---------- legenda: uma linha curta por vez
MAXC = 24
chunks, cur = [], []
for w in PAL:
    if cur and (w["p"] != cur[-1]["p"] or len(" ".join(x["w"] for x in cur + [w])) > MAXC or
                (cur[-1]["w"][-1] in ",.?!:" and len(" ".join(x["w"] for x in cur)) >= 11) or cur[-1]["w"][-1] in ".?!"):
        chunks.append(cur); cur = []
    cur.append(w)
if cur: chunks.append(cur)

FONT_PX = 46
pil = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", FONT_PX)
KW = 1.0          # calibracao largura libass / Pillow
CY = 1700         # centro vertical da legenda
def ts(t):
    t = max(0, t); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
def rr(w, h, r):
    k = 0.5523 * r
    return (f"m {r} 0 l {w - r} 0 b {w - r + k:.1f} 0 {w} {r - k:.1f} {w} {r} l {w} {h - r} b {w} {h - r + k:.1f} {w - r + k:.1f} {h} {w - r} {h} "
            f"l {r} {h} b {r - k:.1f} {h} 0 {h - r + k:.1f} 0 {h - r} l 0 {r} b 0 {r - k:.1f} {r - k:.1f} 0 {r} 0")
ev = []
def E(a, b, style, text, layer=0): ev.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}")
for n, ch in enumerate(chunks):
    a = ch[0]["s"]; b = ch[-1]["e"] + 0.15
    if n + 1 < len(chunks): b = min(b, chunks[n + 1][0]["s"])
    b = max(b, a + 0.25)
    txt = " ".join(x["w"] for x in ch).replace("{", "(")
    w = pil.getlength(txt) * KW + 2 * 34; h = FONT_PX * 1.5 + 6
    E(a, b, "Cap", f"{{\\an7\\pos({540 - w / 2:.0f},{CY - h / 2:.0f})\\bord0\\shad0\\1c&H000000&\\1a&H55&\\fad(70,70)\\p1}}{rr(int(w), int(h), 22)}", 0)
    E(a, b, "Cap", f"{{\\an5\\pos(540,{CY})\\fad(70,70)}}{txt}", 1)

# ---------- elementos do topo
def tstart(p): return min(x["s"] for x in PAL if x["p"] == p)
ROXO, LIMA = ET.ROXO, ET.LIMA
SECS = [  # 1a frase de cada trecho
    (0, lambda a, b: put("e0", ET.sticker_ig("Qual é o teste?", "Enviar um vídeo com mais de 30 MB para o Claude Code editar", 170), a, b)),
    (2, lambda a, b: put("e1", ET.impacto(["Edição *INTERESSANTE*", "só para *TESTAR*"], 150, ROXO), a, b)),
    (4, lambda a, b: put("e2", ET.brutal_c("arquivo", "vídeo", "x chat", [("vídeo original", "+30 MB", "↑ grande demais", False), ("pelo chat", "30 MB", "não passa", True)]), a, b)),
    (6, lambda a, b: put("e3", ET.impacto(["Vídeo final de", "*1 MINUTO* pós-edição"], 150, LIMA), a, b)),
    (7, lambda a, b: put("e4", ET.sticker_ig("Qual é a ideia?", "Testar vários estilos de edição no mesmo vídeo", 170), a, b)),
    (9, lambda a, b: put("e5", ET.impacto(["Você *SELECIONA*", "os melhores"], 150, ROXO), a, b)),
    (11, lambda a, b: put("e6", ET.brutal_c("skill", "edição", "padrão", [("edição", "simples", "↑ vira skill", False)]), a, b)),
    (13, lambda a, b: put("e7", ET.impacto(["Legenda *EMBAIXO*", "texto *NO TOPO*"], 150, LIMA), a, b)),
    (15, lambda a, b: put("e8", ET.brutal_c("animação", "se pedir", "entra", [("gráfico", "falando", "↑ Claude Code", False)]), a, b)),
]
bounds = [0.0] + [max(0.1, tstart(p0) - 0.15) for p0, _ in SECS[1:]] + [TOTAL]
ELEM = []   # (png, inicio, fim)
os.makedirs(S + "/el", exist_ok=True)
def put(name, img, a, b):
    p = f"{S}/el/{name}.png"; img.save(p); ELEM.append((p, a, b))
for k, (p0, fn) in enumerate(SECS): fn(bounds[k] + 0.1, bounds[k + 1] - 0.05)

HDR = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
"""
STY = [f"Style: Cap,Inter SemiBold,{FONT_PX},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,20,20,20,1",
       "Style: Tag,Inter Bold,32,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,2,0,7,36,36,34,1"]
open(S + "/estilos.ass", "w").write(HDR + "\n".join(STY) + "\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n" + "\n".join(ev) + "\n")
json.dump({"palavras": PAL, "bounds": bounds, "total": TOTAL}, open(S + "/linha.json", "w"), ensure_ascii=False)

# ---------- filtro
n = len(keep); fc = []
for i in range(n):
    fc.append(f"[{i}:v]setpts=PTS-STARTPTS,fps=30,scale=1080:1920,setsar=1,format=yuv420p[v{i}]")
    fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][aout]")
last = "vc"
for k, (png, a, b) in enumerate(ELEM):
    idx = n + k; d = b - a
    fc.append(f"[{idx}:v]format=rgba,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st={max(0, d - 0.2):.3f}:d=0.2:alpha=1,setpts=PTS+{a:.3f}/TB[el{k}]")
    fc.append(f"[{last}][el{k}]overlay=x=0:y='34*(1-min(1,max(0,(t-{a:.3f})/0.3)))':eof_action=pass[o{k}]"); last = f"o{k}"
fc.append(f"[{last}]ass={S}/estilos.ass[vf]")
open(S + "/filtro.txt", "w").write(";\n".join(fc))
ins = [x for s, e in keep for x in ("-ss", str(s), "-t", f"{e - s:.3f}", "-i", SRC)]
for png, a, b in ELEM: ins += ["-loop", "1", "-framerate", "30", "-t", f"{b - a + 0.1:.3f}", "-i", png]
print("total", round(TOTAL, 2), "secoes", [round(x, 1) for x in bounds])
subprocess.run(["ffmpeg", "-v", "error", "-nostats", "-y", *ins, "-filter_complex_script", S + "/filtro.txt", "-map", "[vf]", "-map", "[aout]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT], check=True)
