"""Edicao de reel falado: corta respiracoes/erros, melhora a imagem, caixa de pergunta fixa e legenda.

uso: python3 editar_reel.py ORIGINAL.mp4 WORKDIR SAIDA.mp4 CONFIG.json [--rapido]
"""
import json, math, subprocess, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, WORK, OUT = sys.argv[1:4]
FAST = "--rapido" in sys.argv
FPS, SR = 30, 16000
W, H = 1080, 1920

CFG = json.load(open(sys.argv[4]))
PERGUNTA = CFG["pergunta"]
# trechos de fala cortados por serem erros/hesitacoes (segundos no original)
CORTES_MANUAIS = [tuple(c) for c in CFG.get("cortes", [])]
# [fim aproximado do trecho, fim maximo]: limita a folga final (ex.: antes de virar a cabeca)
FIM_MAX = [tuple(c) for c in CFG.get("fim_max", [])]
# transcricao revisada: "ancora_no_original palavra|..." (a ancora so decide em qual trecho de fala a palavra cai)
PALAVRAS = [(float(a), w) for a, w in (x.split(" ", 1) for x in CFG["palavras"].replace("\n", "|").split("|") if x.strip())]


def features():
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", f"{WORK}/a.raw"], check=True)
    a = np.fromfile(f"{WORK}/a.raw", dtype=np.int16).astype(np.float32) / 32768
    hop, win = 160, 480
    n = (len(a) - win) // hop
    fr = np.lib.stride_tricks.sliding_window_view(a, win)[::hop][:n]
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    fr0 = fr - fr.mean(1, keepdims=True)
    ac = np.fft.irfft(np.abs(np.fft.rfft(fr0, n=1024)) ** 2)[:, :win]
    ac = ac / (ac[:, :1] + 1e-9)
    voi = ac[:, int(SR / 400):int(SR / 75)].max(1)
    P = np.abs(np.fft.rfft(fr * np.hanning(win), n=512)) ** 2
    cen = (P * np.fft.rfftfreq(512, 1 / SR)).sum(1) / (P.sum(1) + 1e-12)
    t = np.arange(n) * hop / SR + win / 2 / SR
    return t, db, voi, cen


def trechos_de_fala(t, db, voi, cen):
    dt = 0.01
    act = db > -47
    runs, i = [], 0
    while i < len(act):
        if act[i]:
            j = i
            while j < len(act) and act[j]:
                j += 1
            runs.append([i, j]); i = j
        else:
            i += 1
    m = []
    for r in runs:  # micro pausas naturais (<=0,10s) ficam
        if m and (r[0] - m[-1][1]) * dt <= 0.10:
            m[-1][1] = r[1]
        else:
            m.append(list(r))
    voiced = (voi > 0.55) & (db > -42)
    breathy = (voi < 0.5) & (db < -33) & (cen < 3000)
    seg, log = [], []
    for a, b in m:
        ta, tb = t[a], t[b - 1]
        if any(ta >= c0 - 0.05 and tb <= c1 + 0.05 for c0, c1 in CORTES_MANUAIS):
            log.append(("vicio/hesitacao", ta, tb)); continue
        if voiced[a:b].sum() < 3:
            log.append(("sem voz (respiracao/ruido)", ta, tb)); continue
        h = a
        while h < b and breathy[h]:
            h += 1
        if (h - a) * dt > 0.10:
            log.append(("inspiracao", t[a], t[h])); a = h - 4
        e = b
        while e > a and breathy[e - 1]:
            e -= 1
        if (b - e) * dt > 0.10:
            log.append(("expiracao", t[e], t[b - 1])); b = e + 4
        seg.append([t[a], t[b - 1]])
    return seg, log


def quadros(seg, dur):
    """trechos finais com folga, em quadros inteiros. retorna [(f0, f1, fala_ini, fala_fim)]"""
    PRE, POST = 0.05, 0.09
    out = []
    for k, (s, e) in enumerate(seg):
        ps = PRE if k == 0 else min(PRE, (s - seg[k - 1][1]) / 2)
        pe = POST if k == len(seg) - 1 else min(POST, (seg[k + 1][0] - e) / 2)
        f0, f1 = round((s - ps) * FPS), round((e + pe) * FPS)
        if out and f0 < out[-1][1]:
            f0 = out[-1][1]
        for fe, fm in FIM_MAX:
            if abs(e - fe) < 0.15:
                f1 = min(f1, round(fm * FPS))
        out.append((max(0, f0), min(int(dur * FPS), f1), s, e))
    return out


def palavras_por_trecho(seg):
    por = [[] for _ in seg]
    sem = []
    for t0, w in PALAVRAS:
        d = [max(s - t0, t0 - e, 0) for s, e in seg]
        k = int(np.argmin(d))
        (por[k] if d[k] <= 0.45 else sem).append((t0, w))
    return por, sem


def peso(w):
    p = w.strip(".,?!")
    return 3 + 2 * len(p) if p.isdigit() else max(2, len(p))


def legenda_ass(q, por, seg):
    """eventos palavra a palavra no tempo da saida"""
    saida, acc = [], 0.0
    for (f0, f1, s, e) in q:
        saida.append(acc); acc += (f1 - f0) / FPS
    words = []  # (ini, fim, texto) no tempo da saida
    for k, (f0, f1, s, e) in enumerate(q):
        ws = por[k]
        if not ws:
            continue
        tot = sum(peso(w) for _, w in ws)
        t = saida[k] + (s - f0 / FPS)
        dur = e - s
        for _, w in ws:
            d = dur * peso(w) / tot
            words.append((t, t + d, w)); t += d
    # blocos de ate 3 palavras / 22 caracteres, quebrando em pontuacao e pausas
    blocos, cur = [], []
    for w in words:
        if cur and (len(cur) >= 3 or len(" ".join(x[2] for x in cur + [w])) > 22 or cur[-1][2][-1] in ".,?!" or w[0] - cur[-1][1] > 0.25):
            blocos.append(cur); cur = []
        cur.append(w)
    if cur:
        blocos.append(cur)
    BR, LIM = "&H00FFFFFF&", "&H0070FFEB&"
    ev = []
    for bi, b in enumerate(blocos):
        fim_bloco = b[-1][1] + 0.10
        if bi + 1 < len(blocos):
            fim_bloco = min(fim_bloco, blocos[bi + 1][0][0])
        for i, (t0, t1, _) in enumerate(b):
            ini = t0
            fim = b[i + 1][0] if i + 1 < len(b) else fim_bloco
            txt = " ".join(("{\\c%s}" % (LIM if j == i else BR)) + b[j][2] for j in range(len(b)))
            ev.append((ini, fim, txt))
    f = lambda x: "%d:%02d:%05.2f" % (x // 3600, (x % 3600) // 60, x % 60)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Padrao,JetBrains Mono,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,8,6,2,60,60,{LEGENDA_MV},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    open(f"{WORK}/legenda.ass", "w").write(head + "".join(f"Dialogue: 0,{f(a)},{f(b)},Padrao,,0,0,0,,{x}\n" for a, b, x in ev))
    return acc, len(blocos)


def caixa_pergunta():
    """sticker de caixa de perguntas do Instagram, fixo, acima da cabeca"""
    S = 2  # supersample
    cw, x0, y0 = 980, 50, 262
    fb = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 38 * S)
    fl = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 24 * S)
    dr0 = ImageDraw.Draw(Image.new("L", (10, 10)))
    def quebra(larg):
        linhas, cur = [], ""
        for w in PERGUNTA.split():
            t = (cur + " " + w).strip()
            if dr0.textlength(t, font=fb) > larg * S and cur:
                linhas.append(cur); cur = w
            else:
                cur = t
        return linhas + [cur]
    larg = cw - 70
    n = len(quebra(larg))
    while len(quebra(larg - 10)) == n:  # equilibra as linhas, sem palavra sozinha na ultima
        larg -= 10
    linhas = quebra(larg)
    lh = 48
    ch = 30 + 28 + 12 + lh * len(linhas) + 28
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    box = (x0 * S, y0 * S, (x0 + cw) * S, (y0 + ch) * S)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((box[0], box[1] + 10 * S, box[2], box[3] + 10 * S), 44 * S, fill=(0, 0, 0, 90))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14 * S)))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle(box, 44 * S, fill=(255, 255, 255, 255))
    ty = (y0 + 30) * S
    dr.text((W * S / 2, ty), "Pergunta", font=fl, fill=(142, 142, 142, 255), anchor="mt")
    ty += (28 + 12) * S
    for l in linhas:
        dr.text((W * S / 2, ty), l, font=fb, fill=(17, 17, 17, 255), anchor="mt")
        ty += lh * S
    img = img.resize((W, H), Image.LANCZOS)
    img.save(f"{WORK}/pergunta.png")
    print('linhas da pergunta:', len(linhas))
    return y0, y0 + ch


# legenda logo abaixo da caixa, acima da cabeca (o rosto ocupa a metade de baixo do quadro)
LEGENDA_BASE = 612
LEGENDA_MV = H - LEGENDA_BASE

if __name__ == "__main__":
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC]))
    t, db, voi, cen = features()
    seg, log = trechos_de_fala(t, db, voi, cen)
    q = quadros(seg, dur)
    por, sem = palavras_por_trecho(seg)
    for l in log:
        print("cortado:", l[0], round(l[1], 2), round(l[2], 2))
    for k, (s, e) in enumerate(seg):
        if not por[k]:
            print("AVISO trecho sem palavras (ruido?):", round(s, 2), round(e, 2))
    for t0, w in sem:
        print("AVISO palavra sem trecho:", t0, w)
    total, nb = legenda_ass(q, por, seg)
    y0, y1 = caixa_pergunta()
    print(f"{len(q)} trechos, {dur:.1f}s -> {total:.1f}s, {nb} blocos de legenda, caixa y={y0}-{y1}")
    fc = []
    n = len(q)
    fc.append("[0:v]fps=30,scale=in_color_matrix=bt470bg:out_color_matrix=bt709:in_range=full:out_range=tv,format=yuv420p,"
              f"split={n}" + "".join(f"[s{k}]" for k in range(n)))
    for k, (f0, f1, s, e) in enumerate(q):
        d = (f1 - f0) / FPS
        fc.append(f"[s{k}]trim=start_frame={f0}:end_frame={f1},setpts=PTS-STARTPTS[v{k}];"
                  f"[0:a]atrim=start={f0 / FPS:.4f}:end={f1 / FPS:.4f},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:d=0.012,afade=t=out:st={d - 0.012:.4f}:d=0.012[a{k}]")
    fc.append("".join(f"[v{k}][a{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    fc.append("[vc]hqdn3d=1.6:1.6:5:5,eq=contrast=1.05:saturation=1.10:gamma=1.04,unsharp=5:5:0.7:5:5:0.0[vo]")
    fc.append("[vo][1:v]overlay=0:0:format=auto[vp]")
    fc.append(f"[vp]ass={WORK}/legenda.ass[vf]")
    open(f"{WORK}/fc.txt", "w").write(";\n".join(fc))
    cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-i", SRC, "-i", f"{WORK}/pergunta.png", "-filter_complex_script", f"{WORK}/fc.txt",
           "-map", "[vf]", "-map", "[ac]", "-c:v", "libx264", "-preset", "veryfast" if FAST else "slow", "-crf", "20" if FAST else "20",
           "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
    subprocess.run(cmd, check=True)
    json.dump({"q": q}, open(f"{WORK}/q.json", "w"))
