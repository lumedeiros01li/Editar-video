import numpy as np, json
from faster_whisper import WhisperModel
a = np.fromfile("raw16.raw", dtype=np.int16).astype(np.float32) / 32768
m = WhisperModel("large-v3-turbo", compute_type="int8")
segs, _ = m.transcribe(a, language="pt", word_timestamps=True, condition_on_previous_text=False, beam_size=5, vad_filter=False)
out = []
for s in segs:
    out.append({"s": s.start, "e": s.end, "t": s.text, "w": [[w.word.strip(), round(w.start, 2), round(w.end, 2), round(w.probability, 2)] for w in s.words]})
    print(f"{s.start:.1f}-{s.end:.1f} {s.text}", flush=True)
json.dump(out, open("asr_raw.json", "w"), ensure_ascii=False)
