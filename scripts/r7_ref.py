"""R7 no estilo do print de referência: caixas retas, sem sombra, fonte geométrica média (Poppins).
Mesma paleta (preto, branco, lima, roxo), mesmos tempos e mesmo agrupamento do r7c.

Uso: python3 -I r7_ref.py video.mp4 face.npz saida_dir
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import r7_edit as R7
from r7_edit import W, H, EMO, FINGER, emoji_img, place, clamp, ease_out_cubic, render
from r7_tarjas import BLACK, WHITE, LIME, PURPLE, T, E, bar, rows

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_f = {}
def pf(size, w=500):
    k = (int(size), w)
    if k not in _f: _f[k] = ImageFont.truetype(f"{FD}/poppins-{w}.woff", int(size))
    return _f[k]

def box(runs, size, bg, fg, padx=28, radius=8, outline=None, weight=500, hmul=1.4):
    ws = [emoji_img(t, size).width if e else pf(size, weight).getlength(t) for t, e in runs]
    bw = int(sum(ws) + padx * 2); bh = int(size * hmul); pad = 10
    im = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + bw, pad + bh), radius, fill=bg + (255,),
                        outline=(outline + (255,)) if outline else None, width=3 if outline else 0)
    x = pad + padx; cy = pad + bh / 2
    for (t, e), w in zip(runs, ws):
        if e: em = emoji_img(t, size); im.alpha_composite(em, (int(x), int(cy - em.height / 2)))
        else: d.text((x, cy + 0.70 * size / 2), t, font=pf(size, weight), fill=fg + (255,), anchor="ls")
        x += w
    return im, bh

def make_d():
    size = 80; gap = 6; legend_size = 58
    sc = rows()
    p1 = [box(r, size, bg, fg) for r, bg, fg in sc[0]]
    p2 = [box(r, size, bg, fg) for r, bg, fg in sc[1]]
    leg, leg_h = box(sc[2][0][0], legend_size, BLACK, LIME, outline=LIME, weight=600, hmul=1.5)
    leg_bar = bar(leg.width - 20, 10)
    st = {}
    def tops(ctx):
        if not st:
            m = R7.CHIN_MARGIN + 14
            st["t1"] = float(ctx.chin[:90].max()) + m; st["t2"] = float(ctx.chin[90:].max()) + m
        return st["t1"], st["t2"]
    def stack(ov, pills, y, lt, out):
        for n, (im, h) in enumerate(pills):
            u = (lt - n * 0.09) / 0.22
            if u > 0:
                e = ease_out_cubic(u)
                place(ov, im, W / 2, y + h / 2 + 10 + (1 - e) * 40, 0.94 + 0.06 * e, clamp(u * 3) * out)
            y += h + gap
        return y
    def f(i, t, frame, ctx):
        t1, t2 = tops(ctx); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if t < 3.0: stack(ov, p1, t1, t, clamp((3.0 - t) / 0.1))
        else:
            y = stack(ov, p2, t2, t - 3.0, 1.0)
            u = (t - 5.0) / 0.25
            if u > 0:
                e = ease_out_cubic(u)
                place(ov, leg, W / 2, y + 16 + leg_h / 2 + 10 + (1 - e) * 40, 0.94 + 0.06 * e, clamp(u * 3))
                place(ov, leg_bar, W / 2, y + 16 + leg_h + 22, 1.0, clamp((t - 5.2) / 0.2))
        return ov, None
    return f

if __name__ == "__main__":
    video, face, outdir = sys.argv[1:4]
    os.makedirs(outdir, exist_ok=True)
    if "pb" in sys.argv[4:]:
        render("r7e_estilo_referencia_pb", make_d, video, face, outdir, gray=True)
    else:
        render("r7d_estilo_referencia", make_d, video, face, outdir)
