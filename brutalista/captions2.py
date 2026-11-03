import json, re
W = json.load(open("build/words2.json"))
m = []
for w in W:
    if m and (w["w"].startswith("-") or w["w"].startswith(",") or w["w"] == "%"):
        m[-1]["w"] += w["w"]; m[-1]["e"] = w["e"]
    else: m.append(dict(w))
out_w = []
for i, w in enumerate(m):
    out_w.append(w)
    if w["w"] == "eu" and i + 1 < len(m) and m[i + 1]["w"].startswith("explico"):   # "eu te explico" (como no texto do vídeo)
        nx = m[i + 1]; d = (nx["e"] - nx["s"]) * 0.22
        out_w.append({"w": "te", "s": round(nx["s"], 3), "e": round(nx["s"] + d, 3)}); nx["s"] = round(nx["s"] + d, 3)
m = out_w
json.dump(m, open("build/words2_fixed.json", "w"), ensure_ascii=False)
chunks, cur = [], []
for i, w in enumerate(m):
    cur.append(w); txt = " ".join(x["w"] for x in cur)
    nxt = m[i + 1] if i + 1 < len(m) else None
    gap = (nxt["s"] - w["e"]) if nxt else 9
    punct = re.search(r"[.,?!:]$", w["w"])
    if punct or gap > 0.28 or len(cur) >= 4 or len(txt) >= 17 or (nxt and len(txt) + len(nxt["w"]) > 20):
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
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
json.dump(out, open("build/captions2.json", "w"), ensure_ascii=False)
for o in out: print(f'{o["s"]:6.2f} {o["e"]:6.2f}  ' + " ".join(w["w"] for w in o["words"]))
