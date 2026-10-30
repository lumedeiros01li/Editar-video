"""Rastreia o rosto no video mestre (cx, cy normalizados 0-1, por frame a 30 fps) e salva face.json."""
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user-Editar-video/f47d3059-e524-5d1f-b347-acff40590d7d/scratchpad/cv4")
import cv2, json, numpy as np, subprocess
src, out = sys.argv[1], sys.argv[2]
W, H = 270, 480
cmd = ["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=10,scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
casc2 = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
res = []; last = None
while True:
    b = p.stdout.read(W * H)
    if len(b) < W * H: break
    g = cv2.equalizeHist(np.frombuffer(b, np.uint8).reshape(H, W))
    f = casc.detectMultiScale(g, 1.1, 5, minSize=(40, 40))
    if len(f) == 0: f = casc2.detectMultiScale(g, 1.1, 5, minSize=(40, 40))
    if len(f):
        x, y, w, h = max(f, key=lambda r: r[2] * r[3])
        last = (x + w / 2, y + h / 2, w)
        res.append((last[0] / W, last[1] / H, w / W))
    else: res.append(None)
ok = [i for i, r in enumerate(res) if r]
print("frames", len(res), "com rosto", len(ok))
arr = np.array([[r[0], r[1], r[2]] if r else [np.nan] * 3 for r in res])
idx = np.arange(len(arr))
for c in range(3):
    m = ~np.isnan(arr[:, c]); arr[:, c] = np.interp(idx, idx[m], arr[m, c])
json.dump({"fps": 10, "pts": arr.round(4).tolist()}, open(out, "w"))
