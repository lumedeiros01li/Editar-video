#!/usr/bin/env python3
"""
Transcreve o vídeo JÁ CORTADO com tempo por palavra (faster-whisper, roda local).

Uso:
    python transcrever.py video_cortado.mp4 [--modelo small|medium|large-v3] [--vocabulario "Tesouro IPCA+, LCA"]

Gera, ao lado do vídeo:
  transcricao.json  -> {"idioma": "pt", "palavras": [{"i", "texto", "ini", "fim", "prob"}]}
  transcricao.txt   -> uma palavra por linha com índice e tempo, para montar o plano

Na primeira execução o modelo é baixado (small ~ 0,5 GB, medium ~ 1,5 GB).
"""
import argparse
import json
import os
import sys

VOCAB = ("Lucas Medeiros, InvestSmart, XP, CDI, IPCA, Selic, Copom, CDB, LCI, LCA, CRI, CRA, "
         "FGC, Tesouro Direto, Tesouro Selic, Tesouro IPCA+, renda fixa, previdência, PGBL, VGBL, "
         "come-cotas, liquidez, reserva de emergência, juros compostos, dólar, imposto de renda.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--modelo", default="small")
    ap.add_argument("--vocabulario", default="")
    a = ap.parse_args()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("ERRO: instale com  pip install faster-whisper")

    modelo = WhisperModel(a.modelo, device="auto", compute_type="int8")
    prompt = VOCAB + (" " + a.vocabulario if a.vocabulario else "")
    segs, info = modelo.transcribe(
        a.video, language="pt", word_timestamps=True, beam_size=5,
        initial_prompt=prompt, condition_on_previous_text=False, vad_filter=False,
    )
    palavras = []
    for s in segs:
        for w in s.words or []:
            txt = w.word.strip()
            if not txt:
                continue
            ini = float(w.start)
            fim = max(float(w.end), ini + 0.05)
            if palavras and ini < palavras[-1]["fim"]:
                ini = palavras[-1]["fim"]
                fim = max(fim, ini + 0.05)
            palavras.append({"i": len(palavras), "texto": txt, "ini": round(ini, 3),
                             "fim": round(fim, 3), "prob": round(float(w.probability), 3)})

    pasta = os.path.dirname(os.path.abspath(a.video))
    json.dump({"idioma": "pt", "modelo": a.modelo, "palavras": palavras},
              open(os.path.join(pasta, "transcricao.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    with open(os.path.join(pasta, "transcricao.txt"), "w", encoding="utf-8") as f:
        for w in palavras:
            alerta = "  <- conferir" if w["prob"] < 0.6 else ""
            f.write(f"{w['i']:4d}  {w['ini']:7.2f}  {w['texto']}{alerta}\n")
    texto = " ".join(w["texto"] for w in palavras)
    print(f"{len(palavras)} palavras. Transcrição em {pasta}/transcricao.json e .txt")
    print(texto)


if __name__ == "__main__":
    main()
