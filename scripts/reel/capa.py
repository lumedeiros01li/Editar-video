import sys, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, ".")
import elementos as ET
W, H = 1080, 1920
T = float(sys.argv[1]) if len(sys.argv) > 1 else 5.6          # tempo do mestre (video) do quadro
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(T), "-i", "master.mp4", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
fd = json.load(open("face.json")); pts = np.array(fd["pts"]); i = int(T * fd["fps"]); cx, cy = pts[i, 0] * W, pts[i, 1] * H
z = 1.0; cw, chh = W / z, H / z
left = min(max(cx - cw / 2, 0), W - cw); top = cy - 1120 / z
M = np.float32([[z, 0, -left * z], [0, z, -top * z]])
out = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
bl = cv2.GaussianBlur(out, (0, 0), 1.4); out = cv2.addWeighted(out, 1.55, bl, -0.55, 0)
lut = (255 * (np.arange(256) / 255.0) ** 1.45 * 0.92).clip(0, 255).astype(np.uint8); out = cv2.LUT(out, lut)
img = Image.fromarray(out[..., ::-1]).convert("RGBA")
ROXO, LIMA, BLK, WH, CINZA = ET.ROXO, ET.LIMA, ET.BLK, (255, 255, 255, 255), ET.CINZA
lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
# painel do titulo
px0, px1, py0, py1 = 44, W - 44, 380, 850
d.rectangle((px0 + 16, py0 + 16, px1 + 16, py1 + 16), fill=ROXO)
d.rectangle((px0, py0, px1, py1), fill=CINZA, outline=BLK, width=7)
ft = ET.mono(38); t = "[ REFORMA TRIBUTÁRIA ]"; tw = ET.tw(d, t, ft) + 60
d.rectangle((W / 2 - tw / 2, py0 + 30, W / 2 + tw / 2, py0 + 90), fill=LIMA, outline=BLK, width=5)
d.text((W / 2 - tw / 2 + 30, py0 + 38), t, font=ft, fill=BLK)
f1 = ET.inter("Black", 90); f2 = ET.inter("Black", 108)
ET.ctext(d, W / 2, py0 + 120, "O BRASIL PODE TER", f1, BLK)
ET.ctext(d, W / 2, py0 + 220, "O MAIOR IMPOSTO", f1, BLK)
wb = ET.tw(d, "DO MUNDO?", f2) + 60; bx = W / 2 - wb / 2; by = py0 + 325
d.rectangle((bx, by, bx + wb, by + 125), fill=ROXO, outline=BLK, width=6)
d.text((bx + 30, by + 2), "DO MUNDO?", font=f2, fill=WH)
lay = ET.shadow(lay, 0, (0, 0), 0) if False else lay
# faixa "SEGUE O LIDER" acima do painel
fs = ET.inter("Black", 58); st = "SEGUE O LÍDER"; sw = ET.tw(d, st, fs) + 90
sx = W / 2 - sw / 2
d.rectangle((sx + 12, 262 + 12, sx + sw + 12, 262 + 92 + 12), fill=LIMA)
d.rectangle((sx, 262, sx + sw, 262 + 92), fill=BLK, outline=BLK, width=6)
d.text((sx + 45, 262 + 8), st, font=fs, fill=WH)
# cartao 30%
cw_, ch_ = 640, 270; card = Image.new("RGBA", (cw_ + 60, ch_ + 60), (0, 0, 0, 0)); c = ImageDraw.Draw(card)
c.rectangle((38, 38, 38 + cw_, 38 + ch_), fill=LIMA)
c.rectangle((20, 20, 20 + cw_, 20 + ch_), fill=WH, outline=BLK, width=8)
c.text((56, 46), "[ CBS + IBS ]", font=ET.mono(36), fill=BLK)
fv = ET.inter("Black", 150); c.text((20 + cw_ / 2 - ET.tw(c, "30%", fv) / 2, 60), "30%", font=fv, fill=BLK)
fb = ET.mono(38); bt = "de imposto sobre consumo"; bw = ET.tw(c, bt, fb) + 44
c.rectangle((20 + cw_ - 36 - bw, 20 + ch_ - 66, 20 + cw_ - 36, 20 + ch_ - 18), fill=ROXO, outline=BLK, width=5)
c.text((20 + cw_ - 36 - bw + 22, 20 + ch_ - 59), bt, font=fb, fill=WH)
card = card.rotate(-4, resample=Image.BICUBIC, expand=True)
lay.alpha_composite(card, (int(W / 2 - card.width / 2), 1340))
img.alpha_composite(lay)
img.convert("RGB").save(sys.argv[2] if len(sys.argv) > 2 else "capa.png")
