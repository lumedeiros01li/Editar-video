"""Edicao simples: cortes limpos, zoom leve so nos cortes, grade discreta,
voz tratada, legenda e cards no estilo cartao claro / borda preta / sombra roxa.

uso: python3 simples_render.py video_original.mp4 saida.mp4
"""
import json, os, subprocess, sys, tempfile
from PIL import ImageFont
from leve_cortes import SEGMENTS, FADE, starts
from leve_render import fix_words, chunk, ts

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/usr/share/fonts/opentype/inter"
W, H = 1080, 1920
SHIFT = 210                                   # video desce; topo ganha fundo desfocado para o cartao
BLK, CARD, PURPLE, LIME = "&H00000000&", "&H00EFEFEF&", "&H00FF6B9B&", "&H006BFFE4&"
WHT, GREY, GREY2 = "&H00FFFFFF&", "&H008A8A8A&", "&H00DCDCDC&"
ZOOMS = [1.00, 1.07]                          # alterna a cada corte real
CARDS = [("25 ANOS", "R$ 3.150", 6.95, 9.25), ("35 ANOS", "R$ 5.750", 10.68, 12.30), ("45 ANOS", "R$ 12.300", 14.78, 17.28)]
KEYWORDS = {"60", "10", "mil", "25", "35", "45", "12", "reais", "dobra", "R$ 3.150,", "R$ 5.750"}


def rect(L, a, b, x, y, w, h, color, layer, fade=""):
    L.append(f"Dialogue: {layer},{ts(a)},{ts(b)},Box,,0,0,0,,{{\\an7\\pos({x},{y}){fade}\\p1\\1c{color}\\bord0\\shad0}}m 0 0 l {w} 0 l {w} {h} l 0 {h}")


def build_ass(words, total):
    cap_font = ImageFont.truetype(f"{FONTS}/Inter-Black.otf", 62)
    big = ImageFont.truetype(f"{FONTS}/Inter-Black.otf", 120)
    blk = ImageFont.truetype(f"{FONTS}/Inter-Black.otf", 76)
    mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 38)
    mono2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 35)
    L = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Box,Inter,20,{WHT},{WHT},{BLK},{BLK},0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Mono,DejaVu Sans Mono,38,{BLK},{BLK},{BLK},{BLK},-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Big,Inter Black,120,{BLK},{BLK},{BLK},{BLK},0,0,0,0,100,100,-2,0,1,0,0,5,0,0,0,1
Style: Blk,Inter Black,76,{WHT},{WHT},{BLK},{BLK},0,0,0,0,100,100,-1,0,1,0,0,5,0,0,0,1
Style: Age,DejaVu Sans Mono,28,{BLK},{BLK},{BLK},{BLK},-1,0,0,0,100,100,0,0,1,0,0,4,0,0,0,1
Style: Val,Inter Black,38,{WHT},{WHT},{BLK},{BLK},0,0,0,0,100,100,-1,0,1,0,0,5,0,0,0,1
Style: Cap,Inter Black,62,{BLK},{BLK},{CARD},{BLK},0,0,0,0,100,100,-1,0,3,16,0,2,40,40,380,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"""]
    ev = lambda l, a, b, st, txt: L.append(f"Dialogue: {l},{ts(a)},{ts(b)},{st},,0,0,0,,{txt}")
    fade = "\\fad(220,0)"

    # --- cartao do titulo ---
    cx, cy, cw, ch = 44, 40, 992, 392
    rect(L, 0, total, cx + 18, cy + 16, cw, ch, PURPLE, 1, fade)
    rect(L, 0, total, cx - 6, cy - 6, cw + 12, ch + 12, BLK, 2, fade)
    rect(L, 0, total, cx, cy, cw, ch, CARD, 3, fade)
    tag = "[ APOSENTADORIA AOS 60 ]"
    tw = int(mono.getlength(tag)) + 56
    rect(L, 0, total, W // 2 - tw // 2 - 4, 62 - 4, tw + 8, 60, BLK, 4, fade)
    rect(L, 0, total, W // 2 - tw // 2, 62, tw, 52, CARD, 5, fade)
    ev(6, 0, total, "Mono", f"{{\\pos({W//2},89){fade}}}{tag}")
    ev(6, 0, total, "Big", f"{{\\pos({W//2},186){fade}}}R$ 10.000")
    bw = int(blk.getlength("DE RENDA")) + 56
    rect(L, 0, total, W // 2 - bw // 2, 250, bw, 90, PURPLE, 5, fade)
    ev(6, 0, total, "Blk", f"{{\\pos({W//2},297){fade}}}DE RENDA")
    pill = "↑ quanto guardar por mês"
    pw = int(mono2.getlength(pill)) + 48
    rect(L, 0, total, W // 2 - pw // 2 - 4, 352 - 4, pw + 8, 58, BLK, 4, fade)
    rect(L, 0, total, W // 2 - pw // 2, 352, pw, 50, LIME, 5, fade)
    ev(6, 0, total, "Mono", f"{{\\pos({W//2},378){fade}\\fs35}}{pill}")

    # --- cards idade -> valor ---
    kx, kw, kh, gap, ky0 = 774, 262, 116, 26, 500
    for k, (age, val, ta, tv) in enumerate(CARDS):
        y = ky0 + k * (kh + gap)
        f = "\\fad(150,0)"
        rect(L, ta, total, kx + 10, y + 10, kw, kh, PURPLE, 1, f)
        rect(L, ta, total, kx - 5, y - 5, kw + 10, kh + 10, BLK, 2, f)
        rect(L, ta, total, kx, y, kw, kh, CARD, 3, f)
        ev(6, ta, total, "Age", f"{{\\pos({kx + 16},{y + 24}){f}}}{age}")
        rect(L, ta, tv, kx + 12, y + 50, kw - 24, 54, GREY2, 4, f)
        ev(6, ta, tv, "Mono", f"{{\\pos({kx + kw // 2},{y + 77})\\1c{GREY}\\fs28{f}}}R$ ----")
        rect(L, tv, total, kx + 12, y + 50, kw - 24, 54, PURPLE, 4)
        ev(6, tv, total, "Val", f"{{\\pos({kx + kw // 2},{y + 79})}}{val}")

    # --- legendas: caixa clara; roxa com texto branco na palavra-chave ---
    chunks = chunk(words, cap_font, maxw=820)
    for ci, ch_ in enumerate(chunks):
        end = ch_[-1][2] + 0.25
        if ci + 1 < len(chunks): end = min(end, chunks[ci + 1][0][1])
        for wi, (w, s, e) in enumerate(ch_):
            nxt = ch_[wi + 1][1] if wi + 1 < len(ch_) else end
            nxt = max(nxt, s + 0.08)
            start = min(s, ch_[0][1]) if wi == 0 else s
            txt = " ".join(x[0].upper() for x in ch_)
            if w in KEYWORDS:
                txt = f"{{\\1c{WHT}\\3c{PURPLE}}}{txt}"
            ev(3, start, nxt, "Cap", txt)
    return "\n".join(L) + "\n"


def zoom_expr(cuts, total):
    bounds = [0.0] + cuts + [total]
    return "+".join(f"gte(t,{a:.3f})*lt(t,{b:.3f})*{ZOOMS[i % len(ZOOMS)]}" for i, (a, b) in enumerate(zip(bounds, bounds[1:])))


def filter_graph(cuts, total, ass):
    L = []
    for i, (s, e) in enumerate(SEGMENTS):
        L.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
        L.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d={FADE},afade=t=out:st={e-s-FADE}:d={FADE}[a{i}]")
    n = len(SEGMENTS)
    L.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    z = zoom_expr(cuts, total)
    L.append(
        "[vc]fps=30,format=yuv420p,hqdn3d=1.2:1:2:2,"
        f"scale=w='trunc(1080*({z})/2)*2':h='trunc(1920*({z})/2)*2':eval=frame:flags=bicubic,"
        "crop=1080:1920:'(in_w-1080)*0.6':0,split[m1][m2]")
    L.append(f"[m1]crop=1080:{H - SHIFT}:0:0[body]")
    L.append(f"[m2]crop=1080:{SHIFT}:0:0,vflip,gblur=sigma=30[top]")
    L.append(f"[top][body]vstack,eq=contrast=1.05:saturation=1.05:gamma=1.02,ass={ass}:fontsdir={FONTS}[v]")
    L.append(
        "[ac]pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,highpass=f=85,afftdn=nr=14:nf=-38:tn=1,"
        "equalizer=f=230:t=q:w=1:g=-2.5,equalizer=f=120:t=q:w=0.8:g=1.5,equalizer=f=3200:t=q:w=1:g=3,"
        "equalizer=f=8000:t=h:w=0.7:g=2,deesser=i=0.25:m=0.5:f=0.5,"
        "acompressor=threshold=0.1:ratio=3.2:attack=6:release=90:makeup=3,"
        "loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.84:level=0[a]")
    return ";\n".join(L)


def main(src, dst):
    raw = json.load(open(os.path.join(HERE, "leve_palavras.json")))
    st, total = starts()
    cuts = [round(x, 3) for x in st[1:]]
    work = tempfile.mkdtemp(prefix="simples_")
    ass = os.path.join(work, "simples.ass")
    open(ass, "w").write(build_ass(fix_words(raw), total))
    script = os.path.join(work, "graph.txt")
    open(script, "w").write(filter_graph(cuts, total, ass))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex_script", script,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "19", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst], check=True)
    print("ok", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
