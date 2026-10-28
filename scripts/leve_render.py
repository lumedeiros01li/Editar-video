"""Edicao leve: cortes + legenda + titulo no topo + cards de idade/valor.

uso: python3 leve_render.py video_original.mp4 saida.mp4
"""
import json, subprocess, sys, os
from PIL import ImageFont
from leve_cortes import SEGMENTS, FADE, starts

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/usr/share/fonts/opentype/inter"
W, H = 1080, 1920
YELLOW = "&H0000D7FF&"   # BGR
GREEN = "&H0070E04A&"
WHITE = "&H00FFFFFF&"
BLACK = "&H00000000&"
NAVY = "&H00301C12&"

CARDS = [  # idade, valor, aparece idade, aparece valor (s, linha do tempo final)
    ("25 anos", "R$ 3.150", 6.95, 9.25),
    ("35 anos", "R$ 5.750", 10.68, 12.30),
    ("45 anos", "R$ 12.300", 14.78, 17.28),
]


def ts(t):
    h, r = divmod(max(t, 0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def fix_words(raw):
    """Corrige o que o Whisper erra: numeros colapsados e 'nos' no lugar de 'aos'."""
    out, i = [], 0
    while i < len(raw):
        w, s, e = raw[i]
        if w == "R":
            j = i
            while j + 1 < len(raw) and not raw[j][0].startswith(",00"):
                j += 1
            s0, e0 = s, raw[j][2]
            nums = "".join(x[0] for x in raw[i:j + 1])
            if "12" in nums:
                d = (e0 - s0) / 3
                out += [("12", s0, s0 + d), ("mil", s0 + d, s0 + 2 * d), ("reais", s0 + 2 * d, e0)]
            else:
                val = "R$ " + ("3.150," if "3" in nums else "5.750")
                out.append((val, s0, e0))
            i = j + 1
            continue
        out.append(("aos" if w == "nos" else w, s, e))
        i += 1
    return out


def chunk(words, font, maxw=860):
    """Quebra em pontuacao e divide cada trecho em blocos equilibrados de ate 3 palavras."""
    clauses, cur = [], []
    for w in words:
        cur.append(w)
        if w[0][-1] in ",.?!":
            clauses.append(cur); cur = []
    if cur: clauses.append(cur)
    chunks = []
    for cl in clauses:
        n = -(-len(cl) // 3)
        while True:
            base, rem = divmod(len(cl), n)
            sizes = [base + 1] * rem + [base] * (n - rem)
            parts, i = [], 0
            for z in sizes:
                parts.append(cl[i:i + z]); i += z
            if n >= len(cl) or all(font.getlength(" ".join(x[0] for x in p).upper()) <= maxw for p in parts):
                break
            n += 1
        chunks += parts
    return chunks


def rrect(w, h, r):
    return (f"m {r} 0 l {w-r} 0 b {w} 0 {w} 0 {w} {r} l {w} {h-r} b {w} {h} {w} {h} {w-r} {h} "
            f"l {r} {h} b 0 {h} 0 {h} 0 {h-r} l 0 {r} b 0 0 0 0 {r} 0")


def build_ass(words, total):
    cap_font = ImageFont.truetype(f"{FONTS}/Inter-ExtraBold.otf", 72)
    L = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,Inter ExtraBold,72,{WHITE},{WHITE},{BLACK},&H80000000&,0,0,0,0,100,100,0,0,1,7,3,2,40,40,440,1
Style: Top,Inter ExtraBold,50,{WHITE},{WHITE},{BLACK},&H80000000&,0,0,0,0,100,100,1,0,1,4,2,8,40,40,0,1
Style: Hook,Inter Black,76,{BLACK},{BLACK},{BLACK},&H00000000&,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Box,Inter,20,{WHITE},{WHITE},{YELLOW},&H00000000&,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Age,Inter ExtraBold,54,{WHITE},{WHITE},{BLACK},&H00000000&,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Val,Inter Black,50,{GREEN},{GREEN},{BLACK},&H00000000&,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"""]
    ev = lambda l, a, b, st, txt: L.append(f"Dialogue: {l},{ts(a)},{ts(b)},{st},,0,0,0,,{txt}")

    # titulo (gancho) acima da cabeca, fica o video todo
    slide = lambda x, y: f"\\move({x},{y-36},{x},{y},0,320)\\fad(280,0)"
    ev(1, 0, total, "Top", f"{{{slide(W//2, 62)}}}PARA SE APOSENTAR AOS 60 ANOS")
    bw, bh = 860, 112
    bx, by = (W - bw) // 2, 138
    ev(1, 0, total, "Box", f"{{\\an7\\1c{YELLOW}\\3c{BLACK}\\bord4\\shad0{slide(bx, by)}\\p1}}{rrect(bw, bh, 28)}")
    ev(2, 0, total, "Hook", f"{{{slide(W//2, by + bh//2)}}}R$ 10.000 DE RENDA")

    # cards de idade -> valor, na lateral direita (parede vazia)
    cw, ch, gap, cx, cy0 = 290, 134, 18, 765, 322
    for k, (age, val, t_age, t_val) in enumerate(CARDS):
        cy = cy0 + k * (ch + gap)
        mv = lambda x, y: f"\\move({x+70},{y},{x},{y},0,260)\\fad(200,0)"
        ev(1, t_age, total, "Box", f"{{\\an7\\1c{NAVY}\\1a&H30&\\3c{YELLOW}\\bord3\\shad0{mv(cx, cy)}\\p1}}{rrect(cw, ch, 24)}")
        ev(2, t_age, total, "Age", f"{{{mv(cx + 28, cy + 10)}}}{age}")
        ev(2, t_val, total, "Val", f"{{\\pos({cx+28},{cy+72})\\fad(180,0)\\fscx88\\fscy88\\t(0,200,\\fscx100\\fscy100)}}{val}")

    # legendas: 3 palavras por bloco, palavra falada em amarelo
    chunks = chunk(words, cap_font)
    for ci, ch_ in enumerate(chunks):
        end = ch_[-1][2] + 0.25
        if ci + 1 < len(chunks): end = min(end, chunks[ci + 1][0][1])
        for wi, (w, s, e) in enumerate(ch_):
            nxt = ch_[wi + 1][1] if wi + 1 < len(ch_) else end
            nxt = max(nxt, s + 0.05)
            txt = " ".join(
                (f"{{\\1c{YELLOW}}}{x[0].upper()}{{\\1c{WHITE}}}" if j == wi else x[0].upper())
                for j, x in enumerate(ch_))
            ev(3, s if wi else min(s, ch_[0][1]), nxt, "Cap", txt)
    return "\n".join(L) + "\n"


def main(src, dst):
    raw = json.load(open(os.path.join(HERE, "leve_palavras.json")))
    _, total = starts()
    ass = os.path.join(os.path.dirname(os.path.abspath(dst)), "leve.ass")
    open(ass, "w").write(build_ass(fix_words(raw), total))
    v, a, vl, al = [], [], [], []
    for i, (s, e) in enumerate(SEGMENTS):
        vl.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
        vl.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d={FADE},afade=t=out:st={e-s-FADE}:d={FADE}[a{i}]")
        v.append(f"[v{i}][a{i}]")
    fc = ";".join(vl) + ";" + "".join(v) + f"concat=n={len(SEGMENTS)}:v=1:a=1[vc][ac];"
    fc += f"[vc]format=yuv420p,ass={ass}:fontsdir={FONTS}[v];[ac]loudnorm=I=-16:TP=-1.5:LRA=11[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", dst], check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
