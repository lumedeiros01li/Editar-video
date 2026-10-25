"""Monta o video de teste de estilos: cortes + legendas (ASS) + texto no topo + efeitos por secao.
uso: python3 build_estilos.py <video_original> <dir com keep.json> <saida.mp4>"""
import json, math, re, subprocess, sys, os
SRC, S, OUT = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
keep = json.load(open(S + "/keep.json"))
roteiro = json.load(open(HERE + "/roteiro_estilos.json"))
starts, acc = [], 0.0
for s, e in keep: starts.append(acc); acc += math.ceil((e - s) * 30 - 1e-6) / 30  # o corte fecha em frames de 1/30s
TOTAL = acc

def mp(t):
    for (s, e), o in zip(keep, starts):
        if t <= e: return o + max(0.0, t - s)
    return TOTAL

# ---- frases: palavras distribuidas pelo tempo de saida, proporcional ao tamanho
frases = []
for r in roteiro:
    a, b = mp(r["s"]), mp(r["e"])
    if b - a < 0.4: b = a + 0.4
    ws = r["t"].split()
    tot = sum(len(w) + 2 for w in ws); t = a; lst = []
    for w in ws:
        d = (b - a) * (len(w) + 2) / tot
        lst.append({"w": w, "s": t, "e": t + d}); t += d
    frases.append(lst)

def chunks(ws, n=4):
    out, cur = [], []
    for w in ws:
        cur.append(w)
        if len(cur) >= n or re.search(r"[.?!:]$", w["w"]) or (re.search(r",$", w["w"]) and len(cur) >= 3):
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out

# ---- secoes: (nome, indice da primeira frase, titulo do topo)
SEC = [
    ("CLASSICO",   0, "Teste de edição com Claude Code"),
    ("KARAOKE",    2, "Enviando vídeo acima de 30 MB"),
    ("CAIXA",      5, "Como mandar o arquivo grande?"),
    ("PALAVRA",    8, "Vários estilos de edição"),
    ("MINIMAL",   11, "Escolher e virar uma skill"),
    ("GRAFICO",   14, "Legenda + texto + animação"),
]
bounds = [frases[i][0]["s"] for _, i, _ in SEC] + [TOTAL]
bounds[0] = 0.0
# cada fronteira vira o inicio do segmento de corte mais proximo
for k in range(1, len(SEC)):
    bounds[k] = min(starts, key=lambda x: abs(x - bounds[k]))

def sec_of(t):
    for k in range(len(SEC)):
        if bounds[k] - 1e-6 <= t < bounds[k + 1] - 1e-6: return k
    return len(SEC) - 1

def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

HDR = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
"""
# cores ASS = &HAABBGGRR
STY = [
 "Style: Classico,Inter,68,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,70,70,210,1",
 "Style: Karaoke,Inter Black,72,&H0000E5FF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,3,2,70,70,210,1",
 "Style: Caixa,Inter SemiBold,60,&H00FFFFFF,&H00FFFFFF,&HB0000000,&H00000000,0,0,0,0,100,100,0,0,3,16,0,2,90,90,210,1",
 "Style: Palavra,Inter Black,120,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,9,4,2,40,40,260,1",
 "Style: Minimal,Inter Medium,52,&H00F0F0F0,&H00F0F0F0,&H00000000,&H60000000,0,0,0,0,100,100,1,0,1,0,3,2,120,120,230,1",
 "Style: T_Classico,Inter,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,3,8,60,60,110,1",
 "Style: T_Pill,Inter Bold,58,&H00FFFFFF,&H00FFFFFF,&H00C9640F,&H00000000,1,0,0,0,100,100,0,0,3,22,0,8,60,60,100,1",
 "Style: T_Faixa,Inter Bold,56,&H00FFFFFF,&H00FFFFFF,&HB4000000,&H00000000,1,0,0,0,100,100,0,0,3,24,0,8,0,0,130,1",
 "Style: T_Grande,Inter Black,92,&H0000E5FF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,8,4,8,50,50,90,1",
 "Style: T_Serif,DejaVu Serif,54,&H00F0F0F0,&H00F0F0F0,&H00000000,&H60000000,0,1,0,0,100,100,2,0,1,0,3,8,60,60,100,1",
 "Style: T_Grafico,Inter Bold,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,3,8,60,60,70,1",
 "Style: Tag,Inter Bold,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,2,0,7,36,36,34,1",
]
TSTY = ["T_Classico", "T_Pill", "T_Faixa", "T_Grande", "T_Serif", "T_Grafico"]
ev = []
def E(a, b, style, text, layer=0): ev.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}")

esc = lambda s: s.replace("{", "(").replace("}", ")")
for k, (nome, i0, titulo) in enumerate(SEC):
    a, b = bounds[k], bounds[k + 1]
    tit = titulo.upper() if k in (1, 3) else titulo
    if k == 2: tit = "   " + titulo + "   "
    E(a, b, TSTY[k], "{\\fad(150,120)}" + esc(tit))
    if k == 4: E(a, b, "T_Serif", "{\\an8\\pos(540,205)\\fs1\\1c&H00F0F0F0&\\p1}m 0 0 l 260 0 l 260 3 l 0 3{\\p0}", 1)
    E(a, b, "Tag", f"{{\\alpha&H60&}}ESTILO {k + 1} · {nome}", 2)

for fr in frases:
    for ch in chunks(fr, 3 if False else 4):
        a, b = ch[0]["s"], ch[-1]["e"]
        k = sec_of(a)
        # a legenda nao atravessa fronteira de secao
        b = min(b, bounds[k + 1])
        if b - a < 0.15: continue
        nome = SEC[k][0]
        txt = " ".join(w["w"] for w in ch)
        if nome == "CLASSICO":
            E(a, b, "Classico", "{\\fad(60,60)}" + esc(txt))
        elif nome == "KARAOKE":
            parts = "".join(f"{{\\kf{max(1, int(round((w['e'] - w['s']) * 100)))}}}{esc(w['w'])} " for w in ch)
            E(a, b, "Karaoke", parts.strip())
        elif nome == "CAIXA":
            E(a, b, "Caixa", "{\\fad(80,80)}" + esc(txt.upper()))
        elif nome == "PALAVRA":
            for j in range(0, len(ch), 2):
                g = ch[j:j + 2]
                ga, gb = g[0]["s"], min(g[-1]["e"], bounds[k + 1])
                if gb - ga < 0.12: gb = ga + 0.12
                words = [esc(w["w"].upper()) for w in g]
                words[-1] = "{\\1c&H0000E5FF&}" + words[-1]
                E(ga, gb, "Palavra", "{\\fscx70\\fscy70\\t(0,90,\\fscx100\\fscy100)}" + " ".join(words))
        elif nome == "MINIMAL":
            E(a, b, "Minimal", "{\\fad(140,140)}" + esc(txt.lower() if False else txt))
        else:
            E(a, b, "Classico", "{\\fad(60,60)}" + esc(txt))
open(S + "/estilos.ass", "w").write(HDR + "\n".join(STY) + "\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n" + "\n".join(ev) + "\n")

# ---- filtro de video/audio
fc = []
for i, ((s, e), o) in enumerate(zip(keep, starts)):
    k = sec_of(o + 1e-3)
    v = f"[{i}:v]setpts=PTS-STARTPTS,fps=30,scale=1080:1920,setsar=1"
    z = 1.0
    if SEC[k][0] == "KARAOKE" and int(o // 2.6) % 2 == 1: z = 1.12
    if SEC[k][0] == "PALAVRA" and int(o // 1.8) % 2 == 1: z = 1.2
    if z != 1.0:
        v += f",crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:(ih-ih/{z})*0.3,scale=1080:1920"
    if SEC[k][0] == "MINIMAL": v += ",eq=contrast=1.1:saturation=0.8:brightness=-0.03,vignette=PI/5"
    if SEC[k][0] == "CAIXA": v += ",eq=saturation=1.15:gamma_r=1.04:gamma_b=0.96"
    if SEC[k][0] == "GRAFICO": v += ",eq=saturation=1.1:gamma_b=1.05"
    fc.append(v + f",format=yuv420p,setsar=1[v{i}]")
    fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
n = len(keep)
fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
g0, g1 = bounds[5], TOTAL
fc.append("[ac]asplit=2[aout][aw]")
fc.append("[aw]dynaudnorm=f=150:g=7,volume=2,showfreqs=s=900x130:mode=bar:fscale=log:ascale=cbrt:win_size=1024:colors=0x4DE1FF|0x4DE1FF:overlap=0.7:averaging=2,format=rgba[wv]")
fc.append(f"[vc][wv]overlay=x=90:y=200:enable='between(t,{g0:.3f},{g1:.3f})'[vo]")
fc.append(f"[vo]ass={S}/estilos.ass[vf]")
open(S + "/filtro.txt", "w").write(";\n".join(fc))
ins = [x for s, e in keep for x in ("-ss", str(s), "-t", f"{e - s:.3f}", "-i", SRC)]
cmd = ["ffmpeg", "-v", "error", "-nostats", "-y", *ins, "-filter_complex_script", S + "/filtro.txt",
       "-map", "[vf]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
print("frases", [round(f[0]["s"], 1) for f in frases])
print("total", round(TOTAL, 2), "secoes", [round(x, 2) for x in bounds])
subprocess.run(cmd, check=True)
