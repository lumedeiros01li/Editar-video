"""Gera os elementos do topo como PNG transparente 1080x1920 (Pillow)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1920
FD = "/usr/share/fonts/opentype/inter/"
def inter(w, s): return ImageFont.truetype(FD + f"Inter-{w}.otf", s)
SER = "/usr/share/fonts/truetype/liberation/LiberationSerif-"
def serif(st, s): return ImageFont.truetype(SER + st + ".ttf", s)
YEL = (255, 214, 0, 255); WHITE = (255, 255, 255, 255)

def canvas(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def shadow(img, blur=14, off=(0, 8), alpha=150):
    a = img.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0)); out.alpha_composite(sh, off); out.alpha_composite(img)
    return out
def tw(d, t, f): return d.textlength(t, font=f)
def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if tw(d, t, f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines
def ctext(d, cx, y, t, f, fill, stroke=0, sfill=(0, 0, 0, 255)):
    d.text((cx - tw(d, t, f) / 2, y), t, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
def rich(d, cx, y, parts, f, stroke=0):
    """parts = [(texto, cor)] numa linha, centralizado."""
    tot = sum(tw(d, t, f) for t, _ in parts); x = cx - tot / 2
    for t, c in parts:
        d.text((x, y), t, font=f, fill=c, stroke_width=stroke, stroke_fill=(0, 0, 0, 255)); x += tw(d, t, f)

def sticker_ig(titulo, corpo, y=150):
    """Balao de resposta do Instagram: cabecalho escuro + corpo branco."""
    im = canvas(); d = ImageDraw.Draw(im); x0, x1 = 40, W - 40; hh = 112
    fb = inter("Medium", 54); lines = wrap(d, corpo, fb, x1 - x0 - 90); bh = 50 + len(lines) * 70 + 20
    d.rounded_rectangle((x0, y, x1, y + hh + 40), 38, fill=(28, 31, 38, 255))
    d.rectangle((x0, y + hh - 6, x1, y + hh + 40), fill=(28, 31, 38, 255))
    d.rounded_rectangle((x0, y + hh, x1, y + hh + bh), 38, fill=(255, 255, 255, 255))
    d.rectangle((x0, y + hh, x1, y + hh + 40), fill=(255, 255, 255, 255))
    ctext(d, W / 2, y + 28, titulo, inter("SemiBold", 42), WHITE)
    for i, l in enumerate(lines): ctext(d, W / 2, y + hh + 34 + i * 70, l, fb, (20, 20, 22, 255))
    return shadow(im)

def impacto(linhas, y=150, cor=None):
    """Texto grande branco com palavras-chave amarelas. linhas = [[(texto, '#'|'')...]]; cor amarela quando marcado com *"""
    im = canvas(); d = ImageDraw.Draw(im); f = inter("Black", 80)
    for i, ln in enumerate(linhas):
        parts, on = [], False
        for t in ln.split():
            if t.startswith("*"): on = True
            parts.append((t.strip("*") + " ", (cor or YEL) if on else WHITE))
            if t.endswith("*"): on = False
        rich(d, W / 2, y + i * 100, parts, f, stroke=7)
    return shadow(im, 10, (0, 7), 200)

# ---------------- brutalista ----------------
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
def mono(s): return ImageFont.truetype(MONO, s)
BLK = (0, 0, 0, 255)
def hexc(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
def girar(layer, ang, cx, cy):
    r = layer.rotate(ang, resample=Image.BICUBIC, center=(cx, cy)); return r


CINZA = (240, 240, 240, 255); ROXO = (155, 107, 255, 255); LIMA = (228, 255, 107, 255)
MONOR = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
def brutal_c(tag, preto, roxo, linhas=(), y=0):
    """Painel cinza brutalista: etiqueta [ TAG ], titulo preto + bloco roxo, cartao branco com sombra roxa.
    linhas = [(rotulo, valor, etiqueta, riscado)]"""
    im = canvas(); d = ImageDraw.Draw(im)
    rows = len(linhas); ch = rows * 150; top = 214
    pan_h = (top + ch + 52) if rows else 224
    d.rectangle((0, y, W, y + pan_h), fill=CINZA); d.rectangle((0, y + pan_h - 6, W, y + pan_h), fill=BLK)
    ft = mono(34); t = f"[ {tag.upper()} ]"; tw_ = tw(d, t, ft) + 56
    d.rectangle((W / 2 - tw_ / 2, y + 22, W / 2 + tw_ / 2, y + 74), outline=BLK, width=5)
    d.text((W / 2 - tw_ / 2 + 28, y + 30), t, font=ft, fill=BLK)
    size = 92
    while True:
        f = inter("Black", size); wa = tw(d, preto.upper() + " ", f); wb = tw(d, roxo.upper(), f) + 44
        if wa + wb <= W - 90 or size < 50: break
        size -= 4
    x = (W - wa - wb) / 2; ty = y + 92
    d.text((x, ty), preto.upper(), font=f, fill=BLK)
    bx = x + wa; d.rectangle((bx, ty + 4, bx + wb, ty + size + 14), fill=ROXO)
    d.text((bx + 22, ty), roxo.upper(), font=f, fill=WHITE)
    if rows:
        x0, x1, c0 = 50, W - 50, y + top
        d.rectangle((x0 + 16, c0 + 16, x1 + 16, c0 + ch + 16), fill=ROXO)
        d.rectangle((x0, c0, x1, c0 + ch), fill=WHITE, outline=BLK, width=7)
        for r, (rot, val, etq, risc) in enumerate(linhas):
            ry = c0 + r * 150
            if r: d.line((x0 + 44, ry, x1 - 44, ry), fill=BLK, width=3)
            d.text((x0 + 44, ry + 56), rot, font=ImageFont.truetype(MONOR, 36), fill=(90, 90, 90, 255))
            fv = inter("Black", 62); vw = tw(d, val, fv); vx = x1 - 44 - vw
            d.text((vx, ry + 10), val, font=fv, fill=BLK)
            if risc: d.rectangle((vx - 6, ry + 10 + 40, vx + vw + 6, ry + 10 + 52), fill=ROXO)
            if etq:
                fe = mono(32); ew = tw(d, etq, fe) + 44; ex = x1 - 44 - ew
                d.rectangle((ex, ry + 88, x1 - 44, ry + 88 + 46), fill=LIMA if not risc else WHITE, outline=BLK, width=4)
                d.text((ex + 22, ry + 88 + 5), etq, font=fe, fill=BLK)
    return im
