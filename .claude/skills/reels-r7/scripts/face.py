"""Detecta o rosto (mediapipe) em quadros já ajustados para 1080x1920.
Uso: python3 face.py <pasta_de_quadros> <modelo.tflite> <saida.json>
Saída: union (caixa única), zona (+40 px), proibida (topo da caixa até 85% da altura, com a margem lateral).
"""
import sys, json, glob, os
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision

frames_dir, model, out = sys.argv[1:4]
det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
    base_options=mpt.BaseOptions(model_asset_path=model), min_detection_confidence=0.5))
boxes, miss = [], []
for f in sorted(glob.glob(os.path.join(frames_dir, '*.png'))):
    img = mp.Image.create_from_file(f)
    r = det.detect(img)
    if not r.detections:
        miss.append(os.path.basename(f)); continue
    b = max(r.detections, key=lambda d: d.bounding_box.width * d.bounding_box.height).bounding_box
    boxes.append([os.path.basename(f), b.origin_x, b.origin_y, b.origin_x + b.width, b.origin_y + b.height])
res = {'quadros': len(boxes) + len(miss), 'sem_rosto': miss, 'boxes': boxes}
if boxes:
    x1 = max(0, min(b[1] for b in boxes)); y1 = max(0, min(b[2] for b in boxes))
    x2 = min(1080, max(b[3] for b in boxes)); y2 = min(1920, max(b[4] for b in boxes))
    res.update(union=[x1, y1, x2, y2], zona=[x1 - 40, y1 - 40, x2 + 40, y2 + 40],
               proibida=[x1 - 40, y1, x2 + 40, round(y1 + 0.85 * (y2 - y1))])
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'boxes'}))
os._exit(0)  # evita erro do mediapipe ao fechar
