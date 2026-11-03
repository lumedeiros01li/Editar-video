"""R7 tarjas, paleta nova (preto, branco, lima, roxo) e texto centralizado.

Uso: python3 -I r7_tarjas.py video.mp4 face.npz saida_dir [a b]
  a = uma tela por vez (padrão do v3, centralizado)
  b = textos se acumulam e nenhum some; chamada da legenda fica embaixo
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
import r7_edit as R7
from r7_edit import (W, H, SCREENS, EMO, FINGER, font, emoji_img, run_w, place, clamp, ease_out_back,
                     ease_out_cubic, screen_at, render)
import math

BLACK, WHITE = (0, 0, 0), (255, 255, 255)
LIME, PURPLE = (234, 245, 107), (157, 116, 255)
CAP = 0.727  # altura das maiúsculas da Inter, em em (centragem óptica)

def pill(runs, size, bg, fg, padx=40, pady=12, radius=26, outline=None):
    """Tarja com texto centrado óptica e horizontalmente. runs=[(texto, emoji?)]."""
    widths = [run_w(t, size, e) for t, e in runs]
    tw = sum(widths); bh = int(size * 1.2) + pady * 2; bw = int(tw + padx * 2); pad = 30
    im = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 8, pad + bw, pad + bh + 8), radius, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + bw, pad + bh), radius, fill=bg + (255,),
                        outline=(outline + (255,)) if outline else None, width=4 if outline else 0)
    x = pad + padx; cy = pad + bh / 2
    for (t, e), w in zip(runs, widths):
        if e:
            em = emoji_img(t, size); im.alpha_composite(em, (int(x), int(cy - em.height / 2)))
        else:
            d.text((x, cy + CAP * size / 2), t, font=font(size), fill=fg + (255,), anchor="ls")
        x += w
    return im, bh

def T(t): return (t, False)
def E(t): return (t, True)

# (runs, fundo, texto)
def rows(size_unused=None):
    s1 = [([T("Médica deixa")], WHITE, BLACK), ([T("R$ 300 mil")], PURPLE, WHITE),
          ([T("na conta")], WHITE, BLACK), ([T("corrente "), E(EMO)], WHITE, BLACK)]
    s2 = [([T("A inflação")], LIME, BLACK), ([T("de 4,5% ao ano")], LIME, BLACK),
          ([T("pede R$ 13.500")], PURPLE, WHITE), ([T("só para empatar")], LIME, BLACK)]
    s3 = [([T("LEIA A LEGENDA "), E(FINGER)], BLACK, LIME)]
    return [s1, s2, s3]

def bar(width, h=12):
    im = Image.new("RGBA", (width + 60, h + 60), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((30, 30, 30 + width, 30 + h), h // 2, fill=PURPLE + (255,))
    return im

def make_a():
    """Uma tela por vez, em cascata, centralizado no meio da área livre abaixo do queixo."""
    size = 94; cy_zone = 1270
    data = []
    for scr in rows():
        ls = []
        for runs, bg, fg in scr:
            outline = LIME if bg == BLACK else None
            ls.append(pill(runs, size, bg, fg, outline=outline))
        data.append(ls)
    legend_bar = bar(data[2][0][0].width - 60)
    def f(i, t, frame, ctx):
        k, lt, ld = screen_at(t); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ls = data[k]; gap = 6
        total = sum(h for _, h in ls) + gap * (len(ls) - 1)
        if k == 2: total += 26
        y = cy_zone - total / 2
        out = clamp((ld - lt) / 0.12) if k < 2 else 1.0
        for n, (im, h) in enumerate(ls):
            u = (lt - n * 0.08) / 0.28
            if u > 0:
                place(ov, im, W / 2, y + h / 2 + (1 - ease_out_back(u)) * 90, 1.0, clamp(u * 3) * out)
            y += h + gap
        if k == 2 and lt > 0.2:
            place(ov, legend_bar, W / 2, y + 12, 1.0, clamp((lt - 0.2) / 0.2))
        return ov, None
    return f

def make_b():
    """Textos se acumulam sem sumir. Sem sobrepor o rosto. Legenda fixa na parte inferior."""
    size = 64; top = 885; gap = 4
    sc = rows()
    sc[0] = [sc[0][0], sc[0][1], ([T("na conta corrente "), E(EMO)], WHITE, BLACK)]
    pills = [[pill(r, size, bg, fg, pady=8) for r, bg, fg in scr] for scr in sc[:2]]
    legend = pill(sc[2][0][0], 76, BLACK, LIME, pady=10, outline=LIME)
    bar_img = bar(legend[0].width - 60, 14)
    # posição (centro y) de cada tarja, empilhadas em ordem
    pos, y = [], top
    for scr in pills:
        for im, h in scr: pos.append(y + h / 2); y += h + gap
    flat = [(im, h) for scr in pills for im, h in scr]
    starts = [0.05 + n * 0.18 for n in range(len(pills[0]))] + [3.05 + n * 0.18 for n in range(len(pills[1]))]
    LEG_Y = 1640
    def f(i, t, frame, ctx):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for (im, h), cy, t0 in zip(flat, pos, starts):
            u = (t - t0) / 0.28
            if u > 0:
                place(ov, im, W / 2, cy + (1 - ease_out_back(u)) * 70, 1.0, clamp(u * 3))
        u = (t - 5.0) / 0.35
        if u > 0:
            bob = math.sin((t - 5.0) * 8) * 6 if u > 1 else 0
            place(ov, legend[0], W / 2, LEG_Y + (1 - ease_out_back(u)) * 140 + bob, 1.0 + 0.04 * math.sin((t - 5.0) * 6) * (u > 1), clamp(u * 3))
            place(ov, bar_img, W / 2, LEG_Y + legend[1] / 2 + 24 + bob, 1.0, clamp((t - 5.3) / 0.2))
        return ov, None
    return f

V = {"r7b_a_centralizado": make_a, "r7b_b_acumulado": make_b}

if __name__ == "__main__":
    video, face, outdir = sys.argv[1:4]
    os.makedirs(outdir, exist_ok=True)
    want = sys.argv[4:] or ["a", "b"]
    for n, fac in V.items():
        if any(n.startswith("r7b_" + w) for w in want): render(n, fac, video, face, outdir)
