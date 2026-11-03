"""Testes de edição no modelo R7 (texto em camadas sobre vídeo vertical 1080x1920).

Uso: python3 -I r7_edit.py video.mp4 face.npz saida_dir [v1 v2 ...]

Regra principal: nada de texto/elemento na frente do rosto. O rosto vem de r7_face.py,
e cada frame é checado: o topo do overlay precisa ficar abaixo do queixo + margem.
"""
import sys, os, subprocess, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
YEL, RED = (255, 214, 0), (255, 38, 38)
CY = 1180            # centro vertical do bloco de texto
CHIN_MARGIN = 70     # folga abaixo do queixo
SCREENS = [(0.0, 3.0), (3.0, 5.0), (5.0, 7.2334)]
EMO = "\U0001F3E6"   # banco
FINGER = "\U0001F447"  # dedo apontando pra baixo

_fonts = {}
def font(size):
    size = int(size)
    if size not in _fonts: _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]

_emo_cache = {}
def emoji_img(ch, size):
    k = (ch, int(size))
    if k not in _emo_cache:
        f = ImageFont.truetype(EMOJI, 109)
        im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), ch, font=f, embedded_color=True)
        s = size * 1.05 / 128
        _emo_cache[k] = im.resize((max(1, int(136 * s)), max(1, int(128 * s))), Image.LANCZOS)
    return _emo_cache[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_out_back(x, s=1.70158): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_in_out(x): x = clamp(x); return 3 * x * x - 2 * x ** 3

def screen_at(t):
    for k, (a, b) in enumerate(SCREENS):
        if t < b or k == len(SCREENS) - 1: return k, t - a, b - a

# ---------------------------------------------------------------- layout de texto
def run_w(text, size, emoji):
    return emoji_img(text, size).width if emoji else font(size).getlength(text)

def layout(lines, size, gap=1.16, align="center", left=0):
    """lines: [ {runs:[(texto,cor,emoji?)], size?} ] -> itens posicionados + dimensões do bloco."""
    items, y, maxw = [], 0, 0
    for li, ln in enumerate(lines):
        sz = ln.get("size", size)
        widths = [run_w(t, sz, e) for t, c, e in ln["runs"]]
        tw = sum(widths); maxw = max(maxw, tw)
        x = (W - tw) / 2 if align == "center" else left
        for (t, c, e), w in zip(ln["runs"], widths):
            items.append(dict(text=t, color=c, emoji=e, x=x, y=y, w=w, size=sz, line=li))
            x += w
        y += sz * gap
    return items, maxw, y

def split_words(items):
    """quebra runs em palavras, mantendo posição, para animação palavra por palavra."""
    out = []
    for it in items:
        if it["emoji"]: out.append(dict(it, word=True)); continue
        x = it["x"]; f = font(it["size"])
        parts = it["text"].split(" ")
        for k, p in enumerate(parts):
            if p:
                out.append(dict(it, text=p, x=x, w=f.getlength(p), word=True))
            x += f.getlength(p + (" " if k < len(parts) - 1 else ""))
    return out

def draw_items(items, stroke=8, shadow=True, pad=60, color_override=None):
    """Renderiza itens numa camada RGBA (coordenadas do bloco + pad)."""
    bw = int(max(i["x"] + i["w"] for i in items) + pad * 2)
    bh = int(max(i["y"] + i["size"] * 1.3 for i in items) + pad * 2)
    txt = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    for it in items:
        px, py = it["x"] + pad, it["y"] + pad
        if it["emoji"]:
            e = emoji_img(it["text"], it["size"])
            txt.alpha_composite(e, (int(px), int(py + it["size"] * 0.08)))
        else:
            c = color_override or it["color"]
            d.text((px, py), it["text"], font=font(it["size"]), fill=c + (255,),
                   stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    if not shadow: return txt
    a = txt.getchannel("A")
    sh = Image.new("RGBA", txt.size, (0, 0, 0, 0))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.65)))
    out = Image.new("RGBA", txt.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 10))
    out.alpha_composite(txt)
    return out

def block_layer(lines, size, **kw):
    items, bw, bh = layout(lines, size)
    return draw_items(items, **kw), items, bh

def paste_rgba(ov, layer, x, y):
    x, y = int(x), int(y)
    sx, sy = max(0, -x), max(0, -y)
    if sx >= layer.width or sy >= layer.height: return
    if sx or sy: layer = layer.crop((sx, sy, layer.width, layer.height))
    dx, dy = x + sx, y + sy
    w, h = min(layer.width, W - dx), min(layer.height, H - dy)
    if w <= 0 or h <= 0: return
    if (w, h) != layer.size: layer = layer.crop((0, 0, w, h))
    ov.alpha_composite(layer, (dx, dy))

def place(ov, layer, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.003 or scale <= 0.01: return
    if abs(scale - 1) > 0.003:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BILINEAR)
    if alpha < 0.995:
        a = layer.getchannel("A").point(lambda v: int(v * alpha)); layer = layer.copy(); layer.putalpha(a)
    paste_rgba(ov, layer, cx - layer.width / 2, cy - layer.height / 2)

def fade(lt, ld, fin=0.12, fout=0.12, last=False):
    a = clamp(lt / fin)
    if not last: a *= clamp((ld - lt) / fout)
    return a

# ---------------------------------------------------------------- textos
def R(t, c=WHITE, e=False): return (t, c, e)
def copy(c1, c2, c3):
    """Três telas do roteiro. c1/c2/c3 = cores base; destaque amarelo na tela 1, branco/amarelo na 2."""
    return [
        [dict(runs=[R("Médica deixa", c1)]), dict(runs=[R("R$ 300 mil", YEL)]),
         dict(runs=[R("na conta", c1)]), dict(runs=[R("corrente ", c1), R(EMO, c1, True)])],
        [dict(runs=[R("A inflação", c2)]), dict(runs=[R("de 4,5% ao ano", c2)]),
         dict(runs=[R("pede ", c2), R("R$ 13.500", WHITE if c2 == RED else YEL)]), dict(runs=[R("só para empatar", c2)])],
        [dict(runs=[R("Leia a legenda", c3)]), dict(runs=[R(FINGER, c3, True)], size=120)],
    ]
SIZE = 108

# ---------------------------------------------------------------- contexto (rosto)
class Ctx:
    def __init__(self, face_npz, n):
        d = np.load(face_npz); b = d["boxes"].astype(np.float64)
        ok = (b[:, 1] < 700) & (b[:, 3] > 380) & (b[:, 3] < 540)
        idx = np.arange(len(b))
        for k in range(4): b[:, k] = np.interp(idx, idx[ok], b[ok, k])
        chin = b[:, 1] + b[:, 3]
        self.chin = np.array([chin[max(0, i - 5):i + 6].max() for i in range(len(b))])  # máx. numa janela
        self.boxes = b; self.n = n; self.violations = []; self.min_clear = 1e9
    def check(self, name, i, bbox, chin_y):
        if bbox is None: return
        clear = bbox[1] - (chin_y + CHIN_MARGIN)
        self.min_clear = min(self.min_clear, clear + CHIN_MARGIN)
        if clear < 0: self.violations.append((name, i, int(bbox[1]), int(chin_y)))

def ov_bbox(ov):
    return ov.getchannel("A").point(lambda v: 255 if v > 10 else 0).getbbox()

# ---------------------------------------------------------------- variantes
def make_v1():
    """R7 clássico: branco + amarelo, contorno preto grosso, pop-in com overshoot."""
    scr = copy(WHITE, RED, WHITE)
    layers = [block_layer(s, SIZE, stroke=11)[0] for s in scr]
    def f(i, t, frame, ctx):
        k, lt, ld = screen_at(t); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        place(ov, layers[k], W / 2, CY, 0.6 + 0.4 * ease_out_back(lt / 0.30), fade(lt, ld, last=k == 2))
        return ov, None
    return f

def make_v2():
    """Palavra por palavra: cada palavra salta em sequência; a última a entrar pisca em amarelo."""
    scr = copy(WHITE, RED, WHITE)
    data = []
    for s in scr:
        items, bw, bh = layout(s, SIZE); words = split_words(items)
        ws = []
        for w in words:
            one = [dict(w, x=0, y=0)]
            base = draw_items(one, stroke=11)
            hi = draw_items(one, stroke=11, color_override=YEL) if not w["emoji"] else base
            ws.append((w, base, hi))
        data.append((ws, bh))
    def f(i, t, frame, ctx):
        k, lt, ld = screen_at(t); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ws, bh = data[k]; top = CY - bh / 2
        out = clamp((ld - lt) / 0.12) if k < 2 else 1.0
        for n, (w, base, hi) in enumerate(ws):
            t0 = 0.05 + n * 0.14
            if lt < t0: continue
            u = (lt - t0) / 0.22
            newest = (n == len(ws) - 1 or lt < 0.05 + (n + 1) * 0.14) and lt - t0 < 0.3 and k != 1
            lay = hi if (newest and w["color"] == WHITE) else base
            cx = w["x"] + w["w"] / 2; cy = top + w["y"] + w["size"] * 0.65
            place(ov, lay, cx, cy, 0.4 + 0.6 * ease_out_back(u), clamp(u * 4) * out)
        return ov, None
    return f

def pill_layer(runs, size, bg, fg, padx=38, pady=10, radius=26, emoji_ok=True):
    widths = [run_w(t, size, e) for t, c, e in runs]
    tw = int(sum(widths)); bh = int(size * 1.22) + pady * 2
    pad = 30
    im = Image.new("RGBA", (tw + padx * 2 + pad * 2, bh + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 8, pad + tw + padx * 2, pad + bh + 8), radius, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + tw + padx * 2, pad + bh), radius, fill=bg + (255,))
    x = pad + padx
    for (t, c, e), w in zip(runs, widths):
        if e: im.alpha_composite(emoji_img(t, size), (int(x), int(pad + pady + size * 0.06)))
        else: d.text((x, pad + pady - size * 0.02), t, font=font(size), fill=fg + (255,))
        x += w
    return im, bh

def make_v3():
    """Marca-texto: cada linha numa tarja arredondada, entrando em cascata (sobe e aparece)."""
    size = 94
    rows = [
        [([R("Médica deixa")], WHITE, BLACK), ([R("R$ 300 mil")], YEL, BLACK),
         ([R("na conta")], WHITE, BLACK), ([R("corrente "), R(EMO, BLACK, True)], WHITE, BLACK)],
        [([R("A inflação")], RED, WHITE), ([R("de 4,5% ao ano")], RED, WHITE),
         ([R("pede "), R("R$ 13.500", RED)], WHITE, RED), ([R("só para empatar")], RED, WHITE)],
        [([R("Leia a legenda")], YEL, BLACK), ([R(FINGER, BLACK, True)], WHITE, BLACK)],
    ]
    data = []
    for scr in rows:
        ls = []
        for runs, bg, fg in scr:
            runs = [(t, fg if c in (WHITE, BLACK) else c, e) for t, c, e in runs]
            ls.append(pill_layer(runs, size, bg, fg))
        data.append(ls)
    def f(i, t, frame, ctx):
        k, lt, ld = screen_at(t); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ls = data[k]; gap = 6
        total = sum(h for _, h in ls) + gap * (len(ls) - 1); y = CY - total / 2
        out = clamp((ld - lt) / 0.12) if k < 2 else 1.0
        for n, (im, h) in enumerate(ls):
            u = (lt - n * 0.08) / 0.28
            if u > 0:
                dy = (1 - ease_out_back(u)) * 90
                place(ov, im, W / 2, y + h / 2 + 30 + dy, 1.0, clamp(u * 3) * out)
            y += h + gap
        return ov, None
    return f

def make_v4():
    """Cartão: painel com fundo desfocado e barra de destaque que desliza da esquerda."""
    cards = [
        dict(lines=[dict(runs=[R("Médica deixa")]), dict(runs=[R("R$ 300 mil", YEL)]),
                    dict(runs=[R("na conta corrente")])], emo=EMO, accent=YEL, tint=(8, 8, 12), a=0.62),
        dict(lines=[dict(runs=[R("A inflação de 4,5% ao ano")]), dict(runs=[R("pede "), R("R$ 13.500", YEL)]),
                    dict(runs=[R("só para empatar")])], emo=None, accent=WHITE, tint=(150, 8, 12), a=0.80),
        dict(lines=[dict(runs=[R("Leia a legenda")])], emo=FINGER, accent=YEL, tint=(8, 8, 12), a=0.62),
    ]
    size = 80; px, py = 64, 56
    data = []
    for c in cards:
        items, bw, bh = layout(c["lines"], size, gap=1.3, align="left", left=0)
        lay = draw_items(items, stroke=0, shadow=False, pad=0)
        ew = 150 if c["emo"] else 0
        cw = int(bw + px * 2 + ew + 22); ch = int(bh + py * 2 - 8)
        data.append((c, lay, cw, ch))
    def f(i, t, frame, ctx):
        k, lt, ld = screen_at(t); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        c, lay, cw, ch = data[k]
        slide = 1 - ease_out_cubic(lt / 0.40); cx0 = int((W - cw) / 2 - slide * 700)
        if k < 2: cx0 += int(ease_in_out((lt - (ld - 0.25)) / 0.25) * -900)
        cy0 = int(CY - ch / 2)
        x0, y0 = max(0, cx0), cy0
        x1 = min(W, cx0 + cw)
        if x1 > x0:
            crop = frame.crop((x0, y0, x1, y0 + ch)).filter(ImageFilter.GaussianBlur(22))
            tint = Image.new("RGB", crop.size, c["tint"])
            crop = Image.blend(crop, tint, c["a"])
            m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, cw - 1, ch - 1), 40, fill=255)
            m = m.crop((x0 - cx0, 0, x1 - cx0, ch))
            ov.paste(crop.convert("RGBA"), (x0, y0), m)
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle((0, 0, 16, ch - 1), 8, fill=c["accent"] + (255,))
        card.alpha_composite(lay, (px + 8, py - 12))
        if c["emo"]:
            bob = math.sin(lt * 9) * 12 if c["emo"] == FINGER else 0
            e = emoji_img(c["emo"], 110); card.alpha_composite(e, (cw - e.width - 36, int(ch / 2 - e.height / 2 + bob)))
        # recorta o cartão pelo retângulo arredondado e cola deslocado
        cm = Image.new("L", (cw, ch), 0); ImageDraw.Draw(cm).rounded_rectangle((0, 0, cw - 1, ch - 1), 40, fill=255)
        card.putalpha(Image.composite(card.getchannel("A"), Image.new("L", card.size, 0), cm))
        paste_rgba(ov, card, cx0, y0)
        return ov, None
    return f

def fmt_br(n): return f"{int(n):,}".replace(",", ".")

def make_v5():
    """Contador: número gigante sobe de zero até o valor, com tremida na tela vermelha."""
    def f(i, t, frame, ctx):
        k, lt, ld = screen_at(t); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if k == 0:
            n = 300 * ease_out_cubic((lt - 0.1) / 0.9)
            lines = [dict(runs=[R("Médica deixa")], size=84), dict(runs=[R(f"R$ {int(n)} mil", YEL)], size=165),
                     dict(runs=[R("na conta corrente ", WHITE), R(EMO, WHITE, True)], size=84)]
            fixed = layout([dict(runs=[R("R$ 300 mil")], size=165)], 150)
            shake = 0
        elif k == 1:
            n = 13500 * ease_out_cubic((lt - 0.1) / 1.1)
            lines = [dict(runs=[R("A inflação de 4,5% ao ano", RED)], size=64),
                     dict(runs=[R("pede", RED)], size=84), dict(runs=[R(f"R$ {fmt_br(n)}", RED)], size=185),
                     dict(runs=[R("só para empatar", RED)], size=84)]
            shake = math.sin(lt * 55) * 9 * clamp(1 - lt / 0.45)
        else:
            lines = [dict(runs=[R("Leia a legenda")], size=SIZE), dict(runs=[R(FINGER, WHITE, True)], size=130)]
            shake = 0
        items, bw, bh = layout(lines, SIZE)
        lay = draw_items(items, stroke=11)
        bob = math.sin(lt * 9) * 14 if k == 2 else 0
        place(ov, lay, W / 2 + shake, CY + bob, 0.7 + 0.3 * ease_out_back(lt / 0.3), fade(lt, ld, last=k == 2))
        return ov, None
    return f

def make_v6():
    """Zoom no vídeo (punch-in a cada tela) + texto digitado com cursor, tremida na tela vermelha."""
    scr = copy(WHITE, RED, WHITE)
    full = []
    for s in scr:
        items, bw, bh = layout(s, SIZE); full.append((items, bh))
    def zoom_at(t):
        k, lt, ld = screen_at(t)
        base = [1.0, 1.14, 1.04][k]
        drift = 0.05 * (lt / ld)
        z = base + drift
        if k == 1: z += 0.05 * (1 - ease_out_cubic(lt / 0.25))   # soco inicial
        shake = (math.sin(lt * 70) * 7 * clamp(1 - lt / 0.4), math.cos(lt * 63) * 7 * clamp(1 - lt / 0.4)) if k == 1 else (0, 0)
        return z, shake
    def f(i, t, frame, ctx):
        k, lt, ld = screen_at(t); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        items, bh = full[k]
        total = sum(1 if it["emoji"] else len(it["text"]) for it in items)
        n = int(clamp((lt - 0.08) / (min(1.0, ld - 0.5) - 0.08)) * total + 0.9999) if lt > 0.08 else 0
        shown, left, last = [], n, None
        for it in items:
            if left <= 0: break
            ln = 1 if it["emoji"] else len(it["text"])
            if ln <= left: shown.append(it); left -= ln; last = (it, it["w"])
            else:
                part = it["text"][:left]; last = (it, font(it["size"]).getlength(part))
                shown.append(dict(it, text=part, w=last[1])); left = 0
        top = CY - bh / 2
        if shown:
            lay = draw_items(shown, stroke=11)
            paste_rgba(ov, lay, -60, top - 60)   # itens já usam x absoluto; pad = 60
        if last and (n < total or int(lt * 4) % 2 == 0) and lt > 0.08:
            it, w = last
            cx = it["x"] + w + 14; cy0 = top + it["y"] + it["size"] * 0.12
            ImageDraw.Draw(ov).rounded_rectangle((cx, cy0, cx + 12, cy0 + it["size"] * 0.95), 5, fill=YEL + (255,), outline=BLACK + (255,), width=3)
        return ov, zoom_at(t)
    return f

VARIANTS = {
    "v1_classico": make_v1, "v2_palavra_a_palavra": make_v2, "v3_tarja_marca_texto": make_v3,
    "v4_cartao_vidro": make_v4, "v5_contador": make_v5, "v6_zoom_digitando": make_v6,
}

# ---------------------------------------------------------------- render
def read_frames(path):
    cap = cv2.VideoCapture(path)
    while True:
        ok, fr = cap.read()
        if not ok: break
        yield fr

def render(name, factory, video, face_npz, outdir):
    cap_n = int(cv2.VideoCapture(video).get(cv2.CAP_PROP_FRAME_COUNT))
    ctx = Ctx(face_npz, cap_n); f = factory()
    out = os.path.join(outdir, name + ".mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                          "-movflags", "+faststart", "-an", out], stdin=subprocess.PIPE)
    for i, fr in enumerate(read_frames(video)):
        t = i / FPS
        rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        ov, zoom = f(i, t, pil, ctx)
        chin = ctx.chin[min(i, len(ctx.chin) - 1)]
        if zoom:
            z, (sx, sy) = zoom; P = (W / 2, 960)
            M = np.float32([[z, 0, P[0] * (1 - z) + sx], [0, z, P[1] * (1 - z) + sy]])
            rgb = cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            chin = P[1] + (chin - P[1]) * z + sy
            pil = Image.fromarray(rgb)
        ctx.check(name, i, ov_bbox(ov), chin)
        base = pil.convert("RGBA"); base.alpha_composite(ov)
        p.stdin.write(base.convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    print(f"{name}: ok | folga mínima até o queixo ≈ {ctx.min_clear:.0f}px | violações: {len(ctx.violations)}", flush=True)
    if ctx.violations: print("  ", ctx.violations[:5])
    return out

if __name__ == "__main__":
    video, face, outdir = sys.argv[1:4]
    os.makedirs(outdir, exist_ok=True)
    names = sys.argv[4:] or list(VARIANTS)
    for n in VARIANTS:
        if any(n.startswith(a) for a in names): render(n, VARIANTS[n], video, face, outdir)
