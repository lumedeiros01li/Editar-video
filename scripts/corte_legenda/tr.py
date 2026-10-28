import json
from faster_whisper import WhisperModel
m=WhisperModel("small",compute_type="int8")
import numpy as np
aud=np.fromfile("a.raw",dtype=np.int16).astype(np.float32)/32768
segs,info=m.transcribe(aud,language="pt",word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end} for w in s.words]})
json.dump(out,open("tr.json","w"),ensure_ascii=False)
for s in out: print(f"{s['start']:.2f}-{s['end']:.2f} {s['text']}")
