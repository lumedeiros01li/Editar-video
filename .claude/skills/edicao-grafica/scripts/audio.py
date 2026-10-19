#!/usr/bin/env python3
"""
Monta o áudio final: voz + efeitos sintetizados em código (+ música, se houver).

Uso:
    python audio.py plano_resolvido.json [--saida audio_final.wav] [--sem-sfx]

Cada efeito cai no instante exato em que o elemento visual entra (o plano já
ancora os eventos nas palavras). Os efeitos seguem o estilo: Blueprint usa
clique de lápis e risco de caneta, Brutalista usa batida grave em cada cartão. Ruído sempre com semente: o mesmo plano gera
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


def lapis(rng, pico=-26):
    """Clique de lápis no papel: ruído agudo muito curto com um toque de grafite."""
    n = int(0.035 * SR)
    t = np.arange(n) / SR
    x = np.diff(rng.standard_normal(n + 1)) * np.exp(-t / 0.005)
    x += 0.4 * np.sin(2 * np.pi * 3300 * t) * np.exp(-t / 0.004)
    return _norm(_ataque(x, 0.3), pico)


def risco(rng, d=0.45, pico=-32):
    """Caneta riscando o papel: ruído agudo com o vai e vem do traço."""
    n = int(d * SR)
    t = np.arange(n) / SR
    x = np.diff(rng.standard_normal(n + 1))
    x *= (0.55 + 0.45 * np.sin(2 * np.pi * 9 * t) ** 2) * np.sin(np.pi * t / d) ** 0.6
    return _norm(x, pico)


CARTOES = {"numero", "lista", "comparacao", "grafico", "conta", "titulo", "cta"}


def efeitos(plano, dur, ajuste_db):
    tr = np.zeros(int(dur * SR) + SR)
    g = db(ajuste_db)
    br = plano.get("estilo") == "brutalista"

    def put(som, t):
        colar(tr, som * g, t)

    for ev in plano["eventos"]:
        r = rng_de(ev["id"])
        t0, tipo = ev["inicio"], ev["tipo"]
        if br:
            if tipo in CARTOES:
                put(impacto(r, -19), t0)
            if tipo == "palavra":
                put(whoosh(r, 0.14, -28, 900, 5000), t0 - 0.08)
                put(impacto(r, -17), t0 + 0.02)
            elif tipo == "carimbo":
                put(impacto(r, -15), t0)
                put(clique(r, -22), t0 + 0.01)
            elif tipo == "sticker":
                put(pop(-22), t0)
            elif tipo == "numero" and ev.get("contar", True) is not False:
                for q in range(1, 7):
                    put(clique(r, -29), t0 + 0.1 + (q - 1) * 0.5 / 6)
            elif tipo == "emoji":
                put(pop(-23), t0)
            elif tipo == "cta":
                put(sino(-27), t0 + 0.06)
            elif tipo == "zoom" and ev.get("modo") == "seco":
                put(impacto(r, -25), t0)
            for it in ev.get("itens", []) + ev.get("linhas", []):
                put(impacto(r, -26), it["em"])
                put(clique(r, -27), it["em"] + 0.005)
        else:
            if tipo == "titulo":
                put(risco(r, 0.36, -31), t0 + 0.02)
            elif tipo == "palavra":
                put(whoosh(r, 0.3, -29, 300, 2600), t0 - 0.12)
                put(risco(r, 0.32), t0 + 0.12 + 0.028 * len(str(ev.get("texto", ""))))
            elif tipo == "numero":
                put(lapis(r, -24), t0 + 0.1)
                dc = ev.get("contagem", 0.9)
                if ev.get("contar", True) is not False:
                    for k in range(1, 9):   # ticks seguindo a curva de contagem (outExpo)
                        u = -np.log2(1 - k / 9 * (1 - 2 ** -10)) / 10
                        put(clique(r, -33), t0 + 0.1 + u * dc)
                if ev.get("caneta", True) is not False:
                    put(risco(r, 0.32), t0 + (0.1 + dc if ev.get("contar", True) is not False else 0.5))
            elif tipo == "conta":
                put(lapis(r, -27), t0)
                for ln in ev.get("linhas", []):
                    atraso = 0.16 if ln.get("resultado") else 0.0
                    put(lapis(r, -24), ln["em"] + atraso)
                    if ln.get("resultado") and ev.get("caneta", True) is not False:
                        n = len(str(ln.get("rotulo", "")) + str(ln["valor"])) if "valor" in ln else len(str(ln.get("texto", "")))
                        put(risco(r, 0.5), ln["em"] + atraso + min(0.42, 0.05 + n * 0.022) + 0.08)
            elif tipo == "lista":
                put(lapis(r, -27), t0)
                for it in ev.get("itens", []):
                    put(lapis(r, -24), it["em"] + 0.06)
            elif tipo == "comparacao":
                put(lapis(r, -27), t0)
                for ln in ev.get("linhas", []):
                    put(subida(0.6, -30), ln["em"])
                    put(lapis(r, -25), ln["em"] + 0.62)
            elif tipo == "grafico":
                dd = ev.get("desenho", 1.4)
                put(lapis(r, -27), t0)
                put(subida(dd, -31), t0 + 0.3)
                put(risco(r, 0.5), t0 + 0.6 + dd)
            elif tipo == "emoji":
                put(pop(-25), t0 + 0.02)
            elif tipo == "cta":
                put(sino(-24), t0 + 0.05)
            elif tipo == "zoom" and ev.get("modo") == "seco":
                put(whoosh(r, 0.18, -31, 800, 3000), t0 - 0.06)
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
    print(f"Áudio final: {saida}  ({dur:.1f}s, efeitos {plano.get('estilo', 'blueprint')} {'ligados' if n_sfx else 'desligados'}"
          f"{', com música' if cfg.get('musica') else ''})")


if __name__ == "__main__":
    main()
