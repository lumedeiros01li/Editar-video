"""Detecta rosto e mascara da pessoa por frame. Uso: r7_face.py video.mp4 modelos_dir saida.npz"""
import sys, numpy as np, cv2, mediapipe as mp
from mediapipe.tasks import python as mpp
from mediapipe.tasks.python import vision

vid, mdir, out = sys.argv[1:4]
cap = cv2.VideoCapture(vid)
det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
    base_options=mpp.BaseOptions(model_asset_path=mdir + "/face.tflite"), min_detection_confidence=0.3))
seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
    base_options=mpp.BaseOptions(model_asset_path=mdir + "/seg.tflite"), output_confidence_masks=True, output_category_mask=False))
boxes, masks = [], []
last = None
while True:
    ok, fr = cap.read()
    if not ok: break
    h, w = fr.shape[:2]
    small = cv2.resize(fr, (w // 2, h // 2))
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
    r = det.detect(img)
    if r.detections:
        b = max(r.detections, key=lambda d: d.bounding_box.width).bounding_box
        last = [b.origin_x * 2, b.origin_y * 2, b.width * 2, b.height * 2]
    boxes.append(last if last else [0, 0, 0, 0])
    s = seg.segment(img).confidence_masks[0].numpy_view()
    masks.append((cv2.resize(np.squeeze(s), (270, 480)) * 255).astype(np.uint8))
np.savez_compressed(out, boxes=np.array(boxes, dtype=np.float32), masks=np.array(masks))
b = np.array(boxes)
print(len(b), "frames | rosto: x", b[:, 0].min(), "-", (b[:, 0] + b[:, 2]).max(), "| y", b[:, 1].min(), "-", (b[:, 1] + b[:, 3]).max())
