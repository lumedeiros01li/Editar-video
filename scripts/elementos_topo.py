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

def serifado(linhas, y=150):
    """linhas = [(texto, 'peq'|'dest'|'norm')]: serifa fina cinza, destaque itálico amarelo grande."""
    im = canvas(); d = ImageDraw.Draw(im); yy = y
    for t, k in linhas:
        if k == "peq": f, c, h = serif("Regular", 66), (215, 215, 220, 255), 84
        elif k == "dest": f, c, h = serif("Italic", 120), YEL, 128
        else: f, c, h = serif("Regular", 92), WHITE, 108
        ctext(d, W / 2, yy, t, f, c); yy += h
    return shadow(im, 12, (0, 6), 235)

def estatistica(num, rotulo, y=170):
    im = canvas(); d = ImageDraw.Draw(im); x0, x1 = 50, W - 50
    d.rounded_rectangle((x0, y, x1, y + 210), 44, fill=(14, 14, 20, 215))
    d.rounded_rectangle((x0 + 26, y + 26, x0 + 40, y + 184), 7, fill=YEL)
    fn = inter("Black", 118); d.text((x0 + 76, y + 30), num, font=fn, fill=YEL)
    nx = x0 + 76 + tw(d, num, fn) + 40
    lines = wrap(d, rotulo, inter("SemiBold", 44), x1 - nx - 40)
    for i, l in enumerate(lines): d.text((nx, y + 105 - len(lines) * 28 + i * 56), l, font=inter("SemiBold", 44), fill=WHITE)
    return shadow(im, 12, (0, 8), 120)

def balao_chat(texto, lado, y):
    im = canvas(); d = ImageDraw.Draw(im); f = inter("Medium", 50); lines = wrap(d, texto, f, 640)
    w = max(tw(d, l, f) for l in lines) + 84; h = len(lines) * 64 + 44
    x0 = 50 if lado == "esq" else W - 50 - w
    if lado == "esq": d.rounded_rectangle((x0, y, x0 + w, y + h), 42, fill=(238, 238, 240, 255)); col = (20, 20, 24, 255)
    else:
        g = Image.new("RGBA", (int(w), int(h))); gd = ImageDraw.Draw(g)
        for i in range(int(w)):
            t = i / w; gd.line((i, 0, i, h), fill=(int(120 + 60 * t), int(80 - 10 * t), int(255 - 40 * t), 255))
        m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), 42, fill=255); im.paste(g, (int(x0), y), m); col = WHITE
    for i, l in enumerate(lines): d.text((x0 + 42, y + 22 + i * 64), l, font=f, fill=col)
    return shadow(im, 10, (0, 6), 90), y + h

def manchete(titulo, sub, y=170):
    im = canvas(); d = ImageDraw.Draw(im)
    g = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for i in range(W): gd.line((i, 0, i, 260), fill=(0, 0, 0, int(190 * max(0, 1 - i / (W * 0.95)))))
    im.alpha_composite(g, (0, y)); d = ImageDraw.Draw(im)
    d.rectangle((50, y + 30, 66, y + 230), fill=YEL)
    d.text((100, y + 28), titulo, font=inter("ExtraBold", 80), fill=WHITE)
    d.text((100, y + 140), sub, font=inter("Medium", 44), fill=(230, 230, 235, 255))
    return im

def checklist(itens, n, y=150):
    """Cartao branco com itens; n = quantos ja aparecem marcados."""
    im = canvas(); d = ImageDraw.Draw(im); x0, x1 = 60, W - 60; h = 150 + 100 * len(itens)
    d.rounded_rectangle((x0, y, x1, y + h), 44, fill=(255, 255, 255, 250))
    d.text((x0 + 50, y + 30), "O básico da edição", font=inter("ExtraBold", 50), fill=(20, 20, 24, 255))
    for i, t in enumerate(itens[:n]):
        cy = y + 130 + i * 100
        d.ellipse((x0 + 50, cy + 6, x0 + 100, cy + 56), fill=(34, 197, 94, 255))
        d.line((x0 + 63, cy + 32, x0 + 73, cy + 43, x0 + 90, cy + 20), fill=WHITE, width=7, joint="curve")
        d.text((x0 + 125, cy + 3), t, font=inter("SemiBold", 48), fill=(30, 30, 36, 255))
    return shadow(im, 14, (0, 8), 110)

# ---------------- brutalista ----------------
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
def mono(s): return ImageFont.truetype(MONO, s)
BLK = (0, 0, 0, 255)
def hexc(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
def girar(layer, ang, cx, cy):
    r = layer.rotate(ang, resample=Image.BICUBIC, center=(cx, cy)); return r

def brutal_card(cab, corpo, cor_cab, y=150, ang=-2.0):
    """Cartao neo-brutalista: borda preta grossa, sombra dura, cabecalho mono colorido."""
    im = canvas(); d = ImageDraw.Draw(im); x0, x1 = 60, W - 90; fb = inter("Black", 62)
    lines = wrap(d, corpo.upper(), fb, x1 - x0 - 70); h = 96 + 40 + len(lines) * 74
    d.rectangle((x0 + 18, y + 18, x1 + 18, y + h + 18), fill=BLK)
    d.rectangle((x0, y, x1, y + h), fill=(255, 255, 255, 255), outline=BLK, width=8)
    d.rectangle((x0, y, x1, y + 96), fill=hexc(cor_cab), outline=BLK, width=8)
    d.text((x0 + 36, y + 24), cab.upper(), font=mono(40), fill=BLK)
    for i, l in enumerate(lines): d.text((x0 + 36, y + 96 + 28 + i * 74), l, font=fb, fill=BLK)
    return girar(im, ang, W / 2, y + h / 2)

def brutal_faixa(texto, tag, cor, y=170, ang=1.6):
    """Faixa crua: fita listrada + barra preta com texto mono e etiqueta de cor chapada."""
    im = canvas(); d = ImageDraw.Draw(im)
    for i in range(-2, 40):  # fita de alerta
        d.polygon([(i * 56, y), (i * 56 + 28, y), (i * 56 + 56, y + 44), (i * 56 + 28, y + 44)], fill=hexc(cor))
    d.rectangle((0, y, W, y + 44), outline=BLK, width=6)
    f = mono(46); lines = wrap(d, texto.upper(), f, W - 100); h = 40 + len(lines) * 72
    d.rectangle((0, y + 44, W, y + 44 + h), fill=BLK)
    for i, l in enumerate(lines): d.text((54, y + 44 + 24 + i * 72), l, font=f, fill=WHITE)
    ft = mono(36); w = tw(d, tag.upper(), ft) + 48; ty = y + 44 + h
    d.rectangle((54 + 10, ty + 10, 54 + w + 10, ty + 76 + 10), fill=BLK)
    d.rectangle((54, ty, 54 + w, ty + 76), fill=hexc(cor), outline=BLK, width=6)
    d.text((54 + 24, ty + 18), tag.upper(), font=ft, fill=BLK)
    return girar(im, ang, W / 2, y + 120)

def brutal_bloco(linhas, cor_bloco, cor_dest, y=150, ang=-1.5):
    """Bloco chapado de cor com texto gigante preto e ultima linha em marca-texto."""
    im = canvas(); d = ImageDraw.Draw(im); f = inter("Black", 96); x0, x1 = 50, W - 70; h = 60 + len(linhas) * 112
    d.rectangle((x0 + 20, y + 20, x1 + 20, y + h + 20), fill=BLK)
    d.rectangle((x0, y, x1, y + h), fill=hexc(cor_bloco), outline=BLK, width=9)
    for i, l in enumerate(linhas):
        ty = y + 34 + i * 112; l = l.upper()
        if i == len(linhas) - 1:
            w = tw(d, l, f); d.rectangle((x0 + 34, ty + 6, x0 + 34 + w + 30, ty + 104), fill=hexc(cor_dest), outline=BLK, width=6)
            d.text((x0 + 50, ty), l, font=f, fill=BLK)
        else: d.text((x0 + 50, ty), l, font=f, fill=BLK)
    return girar(im, ang, W / 2, y + h / 2)
