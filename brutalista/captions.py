# Builds caption chunks (2-4 words) from whisper word timings
import json, re
W = json.load(open("build/words_raw.json"))
# merge "51" ",8" "%" style tokens
m = []
for w in W:
    if m and (w["w"].startswith(",") or w["w"] == "%"):
        m[-1]["w"] += w["w"]; m[-1]["e"] = w["e"]
    else: m.append(dict(w))
fix = {"Banco": "banco", "Central": "central", "Americano": "americano"}
for i, w in enumerate(m):
    w["w"] = fix.get(w["w"], w["w"])
    if w["w"] == "o" and i + 1 < len(m) and m[i + 1]["w"] == "Congresso": w["w"] = "um"
chunks, cur = [], []
for i, w in enumerate(m):
    cur.append(w)
    txt = " ".join(x["w"] for x in cur)
    nxt = m[i + 1] if i + 1 < len(m) else None
    gap = (nxt["s"] - w["e"]) if nxt else 9
    punct = re.search(r"[.,?!:]$", w["w"])
    if punct or gap > 0.28 or len(cur) >= 4 or len(txt) >= 17 or (nxt and len(txt) + len(nxt["w"]) > 20):
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
# merge orphan single words into the previous chunk
merged = []
for c in chunks:
    if merged and len(c) == 1:
        p = merged[-1]; pt = " ".join(x["w"] for x in p)
        if not re.search(r"[.,?!:]$", pt) and len(pt) + 1 + len(c[0]["w"]) <= 28 and c[0]["s"] - p[-1]["e"] < 0.3:
            p.extend(c); continue
    merged.append(c)
chunks = merged
out = []
for k, c in enumerate(chunks):
    s = c[0]["s"]; e = c[-1]["e"]
    nxt = chunks[k + 1][0]["s"] if k + 1 < len(chunks) else e + 0.8
    out.append({"s": round(s, 3), "e": round(min(nxt, e + 0.5), 3), "words": c})
json.dump(out, open("build/captions.json", "w"), ensure_ascii=False)
for o in out: print(f'{o["s"]:6.2f} {o["e"]:6.2f}  ' + " ".join(w["w"] for w in o["words"]))
