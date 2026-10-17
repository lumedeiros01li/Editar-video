#!/usr/bin/env python3
"""
Monta o áudio final: voz + efeitos sintetizados em código (+ música, se houver).

Uso:
    python audio.py plano_resolvido.json [--saida audio_final.wav] [--sem-sfx]

Cada efeito cai no instante exato em que o elemento visual entra (o plano já
ancora os eventos nas palavras). Ruído sempre com semente: o mesmo plano gera
sempre o mesmo áudio. Saída normalizada em -14 LUFS, pico -1,5 dBTP.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import zlib

import numpy as np

SR = 48000


def db(x):
    return 10 ** (x / 20)


def rng_de(chave):
    return np.random.default_rng(zlib.crc32(str(chave).encode()))


def ler_audio(path):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        sys.exit("ERRO lendo áudio: " + p.stderr.decode()[-800:])
    return np.frombuffer(p.stdout, dtype=np.float32).astype(np.float64)


# ------------------------------------------------------------ síntese
def _t(d):
    return np.arange(int(d * SR)) / SR


def _norm(x, pico_db):
    m = np.max(np.abs(x)) or 1.0
    return x / m * db(pico_db)


def _ataque(x, ms=2):
    n = max(1, int(ms * SR / 1000))
    x[:n] *= np.linspace(0, 1, n)
    return x


def pop(pico=-22):
    t = _t(0.09)
    f = 520 + 520 * (1 - np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.025)
    return _norm(_ataque(x), pico)


def clique(rng, pico=-26):
    t = _t(0.03)
    x = np.sin(2 * np.pi * 2100 * t) * np.exp(-t / 0.006)
    x[:150] += np.diff(rng.standard_normal(151)) * 0.3
    return _norm(_ataque(x, 0.5), pico)


def whoosh(rng, d=0.34, pico=-26, f0=350, f1=4200):
    n = int(d * SR)
    ruido = rng.standard_normal(n)
    u = np.linspace(0, 1, n)
    corte = f0 + (f1 - f0) * np.sin(np.pi * u) ** 1.5
    a = np.exp(-2 * np.pi * corte / SR)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):          # passa-baixa de um polo com corte variável
        acc = (1 - a[i]) * ruido[i] + a[i] * acc
        y[i] = acc
    y *= np.sin(np.pi * u) ** 2
    return _norm(y, pico)


def impacto(rng, pico=-18):
    t = _t(0.32)
    f = 45 + 75 * np.exp(-t / 0.05)
    corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09)
    ataque = np.zeros_like(t)
    k = int(0.012 * SR)
    ataque[:k] = rng.standard_normal(k) * np.exp(-np.arange(k) / (0.003 * SR)) * 0.5
    return _norm(_ataque(corpo + ataque, 1), pico)


def subida(d=0.5, pico=-28):
    t = _t(d)
    f = 300 + 420 * (t / d) ** 1.4
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2
    return _norm(x, pico)


def sino(pico=-22):
    t = _t(0.6)
    x = (np.sin(2 * np.pi * 880 * t) + 0.6 * np.sin(2 * np.pi * 1320 * t)) * np.exp(-t / 0.18)
    return _norm(_ataque(x, 3), pico)


def colar(trilha, som, t):
    i = int(round(t * SR))
    if i >= len(trilha) or i + len(som) <= 0:
        return
    a, b = max(i, 0), min(i + len(som), len(trilha))
    trilha[a:b] += som[a - i:b - i]


def efeitos(plano, dur, ajuste_db):
    tr = np.zeros(int(dur * SR) + SR)
    g = db(ajuste_db)
    for ev in plano["eventos"]:
        r = rng_de(ev["id"])
        t0, tipo = ev["inicio"], ev["tipo"]
        if tipo == "titulo":
            colar(tr, whoosh(r, 0.32, -27) * g, t0 - 0.08)
        elif tipo == "palavra":
            colar(tr, whoosh(r, 0.22, -28, 600, 5000) * g, t0 - 0.16)
            colar(tr, impacto(r) * g, t0 + 0.04)
        elif tipo == "numero":
            colar(tr, pop(-21) * g, t0 + 0.02)
            if ev.get("contar", True) is not False:
                dur_c = ev.get("contagem", 0.9)
                for k in range(1, 9):   # ticks seguindo a curva de contagem (outExpo)
                    u = -np.log2(1 - k / 9 * (1 - 2 ** -10)) / 10
                    colar(tr, clique(r, -30) * g, t0 + 0.1 + u * dur_c)
        elif tipo == "lista":
            colar(tr, whoosh(r, 0.28, -29) * g, t0 - 0.05)
            for it in ev.get("itens", []):
                colar(tr, clique(r, -24) * g, it["em"] + 0.06)
        elif tipo == "comparacao":
            colar(tr, whoosh(r, 0.28, -29) * g, t0 - 0.05)
            for ln in ev.get("linhas", []):
                colar(tr, subida(0.6, -29) * g, ln["em"])
                colar(tr, pop(-25) * g, ln["em"] + 0.62)
        elif tipo == "grafico":
            dd = ev.get("desenho", 1.4)
            colar(tr, whoosh(r, 0.28, -29) * g, t0 - 0.05)
            colar(tr, subida(dd, -30) * g, t0 + 0.3)
            colar(tr, pop(-22) * g, t0 + 0.3 + dd)
        elif tipo == "emoji":
            colar(tr, pop(-23) * g, t0 + 0.02)
        elif tipo == "cta":
            colar(tr, sino(-23) * g, t0 + 0.05)
        elif tipo == "zoom" and ev.get("modo") == "seco":
            colar(tr, whoosh(r, 0.18, -31, 800, 3000) * g, t0 - 0.06)
    return tr


def abaixar_sob_voz(musica, voz):
    """Ducking: música cai 9 dB enquanto há fala (ataque 40 ms, soltura 350 ms)."""
    jan = int(0.03 * SR)
    pot = np.convolve(voz ** 2, np.ones(jan) / jan, "same")
    fala = (10 * np.log10(pot + 1e-12) > -45).astype(float)
    ganho = np.empty_like(fala)
    a_at, a_sol = np.exp(-1 / (0.04 * SR)), np.exp(-1 / (0.35 * SR))
    g = 0.0
    for i, v in enumerate(fala):
        a = a_at if v > g else a_sol
        g = a * g + (1 - a) * v
        ganho[i] = g
    return musica * db(-9 * ganho)


def loudnorm(entrada, saida, alvo=-14):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", entrada, "-af",
                        f"loudnorm=I={alvo}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr.decode("utf-8", "replace"), re.S)
    filtro = f"loudnorm=I={alvo}:TP=-1.5:LRA=11"
    if m:
        d = json.loads(m.group(0))
        filtro += (f":measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}"
                   f":measured_thresh={d['input_thresh']}:offset={d['target_offset']}:linear=true")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", entrada, "-af", filtro + ",aresample=48000",
                        "-ac", "2", "-c:a", "pcm_s16le", saida], stderr=subprocess.PIPE)
    if r.returncode != 0:
        sys.exit("ERRO na normalização: " + r.stderr.decode()[-800:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plano")
    ap.add_argument("--saida")
    ap.add_argument("--sem-sfx", action="store_true")
    a = ap.parse_args()

    plano = json.load(open(a.plano, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(a.plano))
    saida = a.saida or os.path.join(base, "audio_final.wav")
    cfg = plano.get("audio", {})

    voz = ler_audio(plano["video"])
    dur = len(voz) / SR
    mix = voz.copy()
    n_sfx = 0
    if cfg.get("sfx", True) and not a.sem_sfx:
        tr = efeitos(plano, dur, float(cfg.get("volume_sfx", 0)))[:len(voz)]
        n_sfx = int(np.count_nonzero(np.abs(np.diff(np.sign(tr))) > 0) > 0)
        mix += tr
    if cfg.get("musica"):
        mp = cfg["musica"] if os.path.isabs(cfg["musica"]) else os.path.join(base, cfg["musica"])
        mus = ler_audio(mp)
        if len(mus) < len(voz):
            mus = np.tile(mus, int(np.ceil(len(voz) / len(mus))))
        mus = mus[:len(voz)]
        mus = mus / (np.sqrt(np.mean(mus ** 2)) + 1e-9) * db(float(cfg.get("volume_musica", -30)))
        fade = int(1.5 * SR)
        mus[-fade:] *= np.linspace(1, 0, fade)
        mix += abaixar_sob_voz(mus, voz)

    tmp = tempfile.NamedTemporaryFile(suffix=".f32", delete=False)
    tmp.write(np.clip(mix, -1, 1).astype(np.float32).tobytes())
    tmp.close()
    wav = tmp.name + ".wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1",
                    "-i", tmp.name, wav], check=True)
    loudnorm(wav, saida, float(cfg.get("lufs", -14)))
    os.unlink(tmp.name)
    os.unlink(wav)
    print(f"Áudio final: {saida}  ({dur:.1f}s, efeitos {'ligados' if n_sfx else 'desligados'}"
          f"{', com música' if cfg.get('musica') else ''})")


if __name__ == "__main__":
    main()
