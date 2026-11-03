#!/usr/bin/env python3
"""Reels R7: texto em caixas (estilo referência) sobre vídeo vertical, sem cobrir o rosto.

Uso:
  python3 reels_r7.py VIDEO ROTEIRO.json SAIDA_SEM_EXTENSAO [--modo cor|pb|ambos] [--previa]

Gera SAIDA_cor.mp4 e/ou SAIDA_pb.mp4 (1080x1920, áudio original preservado).
Com --previa, salva SAIDA_previa_<modo>.png (um frame por tela + frame final).
"""
import argparse, json, math, os, subprocess, sys, urllib.request
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
CACHE = os.path.expanduser("~/.cache/reels_r7")
FACE_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
EMOJI_FONTS = ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", "/usr/share/fonts/noto/NotoColorEmoji.ttf",
               "/System/Library/Fonts/Apple Color Emoji.ttc"]

W, H = 1080, 1920
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
LIME, PURPLE = (234, 245, 107), (157, 116, 255)
FUNDOS = {"branco": (WHITE, BLACK), "lima": (LIME, BLACK), "roxo": (PURPLE, WHITE), "preto": (BLACK, LIME)}
DESTAQUE = (PURPLE, WHITE)

# padrão aprovado
SIZE, GAP, PADX, HMUL, RADIUS = 80, 6, 28, 1.4, 8
CALL_SIZE = 58
MARGEM_QUEIXO = 84          # folga entre queixo e topo do texto
LIMITE_BAIXO = 1680         # não descer além disso (UI do Reels)
LIMITE_CIMA = 170
MAX_W = 1000                # largura máxima de uma caixa

# ------------------------------------------------------------------ fontes / emoji
_fc = {}
def pf(size, w=500):
    k = (int(size), w)
    if k not in _fc: _fc[k] = ImageFont.truetype(os.path.join(ASSETS, f"poppins-{w}.woff"), int(size))
    return _fc[k]

EMOJI_PATH = next((p for p in EMOJI_FONTS if os.path.exists(p)), None)
_ec = {}
def emoji_img(ch, size):
    k = (ch, int(size))
    if k not in _ec:
        f = ImageFont.truetype(EMOJI_PATH, 109)
        bb = f.getbbox(ch)
        im = Image.new("RGBA", (max(bb[2], 1) + 4, max(bb[3], 1) + 4), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), ch, font=f, embedded_color=True)
        s = size * 1.05 / 128
        _ec[k] = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    return _ec[k]

def is_emoji(c):
    o = ord(c)
    return o >= 0x1F000 or 0x2600 <= o <= 0x27BF or o in (0xFE0F, 0x200D) or 0x2B00 <= o <= 0x2BFF

def runs_of(text):
    """divide texto em trechos [(texto, é_emoji)]; cada emoji (com modificadores) é um trecho"""
    res, i = [], 0
    while i < len(text):
        c = text[i]
        if is_emoji(c):
            j = i + 1
            while j < len(text) and (ord(text[j]) in (0xFE0F, 0x200D) or ord(text[j - 1]) == 0x200D): j += 1
            if EMOJI_PATH: res.append((text[i:j], True))
            i = j
        else:
            if res and not res[-1][1]: res[-1] = (res[-1][0] + c, False)
            else: res.append((c, False))
            i += 1
    return res

# ------------------------------------------------------------------ caixas
def run_w(t, e, size, weight):
    return emoji_img(t, size).width if e else pf(size, weight).getlength(t)

def box(text, size, bg, fg, weight=500, hmul=HMUL, outline=None):
    runs = runs_of(text)
    while size > 40 and sum(run_w(t, e, size, weight) for t, e in runs) + PADX * 2 > MAX_W: size -= 2
    ws = [run_w(t, e, size, weight) for t, e in runs]
    bw, bh, pad = int(sum(ws) + PADX * 2), int(size * hmul), 10
    im = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + bw, pad + bh), RADIUS, fill=bg + (255,),
                        outline=(outline + (255,)) if outline else None, width=3 if outline else 0)
    x, cy = pad + PADX, pad + bh / 2
    for (t, e), w in zip(runs, ws):
        if e: em = emoji_img(t, size); im.alpha_composite(em, (int(x), int(cy - em.height / 2)))
        else: d.text((x, cy + 0.70 * size / 2), t, font=pf(size, weight), fill=fg + (255,), anchor="ls")
        x += w
    return im, bh

def barra(width, h=10):
    im = Image.new("RGBA", (width + 20, h + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((10, 10, 10 + width, 10 + h), h // 2, fill=PURPLE + (255,))
    return im

def build_screen(tela, scale):
    bg, fg = FUNDOS.get(tela.get("fundo", "branco"), FUNDOS["branco"])
    out = []
    for ln in tela["linhas"]:
        if ln.startswith("*") and ln.endswith("*") and len(ln) > 2:
            out.append(box(ln[1:-1], SIZE * scale, *DESTAQUE))
        else:
            out.append(box(ln, SIZE * scale, bg, fg))
    return out

def stack_h(boxes): return sum(h for _, h in boxes) + GAP * (len(boxes) - 1)

# ------------------------------------------------------------------ util
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3

def paste(ov, layer, x, y):
    x, y = int(x), int(y); sx, sy = max(0, -x), max(0, -y)
    if sx >= layer.width or sy >= layer.height: return
    layer = layer.crop((sx, sy, min(layer.width, W - x), min(layer.height, H - y)))
    if layer.width > 0 and layer.height > 0: ov.alpha_composite(layer, (x + sx, y + sy))

def place(ov, layer, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.003: return
    if abs(scale - 1) > 0.003:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BILINEAR)
    if alpha < 0.995:
        layer = layer.copy(); layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    paste(ov, layer, cx - layer.width / 2, cy - layer.height / 2)

ENQUADRAMENTO = "auto"   # auto | preencher | ajustar

def _cover(frame):
    h, w = frame.shape[:2]; s = max(W / w, H / h)
    fr = cv2.resize(frame, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y0, x0 = (fr.shape[0] - H) // 2, (fr.shape[1] - W) // 2
    return fr[y0:y0 + H, x0:x0 + W]

def fit(frame):
    """1080x1920. Vertical: preenche. Horizontal/quadrado: vídeo inteiro no meio com fundo desfocado."""
    h, w = frame.shape[:2]
    mode = ENQUADRAMENTO if ENQUADRAMENTO != "auto" else ("preencher" if w / h < 0.7 else "ajustar")
    if mode == "preencher": return _cover(frame)
    small = cv2.resize(_cover(frame), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    bg = cv2.resize(cv2.GaussianBlur(small, (0, 0), 6), (W, H), interpolation=cv2.INTER_LINEAR)
    bg = (bg.astype(np.float32) * 0.55).astype(np.uint8)
    s = W / w; nh = int(round(h * s))
    if nh > H: s = H / h; nh = H
    nw = int(round(w * s))
    fg = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y0, x0 = (H - nh) // 2, (W - nw) // 2
    bg[y0:y0 + nh, x0:x0 + nw] = fg
    return bg

def frames(path):
    cap = cv2.VideoCapture(path)
    while True:
        ok, fr = cap.read()
        if not ok: break
        yield fit(fr)

# ------------------------------------------------------------------ rosto
def detect_faces(video):
    os.makedirs(CACHE, exist_ok=True)
    mp_model = os.path.join(CACHE, "face.tflite")
    if not os.path.exists(mp_model): urllib.request.urlretrieve(FACE_URL, mp_model)
    import mediapipe as mp
    from mediapipe.tasks import python as mpp
    from mediapipe.tasks.python import vision
    det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=mpp.BaseOptions(model_asset_path=mp_model), min_detection_confidence=0.35))
    boxes = []
    for fr in frames(video):
        small = cv2.cvtColor(cv2.resize(fr, (W // 2, H // 2)), cv2.COLOR_BGR2RGB)
        r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(small)))
        if r.detections:
            b = max(r.detections, key=lambda d: d.bounding_box.width * d.bounding_box.height).bounding_box
            boxes.append([b.origin_x * 2, b.origin_y * 2, b.width * 2, b.height * 2])
        else:
            boxes.append(None)
    return boxes

def clean_faces(raw):
    """remove falsos positivos (mãos, logos) e interpola. Retorna array Nx4 ou None."""
    ok = [i for i, b in enumerate(raw) if b is not None]
    if len(ok) < max(3, len(raw) * 0.15): return None
    b = np.array([raw[i] for i in ok], dtype=np.float64)
    med_h = np.median(b[:, 3]); med_cy = np.median(b[:, 1] + b[:, 3] / 2)
    good = (np.abs(b[:, 3] - med_h) < 0.35 * med_h) & (np.abs(b[:, 1] + b[:, 3] / 2 - med_cy) < 1.2 * med_h)
    idx = np.array(ok)[good]; b = b[good]
    n = len(raw); out = np.zeros((n, 4)); t = np.arange(n)
    for k in range(4): out[:, k] = np.interp(t, idx, b[:, k])
    return out

# ------------------------------------------------------------------ layout
def choose_top(faces, f0, f1, block_h):
    """posição vertical do bloco para os frames [f0, f1): logo abaixo do queixo; senão acima da cabeça."""
    if faces is None: return (H - block_h) / 2, "centro (sem rosto detectado)"
    seg = faces[f0:max(f0 + 1, f1)]
    chin = float((seg[:, 1] + seg[:, 3]).max())
    head = float((seg[:, 1] - 0.45 * seg[:, 3]).min())
    below = chin + MARGEM_QUEIXO
    if below + block_h <= LIMITE_BAIXO: return below, "abaixo do queixo"
    above = head - 30 - block_h
    if above >= LIMITE_CIMA: return above, "acima da cabeça"
    return None, None

def face_rect(faces, i):
    if faces is None: return None
    x, y, w, h = faces[min(i, len(faces) - 1)]
    return (x - 0.15 * w, y - 0.45 * h, x + 1.15 * w, y + h + 20)

# ------------------------------------------------------------------ render
def render(video, cfg, out_base, modo, previa, faces, fps, n_frames):
    telas = cfg["telas"]; chamada = cfg.get("chamada")
    dur = n_frames / fps
    # agrupamento: última tela fica até o fim e recebe a chamada embaixo
    scale = 1.0
    while True:
        built = [build_screen(t, scale) for t in telas]
        call = box(chamada["texto"], CALL_SIZE * scale, BLACK, LIME, weight=600, hmul=1.5, outline=LIME) if chamada else None
        plans, fail = [], False
        for k, t in enumerate(telas):
            last = k == len(telas) - 1
            f0 = int(t["inicio"] * fps); f1 = n_frames if last else int(t["fim"] * fps)
            bh = stack_h(built[k]) + ((16 + call[1] + 26) if (last and call) else 0)
            top, where = choose_top(faces, f0, f1, bh)
            if top is None: fail = True; break
            plans.append((top, where))
        if not fail or scale < 0.6: break
        scale -= 0.07
    if fail:
        print("  AVISO: sem espaço livre fora do rosto. Texto encostado embaixo. Use --enquadramento ajustar.")
        plans = []
        for k, b in enumerate(built):
            bh = stack_h(b) + ((16 + call[1] + 26) if (k == len(built) - 1 and call) else 0)
            plans.append((LIMITE_BAIXO - bh, "embaixo (sem espaço livre)"))
    for k, (top, where) in enumerate(plans): print(f"  tela {k + 1}: y={top:.0f} ({where}), escala {scale:.2f}")
    bar = barra(call[0].width - 20) if call else None

    def overlay(i):
        t = i / fps; ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        k = max([j for j, tl in enumerate(telas) if t >= tl["inicio"]] or [0])
        last = k == len(telas) - 1
        lt = t - telas[k]["inicio"]
        out = 1.0 if last else clamp((telas[k]["fim"] - t) / 0.1)
        y = plans[k][0]
        for n, (im, h) in enumerate(built[k]):
            u = (lt - n * 0.09) / 0.22
            if u > 0:
                e = ease(u); place(ov, im, W / 2, y + h / 2 + (1 - e) * 40, 0.94 + 0.06 * e, clamp(u * 3) * out)
            y += h + GAP
        if last and call and t >= chamada["inicio"]:
            u = (t - chamada["inicio"]) / 0.25; e = ease(u)
            place(ov, call[0], W / 2, y + 10 + call[1] / 2 + (1 - e) * 40, 0.94 + 0.06 * e, clamp(u * 3))
            place(ov, bar, W / 2, y + 10 + call[1] + 16, 1.0, clamp((t - chamada["inicio"] - 0.2) / 0.2))
        return ov

    modos = ["cor", "pb"] if modo == "ambos" else [modo]
    snaps_at = sorted({min(n_frames - 1, int((tl["inicio"] + min(1.2, (tl.get("fim", dur) - tl["inicio"]) * 0.6)) * fps)) for tl in telas} | {n_frames - 1})
    for m in modos:
        out = f"{out_base}_{m}.mp4"
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", f"{fps:.5f}", "-i", "-",
               "-i", video, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        viol, snaps = 0, []
        for i, fr in enumerate(frames(video)):
            rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
            if m == "pb":
                g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
                rgb = cv2.cvtColor(np.clip((g - 128) * 1.12 + 124, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)
            ov = overlay(i)
            bb = ov.getchannel("A").point(lambda v: 255 if v > 10 else 0).getbbox()
            fr_ = face_rect(faces, i)
            if bb and fr_ and not (bb[3] <= fr_[1] or bb[1] >= fr_[3] or bb[2] <= fr_[0] or bb[0] >= fr_[2]): viol += 1
            img = Image.fromarray(rgb).convert("RGBA"); img.alpha_composite(ov); img = img.convert("RGB")
            if previa and i in snaps_at: snaps.append(img.resize((540, 960)))
            p.stdin.write(img.tobytes())
        p.stdin.close(); p.wait()
        print(f"{out}: pronto | frames com texto sobre o rosto: {viol}")
        if previa and snaps:
            sheet = Image.new("RGB", (540 * len(snaps), 960))
            for j, s in enumerate(snaps): sheet.paste(s, (540 * j, 0))
            sheet.save(f"{out_base}_previa_{m}.png"); print(f"  prévia: {out_base}_previa_{m}.png")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("roteiro"); ap.add_argument("saida")
    ap.add_argument("--modo", choices=["cor", "pb", "ambos"], default="ambos")
    ap.add_argument("--previa", action="store_true")
    ap.add_argument("--enquadramento", choices=["auto", "preencher", "ajustar"], default="auto")
    a = ap.parse_args()
    global ENQUADRAMENTO; ENQUADRAMENTO = a.enquadramento
    cfg = json.load(open(a.roteiro, encoding="utf-8"))
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    print("detectando rosto...")
    raw = detect_faces(a.video)
    faces = clean_faces(raw)
    n = len(raw)
    print(f"  {n} frames, {fps:.2f} fps, rosto em {sum(b is not None for b in raw)} frames")
    os.makedirs(os.path.dirname(os.path.abspath(a.saida)), exist_ok=True)
    render(a.video, cfg, a.saida, a.modo, a.previa, faces, fps, n)

if __name__ == "__main__":
    main()
