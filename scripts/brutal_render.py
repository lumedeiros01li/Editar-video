"""Edicao brutalista: zooms nos cortes e nas palavras-chave, grade de imagem,
tratamento de voz, sound design, titulo/cards/legenda em blocos duros.

uso: python3 brutal_render.py video_original.mp4 saida.mp4
"""
import json, os, subprocess, sys, tempfile
from PIL import ImageFont
from leve_cortes import SEGMENTS, FADE, starts
from leve_render import fix_words, chunk, ts
import brutal_sfx

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/usr/share/fonts/opentype/inter"
W, H = 1080, 1920
YEL, BLK, WHT, GRY = "&H0000E6FF&", "&H00000000&", "&H00F2F2F2&", "&H00808080&"

# (tempo na linha do tempo final, tamanho do hit) nas palavras-chave
IMPACTS = [(0.90, "s"), (1.90, "m"), (7.02, "s"), (9.25, "l"), (10.74, "s"), (12.32, "l"),
           (14.86, "s"), (17.28, "l"), (21.66, "m"), (24.86, "l"), (26.74, "s"), (29.24, "m")]
PULSE = {"s": 0.04, "m": 0.065, "l": 0.095}
# cortes "virtuais" dentro da fala continua, para o ritmo de zoom
VIRTUAL = [1.70, 2.92, 5.36, 8.16, 11.44, 15.78, 21.10, 22.62, 24.42, 28.02]
LEVELS = [1.00, 1.13, 1.04, 1.17]
PUSH = 0.05
KEYWORDS = {"60", "10", "mil", "25", "35", "45", "12", "reais", "dobra", "idade", "seu?", "R$ 3.150,", "R$ 5.750"}
CARDS = [("25 ANOS", "R$ 3.150", 6.95, 9.25), ("35 ANOS", "R$ 5.750", 10.68, 12.30), ("45 ANOS", "R$ 12.300", 14.78, 17.28)]
SLAMS = [("QUASE 2X", 21.35, 22.45), ("MAIS DE 2X", 24.60, 25.75)]


def zoom_expr(cuts, total):
    bounds = sorted(set([0.0, total] + cuts + VIRTUAL))
    parts = []
    for i, (a, b) in enumerate(zip(bounds, bounds[1:])):
        z0 = LEVELS[i % len(LEVELS)]
        parts.append(f"gte(t,{a:.3f})*lt(t,{b:.3f})*({z0}+{PUSH}*(t-{a:.3f})/{b-a:.3f})")
    for t, s in IMPACTS:
        parts.append(f"gte(t,{t:.3f})*lt(t,{t+0.4:.3f})*{PULSE[s]}*pow(1-(t-{t:.3f})/0.4,2)")
    return "+".join(parts)


def shake_expr(amp):
    parts = []
    for t, s in IMPACTS:
        if s == "s": continue
        parts.append(f"gte(t,{t:.3f})*lt(t,{t+0.25:.3f})*{amp*PULSE[s]/0.065:.1f}*sin(70*t)*(1-(t-{t:.3f})/0.25)")
    return "+".join(parts) or "0"


def rect(L, a, b, x, y, w, h, color, layer, move=None):
    pos = move or f"\\pos({x},{y})"
    L.append(f"Dialogue: {layer},{ts(a)},{ts(b)},Box,,0,0,0,,{{\\an7{pos}\\p1\\1c{color}\\bord0\\shad0}}m 0 0 l {w} 0 l {w} {h} l 0 {h}")


def build_ass(words, total):
    cap_font = ImageFont.truetype(f"{FONTS}/Inter-Black.otf", 64)
    big = ImageFont.truetype(f"{FONTS}/Inter-Black.otf", 118)
    L = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Box,Inter,20,{WHT},{WHT},{BLK},{BLK},0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Tag,DejaVu Sans Mono,38,{WHT},{WHT},{BLK},{BLK},-1,0,0,0,100,100,0,0,3,12,0,7,0,0,0,1
Style: Mono,DejaVu Sans Mono,26,{WHT},{WHT},{BLK},{BLK},-1,0,0,0,100,100,0,0,1,3,0,9,0,0,0,1
Style: Big,Inter Black,118,{BLK},{BLK},{BLK},{BLK},0,0,0,0,100,100,-2,0,1,0,0,5,0,0,0,1
Style: Val,Inter Black,46,{BLK},{BLK},{BLK},{BLK},0,0,0,0,100,100,-1,0,1,0,0,5,0,0,0,1
Style: Strip,DejaVu Sans Mono,34,{WHT},{WHT},{BLK},{BLK},-1,0,0,0,100,100,0,0,1,0,0,4,0,0,0,1
Style: Cap,Inter Black,64,{BLK},{BLK},{WHT},{BLK},0,0,0,0,100,100,-1,0,3,16,0,2,40,40,430,1
Style: Slam,Inter Black,150,{BLK},{BLK},{YEL},{BLK},0,0,0,0,100,100,-3,0,3,26,16,5,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"""]
    ev = lambda l, a, b, st, txt: L.append(f"Dialogue: {l},{ts(a)},{ts(b)},{st},,0,0,0,,{txt}")
    slide = lambda x, y, dx=-40, d=110: f"\\move({x+dx},{y},{x},{y},0,{d})"

    # --- marcas tecnicas: cantoneiras e timecode ---
    for cx, cy, sx, sy in [(26, 26, 1, 1), (W - 26, 26, -1, 1), (26, H - 26, 1, -1), (W - 26, H - 26, -1, -1)]:
        for (w_, h_) in [(56, 5), (5, 56)]:
            x0 = cx if sx > 0 else cx - w_
            y0 = cy if sy > 0 else cy - h_
            rect(L, 0, total, x0, y0, w_, h_, WHT, 5)
    for s in range(int(total) + 1):
        ev(5, s, min(s + 1, total), "Mono", f"{{\\pos({W-44},58)}}REC 00:{s:02d}/00:{int(total):02d}")

    # --- titulo: bloco amarelo com sombra dura, alinhado a esquerda ---
    ev(4, 0, total, "Tag", f"{{{slide(52, 58)}}}[01] APOSENTAR AOS 60 ANOS")
    tw = int(big.getlength("R$ 10.000")) + 56
    bx, by, bh = 40, 130, 150
    rect(L, 0, total, bx + 12, by + 12, tw + 12, bh + 12, BLK, 3, slide(bx + 12, by + 12))
    rect(L, 0, total, bx - 6, by - 6, tw + 12, bh + 12, BLK, 3, slide(bx - 6, by - 6))
    rect(L, 0, total, bx, by, tw, bh, YEL, 4, slide(bx, by))
    ev(5, 0, total, "Big", f"{{{slide(bx + tw // 2, by + bh // 2 + 4)}}}R$ 10.000")
    ev(5, 0, total, "Tag", f"{{{slide(bx + tw + 34, by + bh - 64)}\\fs46}}DE RENDA")

    # --- cards idade -> valor ---
    cw, sh, bh2, gap, cx, cy0 = 268, 50, 92, 32, 772, 330
    for k, (age, val, ta, tv) in enumerate(CARDS):
        cy = cy0 + k * (sh + bh2 + gap)
        mv = lambda x, y: slide(x, y, 70, 120)
        rect(L, ta, total, cx - 5, cy - 5, cw + 10, sh + bh2 + 10, BLK, 3, mv(cx - 5, cy - 5))
        rect(L, ta, total, cx + 9, cy + 9, cw + 10, sh + bh2 + 10, BLK, 3, mv(cx + 9, cy + 9))
        rect(L, ta, total, cx, cy, cw, sh, BLK, 4, mv(cx, cy))
        rect(L, ta, tv, cx, cy + sh, cw, bh2, WHT, 4, mv(cx, cy + sh))
        rect(L, tv, total, cx, cy + sh, cw, bh2, YEL, 4)
        ev(5, ta, total, "Strip", f"{{{mv(cx + 14, cy + sh // 2)}}}{age}")
        ev(5, ta, tv, "Strip", f"{{\\an5\\pos({cx + cw // 2},{cy + sh + bh2 // 2})\\1c{GRY}\\fs34}}R$ ----")
        ev(5, tv, total, "Val", f"{{\\pos({cx + cw // 2},{cy + sh + bh2 // 2 + 2})\\fscx150\\fscy150\\t(0,130,\\fscx100\\fscy100)}}{val}")

    # --- slams de impacto ---
    for txt, a, b in SLAMS:
        ev(6, a, b, "Slam", f"{{\\pos({W//2},1010)\\frz-3\\fscx135\\fscy135\\t(0,120,\\fscx100\\fscy100)}}{txt}")

    # --- legendas: caixa preta; vira amarela com texto preto na palavra-chave ---
    chunks = chunk(words, cap_font, maxw=820)
    for ci, ch_ in enumerate(chunks):
        end = ch_[-1][2] + 0.25
        if ci + 1 < len(chunks): end = min(end, chunks[ci + 1][0][1])
        for wi, (w, s, e) in enumerate(ch_):
            nxt = ch_[wi + 1][1] if wi + 1 < len(ch_) else end
            nxt = max(nxt, s + 0.08)
            kw = w in KEYWORDS
            start = min(s, ch_[0][1]) if wi == 0 else s
            if kw:
                txt = " ".join(
                    (f"{{\\fscx122\\fscy122\\t(0,110,\\fscx100\\fscy100)}}{x[0].upper()}{{\\fscx100\\fscy100}}" if j == wi else x[0].upper())
                    for j, x in enumerate(ch_))
                ev(3, start, nxt, "Cap", f"{{\\3c{YEL}}}{txt}")
            else:
                ev(3, start, nxt, "Cap", " ".join(x[0].upper() for x in ch_))
    return "\n".join(L) + "\n"


def filter_graph(cuts, total, ass):
    z = zoom_expr(cuts, total)
    flash = "+".join(f"gte(t,{c:.3f})*lt(t,{c+0.067:.3f})" for c in cuts)
    L = []
    for i, (s, e) in enumerate(SEGMENTS):
        L.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
        L.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d={FADE},afade=t=out:st={e-s-FADE}:d={FADE}[a{i}]")
    n = len(SEGMENTS)
    L.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    L.append(
        f"[vc]fps=30,format=yuv420p,hqdn3d=1.6:1.2:3:3,"
        f"scale=w='trunc(1080*({z})/2)*2':h='trunc(1920*({z})/2)*2':eval=frame:flags=bicubic,"
        f"crop=1080:1920:'(in_w-1080)*0.88+({shake_expr(14)})':'0+({shake_expr(10)})',"
        "eq=contrast=1.16:saturation=0.70:gamma=1.04:brightness=0.03,"
        "curves=all='0/0.02 0.2/0.17 0.5/0.52 0.85/0.93 1/1',"
        "colorbalance=rs=-0.02:bs=0.05:rh=0.03:bh=-0.03,"
        "unsharp=5:5:1.0:3:3:0.0,vignette=angle=PI/3.2,noise=alls=8:allf=t+u,"
        f"eq=brightness='0.38*({flash})':eval=frame,"
        f"ass={ass}:fontsdir={FONTS}[v]")
    L.append(
        "[ac]pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,highpass=f=85,afftdn=nr=14:nf=-38:tn=1,"
        "equalizer=f=230:t=q:w=1:g=-2.5,equalizer=f=120:t=q:w=0.8:g=1.5,equalizer=f=3200:t=q:w=1:g=3,"
        "equalizer=f=8000:t=h:w=0.7:g=2,deesser=i=0.25:m=0.5:f=0.5,"
        "acompressor=threshold=0.1:ratio=3.2:attack=6:release=90:makeup=3[voz]")
    L.append("[1:a]aformat=sample_rates=44100:channel_layouts=stereo[fx]")
    L.append("[voz]aformat=sample_rates=44100:channel_layouts=stereo[vz];"
             "[vz][fx]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.84:level=0[a]")
    return ";\n".join(L)


def main(src, dst):
    raw = json.load(open(os.path.join(HERE, "leve_palavras.json")))
    st, total = starts()
    cuts = [round(x, 3) for x in st[1:]]
    work = tempfile.mkdtemp(prefix="brutal_")
    ass = os.path.join(work, "brutal.ass")
    open(ass, "w").write(build_ass(fix_words(raw), total))
    sfx = os.path.join(work, "sfx.wav")
    brutal_sfx.build(total, cuts, IMPACTS, sfx)
    script = os.path.join(work, "graph.txt")
    open(script, "w").write(filter_graph(cuts, total, ass))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", sfx, "-filter_complex_script", script,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst], check=True)
    print("ok", dst, "work:", work)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
