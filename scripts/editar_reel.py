"""Edicao de reel falado: corta respiracoes/erros, melhora a imagem, caixa de pergunta fixa e legenda.

uso: python3 editar_reel.py ORIGINAL.mp4 WORKDIR SAIDA.mp4 CONFIG.json [--rapido]
"""
import json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import os
SRC, WORK, OUT = (os.path.abspath(a) for a in sys.argv[1:4])
FAST = "--rapido" in sys.argv
FPS, SR = 30, 16000
W, H = 1080, 1920

CFG = json.load(open(sys.argv[4]))
# trechos de fala cortados por serem erros/hesitacoes (segundos no original)
CORTES_MANUAIS = [tuple(c) for c in CFG.get("cortes", [])]
# [fim aproximado do trecho, fim maximo]: limita a folga final (ex.: antes de virar a cabeca)
FIM_MAX = [tuple(c) for c in CFG.get("fim_max", [])]
# cortes dentro de uma fala continua (palavra errada, gagueira): [ini, fim] aproximados, encaixados no ponto mais silencioso
CORTES_INTERNOS = [tuple(c) for c in CFG.get("cortes_internos", [])]
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
        if voiced[a:b].sum() < 3 or (db[a:b].max() < -25 and voiced[a:b].sum() < 0.3 * (b - a)):
            log.append(("sem voz (respiracao/ruido)", ta, tb)); continue
        h = a
        while h < b and breathy[h]:
            h += 1
        if (h - a) * dt > 0.10:
            log.append(("inspiracao", t[a], t[h])); a = h - 3
        e = b
        while e > a and breathy[e - 1]:
            e -= 1
        if (b - e) * dt > 0.10:
            log.append(("expiracao", t[e], t[b - 1])); b = e + 3
        seg.append([t[a], t[b - 1], False, False])
    suav = np.convolve(db, np.ones(5) / 5, "same")
    def vale(alvo, w=0.12):
        i0, i1 = max(int((alvo - w) / dt), 0), min(int((alvo + w) / dt), len(db))
        return float(t[i0 + int(np.argmin(suav[i0:i1]))])
    for ca, cb in CORTES_INTERNOS:
        a2, b2 = vale(ca), vale(cb)
        novo = []
        for sg in seg:
            if sg[1] <= a2 or sg[0] >= b2:
                novo.append(sg); continue
            if sg[0] < a2 - 0.15:
                novo.append([sg[0], a2, sg[2], True])
            if sg[1] > b2 + 0.15:
                novo.append([b2, sg[1], True, sg[3]])
        seg = novo
        log.append(("corte interno", a2, b2))
    return seg, log


def quadros(seg, dur):
    """trechos finais com folga, em quadros inteiros. retorna [(f0, f1, fala_ini, fala_fim)]"""
    PRE, POST = 0.03, 0.06
    out = []
    for k, sg in enumerate(seg):
        s, e = sg[0], sg[1]
        ps = 0 if sg[2] else PRE if k == 0 else min(PRE, (s - seg[k - 1][1]) / 2)
        pe = 0 if sg[3] else POST if k == len(seg) - 1 else min(POST, (seg[k + 1][0] - e) / 2)
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
        d = [max(sg[0] - t0, t0 - sg[1], 0) for sg in seg]
        k = int(np.argmin(d))
        (por[k] if d[k] <= 0.45 else sem).append((t0, w))
    return por, sem


def peso(w):
    p = w.strip(".,?!")
    return 3 + 2 * len(p) if p.isdigit() else max(2, len(p))


INTER = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
SUB_Y = 1640  # centro da legenda (85% da altura, abaixo do queixo)
SUB_H = 160
FUNCIONAIS = {"a", "o", "e", "de", "do", "da", "que", "um", "uma", "no", "na", "em", "pra", "pro", "com", "ou", "os", "as", "ao", "se", "eu", "já", "é"}


def fala_em_frases(q, por):
    """palavras no tempo da saida, agrupadas em frases curtas: [(ini, fim, texto)]"""
    saida, acc = [], 0.0
    for (f0, f1, s, e) in q:
        saida.append(acc); acc += (f1 - f0) / FPS
    words = []
    for k, (f0, f1, s, e) in enumerate(q):
        ws = por[k]
        if not ws:
            continue
        tot = sum(peso(w) for _, w in ws)
        t = saida[k] + (s - f0 / FPS)
        for _, w in ws:
            d = (e - s) * peso(w) / tot
            words.append((t, t + d, w, k)); t += d
    frases, cur = [], []
    for w in words:
        txt = " ".join(x[2] for x in cur)
        if cur and (cur[-1][2][-1] in ".?!" or (cur[-1][2][-1] == "," and len(txt) >= 16) or w[0] - cur[-1][1] > 0.25
                    or (w[3] != cur[-1][3] and q[w[3]][2] - q[cur[-1][3]][3] >= 0.45)):  # pausa longa cortada = fim de frase
            frases.append(cur); cur = []
        cur.append(w)
    if cur:
        frases.append(cur)
    MAX = 34  # caracteres por linha de legenda
    out = []
    for fr in frases:
        txt = " ".join(x[2] for x in fr)
        k = math.ceil(len(txt) / MAX)
        if k > 1:  # divide em partes de tamanho parecido
            alvo, ac, parte, partes = len(txt) / k, 0, [], []
            for x in fr:
                if parte and ac + len(x[2]) / 2 > alvo * (len(partes) + 1) and len(partes) < k - 1:
                    partes.append(parte); parte = []
                parte.append(x); ac += len(x[2]) + 1
            partes.append(parte)
            for i in range(len(partes) - 1):  # nao termina parte em artigo/preposicao
                while len(partes[i]) > 1 and partes[i][-1][2].lower().strip(",.?!") in FUNCIONAIS and \
                        len(" ".join(x[2] for x in [partes[i][-1]] + partes[i + 1])) <= 36:
                    partes[i + 1].insert(0, partes[i].pop())
        else:
            partes = [fr]
        for pt in partes:
            out.append([pt[0][0], pt[-1][1], " ".join(x[2] for x in pt)])
    for i, ev in enumerate(out):  # cada legenda some quando a proxima entra
        ev[1] = min(ev[1] + 0.12, out[i + 1][0]) if i + 1 < len(out) else ev[1] + 0.12
    return out, acc


def legenda_png(ev, total):
    """faixas de legenda (texto branco em retangulo escuro translucido) + lista concat com a duracao de cada uma"""
    S = 2
    fnt = ImageFont.truetype(INTER % "SemiBold", 50 * S)
    dr0 = ImageDraw.Draw(Image.new("L", (10, 10)))
    blank = Image.new("RGBA", (W, SUB_H), (0, 0, 0, 0))
    blank.save(f"{WORK}/sub_vazia.png")
    linhas, t_ant = [], 0
    def trecho(path, ini, fim):  # em quadros, sem acumular erro
        linhas.append(f"file '{path}'\nduration {(fim - ini) / FPS:.4f}")
    cursor = 0
    for i, (a, b, txt) in enumerate(ev):
        fa, fb = round(a * FPS), round(b * FPS)
        fa = max(fa, cursor)
        if fb <= fa:
            continue
        if fa > cursor:
            trecho(f"{WORK}/sub_vazia.png", cursor, fa)
        w = dr0.textlength(txt, font=fnt) / S
        bw, bh = w + 64, 92
        img = Image.new("RGBA", (W * S, SUB_H * S), (0, 0, 0, 0))
        x0, y0 = (W - bw) / 2, (SUB_H - bh) / 2
        ImageDraw.Draw(img).rounded_rectangle((x0 * S, y0 * S, (x0 + bw) * S, (y0 + bh) * S), 18 * S, fill=(0, 0, 0, 170))
        ImageDraw.Draw(img).text((W * S / 2, SUB_H * S / 2 - 2 * S), txt, font=fnt, fill=(255, 255, 255, 255), anchor="mm")
        img.resize((W, SUB_H), Image.LANCZOS).save(f"{WORK}/sub_{i:03d}.png")
        trecho(f"{WORK}/sub_{i:03d}.png", fa, fb)
        cursor = fb
    trecho(f"{WORK}/sub_vazia.png", cursor, round(total * FPS) + 60)
    linhas.append(f"file '{WORK}/sub_vazia.png'")
    open(f"{WORK}/sub.txt", "w").write("\n".join(linhas) + "\n")


def caixa_pergunta():
    """sticker de pergunta do Instagram: cabecalho escuro com a pergunta e corpo branco com a resposta. fixo, acima da cabeca"""
    S = 2
    x0, y0, cw = 20, 150, W - 40
    R, HH = 36, 116
    fh = ImageFont.truetype(INTER % "SemiBold", 46 * S)
    dr0 = ImageDraw.Draw(Image.new("L", (10, 10)))
    def quebra(txt, larg, fb):
        linhas, cur = [], ""
        for w in txt.split():
            t = (cur + " " + w).strip()
            if dr0.textlength(t, font=fb) > larg * S and cur:
                linhas.append(cur); cur = w
            else:
                cur = t
        return linhas + [cur]
    larg = cw - 70
    for tam in (56, 54, 52, 50, 48, 46):  # maior fonte que deixa o corpo em ate 2 linhas
        fb = ImageFont.truetype(INTER % "Medium", tam * S)
        if len(quebra(CFG["texto"], larg, fb)) <= 2:
            break
    n = len(quebra(CFG["texto"], larg, fb))
    while len(quebra(CFG["texto"], larg - 10, fb)) == n:  # linhas equilibradas, sem palavra sozinha na ultima
        larg -= 10
    linhas = quebra(CFG["texto"], larg, fb)
    lh = 68
    bh = 40 + lh * len(linhas) + 38
    ch = HH + bh
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    box = (x0 * S, y0 * S, (x0 + cw) * S, (y0 + ch) * S)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((box[0], box[1] + 8 * S, box[2], box[3] + 8 * S), R * S, fill=(0, 0, 0, 80))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(10 * S)))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, R * S, fill=255)
    card = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dc = ImageDraw.Draw(card)
    dc.rectangle((box[0], box[1], box[2], (y0 + HH) * S), fill=(18, 20, 24, 255))
    dc.rectangle((box[0], (y0 + HH) * S, box[2], box[3]), fill=(255, 255, 255, 255))
    card.putalpha(Image.composite(card.getchannel("A"), Image.new("L", img.size, 0), mask))
    img = Image.alpha_composite(img, card)
    dr = ImageDraw.Draw(img)
    dr.text((W * S / 2, (y0 + HH / 2) * S), CFG["cabecalho"], font=fh, fill=(255, 255, 255, 255), anchor="mm")
    ty = (y0 + HH + 38) * S
    for l in linhas:
        dr.text((W * S / 2, ty), l, font=fb, fill=(38, 38, 38, 255), anchor="mt")
        ty += lh * S
    img.resize((W, H), Image.LANCZOS).save(f"{WORK}/pergunta.png")
    print('linhas do texto:', len(linhas))
    return y0, y0 + ch


if __name__ == "__main__":
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC]))
    t, db, voi, cen = features()
    seg, log = trechos_de_fala(t, db, voi, cen)
    q = quadros(seg, dur)
    por, sem = palavras_por_trecho(seg)
    for l in log:
        print("cortado:", l[0], round(l[1], 2), round(l[2], 2))
    for k, sg in enumerate(seg):
        s, e = sg[0], sg[1]
        if not por[k]:
            print("AVISO trecho sem palavras (ruido?):", round(s, 2), round(e, 2))
    for t0, w in sem:
        print("AVISO palavra sem trecho:", t0, w)
    ev, total = fala_em_frases(q, por)
    legenda_png(ev, total)
    y0, y1 = caixa_pergunta()
    print(f"{len(q)} trechos, {dur:.1f}s -> {total:.1f}s, {len(ev)} legendas, caixa y={y0}-{y1}")
    for a_, b_, tx in ev:
        print(f"  {a_:5.2f}-{b_:5.2f} {tx}")
    fc = []
    n = len(q)
    fc.append("[0:v]fps=30,scale=in_color_matrix=bt470bg:out_color_matrix=bt709:in_range=full:out_range=tv,format=yuv420p,"
              f"split={n}" + "".join(f"[s{k}]" for k in range(n)))
    for k, (f0, f1, s, e) in enumerate(q):
        d = (f1 - f0) / FPS
        fc.append(f"[s{k}]trim=start_frame={f0}:end_frame={f1},setpts=PTS-STARTPTS[v{k}];"
                  f"[0:a]atrim=start={f0 / FPS:.4f}:end={f1 / FPS:.4f},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:d=0.012,afade=t=out:st={d - 0.012:.4f}:d=0.012[a{k}]")
    fc.append("".join(f"[v{k}][a{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac0]")
    # reduz o que sobrou de respiracao/ruido fraco entre as palavras (abaixo de -42 dB cai ate -24 dB)
    fc.append("[ac0]agate=threshold=0.008:ratio=8:attack=6:release=150:range=0.06[ac]")
    fc.append("[vc]hqdn3d=1.6:1.6:5:5,eq=contrast=1.05:saturation=1.10:gamma=1.04,unsharp=5:5:0.7:5:5:0.0[vo]")
    fc.append("[vo][1:v]overlay=0:0:format=auto[vp]")
    fc.append("[2:v]fps=30,format=rgba[sb]")
    fc.append(f"[vp][sb]overlay=0:{SUB_Y - SUB_H // 2}:format=auto:eof_action=pass[vf]")
    open(f"{WORK}/fc.txt", "w").write(";\n".join(fc))
    cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-i", SRC, "-i", f"{WORK}/pergunta.png", "-f", "concat", "-safe", "0", "-i", f"{WORK}/sub.txt", "-filter_complex_script", f"{WORK}/fc.txt",
           "-map", "[vf]", "-map", "[ac]", "-c:v", "libx264", "-preset", "veryfast" if FAST else "slow", "-crf", "20" if FAST else "20",
           "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
    subprocess.run(cmd, check=True)
    json.dump({"q": q}, open(f"{WORK}/q.json", "w"))
