#!/usr/bin/env python3
"""Substituto de transcrever.py quando o HuggingFace está bloqueado.
Usa Parakeet TDT 0.6b v3 (sherpa-onnx) e grava transcricao.json/.txt no mesmo formato.
Uso: python3 transcrever_parakeet.py audio.m4a pasta_modelo
"""
import json, os, subprocess, sys
import numpy as np
import sherpa_onnx

audio, mod = sys.argv[1], sys.argv[2]
SR = 16000
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     stdout=subprocess.PIPE, check=True).stdout
x = np.frombuffer(pcm, dtype=np.float32)

rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=f"{mod}/encoder.int8.onnx", decoder=f"{mod}/decoder.int8.onnx",
    joiner=f"{mod}/joiner.int8.onnx", tokens=f"{mod}/tokens.txt",
    model_type="nemo_transducer", num_threads=4, decoding_method="greedy_search")

# blocos de ~20 s cortados no ponto mais silencioso para não estourar o encoder
bloco, janela = 20 * SR, 2 * SR
cortes, ini = [0], 0
while len(x) - ini > bloco + janela:
    a = ini + bloco - janela
    e = np.convolve(x[a:a + 2 * janela] ** 2, np.ones(800), "same")
    ini = a + int(np.argmin(e))
    cortes.append(ini)
cortes.append(len(x))

toks = []
for a, b in zip(cortes[:-1], cortes[1:]):
    s = rec.create_stream()
    s.accept_waveform(SR, x[a:b])
    rec.decode_stream(s)
    r = s.result
    for t, ts in zip(r.tokens, r.timestamps):
        toks.append((t, ts + a / SR))

# junta tokens em palavras (sentencepiece: "▁" inicia palavra)
pal = []
for t, ts in toks:
    if t.startswith((" ", "▁")) or not pal:
        pal.append({"texto": t.lstrip(" ▁"), "ini": ts})
    else:
        pal[-1]["texto"] += t
pal = [p for p in pal if p["texto"].strip()]
dur = len(x) / SR
palavras = []
for k, p in enumerate(pal):
    prox = pal[k + 1]["ini"] if k + 1 < len(pal) else dur
    fim = min(prox, p["ini"] + 0.08 + 0.075 * len(p["texto"]))
    palavras.append({"i": k, "texto": p["texto"], "ini": round(p["ini"], 3),
                     "fim": round(max(fim, p["ini"] + 0.05), 3), "prob": 1.0})

pasta = os.path.dirname(os.path.abspath(audio))
json.dump({"idioma": "pt", "modelo": "parakeet-tdt-0.6b-v3", "palavras": palavras},
          open(os.path.join(pasta, "transcricao.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(pasta, "transcricao.txt"), "w", encoding="utf-8") as f:
    for w in palavras:
        f.write(f"{w['i']:4d}  {w['ini']:7.2f}  {w['texto']}\n")
print(len(palavras), "palavras")
print(" ".join(w["texto"] for w in palavras))
