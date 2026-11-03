# Vídeo 2: mantém as CORES originais das imagens. Só dá um leve acabamento (contraste/saturação)
# e cria os adesivos com borda branca.
import cv2, numpy as np, os, sys
CUT, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT + "/img", exist_ok=True)
rng = np.random.default_rng(11)

def grade(bgr, sat=1.10, con=1.06):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 255)
    im = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    return np.clip((im - 128) * con + 128, 0, 255).astype(np.uint8)

def photo(name, up=1.0):
    im = cv2.imread(f"{CUT}/{name}.jpg"); im = grade(im)
    if up != 1: im = cv2.resize(im, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
    cv2.imwrite(f"{OUT}/img/{name}.jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 93])

def sticker(name, border=14, scale=1.0):
    im = cv2.imread(f"{CUT}/{name}.png", cv2.IMREAD_UNCHANGED)
    if scale != 1: im = cv2.resize(im, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    pad = border + 6
    im = cv2.copyMakeBorder(im, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
    rgb, a = grade(im[..., :3]), im[..., 3].astype(np.float32) / 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * border + 1, 2 * border + 1))
    ab = cv2.GaussianBlur(cv2.dilate((a > 0.5).astype(np.uint8), k).astype(np.float32), (3, 3), 0)
    white = np.ones_like(rgb, np.float32) * np.array([250, 252, 253], np.float32)
    out = white * (1 - a[..., None]) + rgb.astype(np.float32) * a[..., None]
    cv2.imwrite(f"{OUT}/img/{name}.png", np.dstack([np.clip(out, 0, 255).astype(np.uint8), (ab * 255).astype(np.uint8)]))

# papel (igual ao vídeo 1)
w, h = 1080, 1920
base = np.ones((h, w, 3), np.float32) * np.array([214, 228, 236], np.float32) / 255
low = cv2.resize(rng.random((24, 14)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
fib = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 0.8)
streak = cv2.blur(rng.random((h, w)).astype(np.float32), (1, 41))
v = 1 + 0.05 * (low - 0.5) + 0.06 * (fib - 0.5) + 0.05 * (streak - 0.5)
yy, xx = np.mgrid[0:h, 0:w]; vig = 1 - 0.10 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
cv2.imwrite(OUT + "/img/paper.jpg", np.clip(base * (v * vig)[..., None] * 255, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])

for n in ["bc", "cong", "esp", "oil", "mapa", "tanker", "capitolio", "fed", "crowd_a", "lucas"]: photo(n, 1.15)
sticker("lucas_busto", scale=1.0); sticker("ship", border=10, scale=1.6)
print("ok")
