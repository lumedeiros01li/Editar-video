#!/usr/bin/env python3
"""
Áudio do Reel animado: voz limpa + trilha sintetizada + efeitos, mix em -14 LUFS.

Uso:
    python audio.py plano_resolvido.json [--saida audio_final.wav] [--so-trilha]

A trilha é composta em código na mesma grade de batidas do beats.json, então
todo acerto (troca de cena, entrada de elemento) cai numa semicolcheia da música.
Mesma entrada, mesmo áudio: todo ruído tem semente.
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



# ------------------------------------------------------------ trilha
NOTAS = {"A2": 110.0, "C3": 130.81, "D3": 146.83, "E3": 164.81, "F2": 87.31, "G2": 98.0,
         "F3": 174.61, "G3": 196.0, "A3": 220.0, "B3": 246.94, "C4": 261.63, "D4": 293.66,
         "E4": 329.63, "F4": 349.23, "G4": 392.0, "A4": 440.0}
# vi - IV - I - V em lá menor / dó maior: calmo, sem resolver, bom para fala por cima
PROGRESSAO = [("A2", ["A3", "C4", "E4"]), ("F2", ["F3", "A3", "C4"]),
              ("C3", ["G3", "C4", "E4"]), ("G2", ["G3", "B3", "D4"])]


def onda(freq, t, harm=6, detune=0.0):
    f = freq * (2 ** (detune / 1200))
    return sum(np.sin(2 * np.pi * f * h * t) / h for h in range(1, harm + 1))


def trilha(dur, bpm, estilo, semente="trilha"):
    r = rng_de(semente)
    n = int(dur * SR)
    out = np.zeros(n + SR)
    beat = 60.0 / bpm
    compasso = 4 * beat
    n_comp = int(np.ceil(dur / compasso)) + 1

    def soma(som, t0):
        colar(out, som, t0)

    for b in range(n_comp):
        t0 = b * compasso
        raiz, acorde = PROGRESSAO[b % 4]
        # pad: acorde sustentado com ataque lento
        tt = _t(compasso + 0.6)
        env = np.minimum(1, tt / 0.45) * np.exp(-np.maximum(0, tt - compasso) / 0.25)
        pad = sum(onda(NOTAS[nt], tt, 5, -4) + onda(NOTAS[nt], tt, 5, 4) for nt in acorde)
        soma(pad * env * 0.05, t0)
        if b == 0:
            continue
        # baixo nos tempos 1 e 3
        for k, d in ((0, 1.6), (2, 0.9)):
            tb = _t(d * beat)
            sb = (np.sin(2 * np.pi * NOTAS[raiz] * tb) + 0.3 * np.sin(4 * np.pi * NOTAS[raiz] * tb))
            soma(_ataque(sb * np.exp(-tb / (0.6 * d * beat)), 6) * 0.32, t0 + k * beat)
        # arpejo em colcheias, uma oitava acima
        for k in range(8):
            nt = acorde[[0, 1, 2, 1][k % 4]]
            tp = _t(0.45)
            f = NOTAS[nt] * 2
            sp = (np.sin(2 * np.pi * f * tp) + 0.18 * np.sin(6 * np.pi * f * tp)) * np.exp(-tp / 0.16)
            soma(_ataque(sp, 3) * (0.07 if k % 2 else 0.1), t0 + k * beat / 2)
        if estilo == "pulso":
            for k in (0, 2):
                tk = _t(0.3)
                fk = 45 + 80 * np.exp(-tk / 0.035)
                soma(np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tk / 0.11) * 0.45, t0 + k * beat)
            for k in range(8):
                if k % 2:
                    ruido = np.diff(r.standard_normal(int(0.05 * SR) + 1))
                    soma(ruido * np.exp(-_t(0.05) / 0.012) * 0.035, t0 + k * beat / 2)
    out = out[:n]
    fade = int(1.4 * SR)
    out[-fade:] *= np.linspace(1, 0, fade) ** 2
    return out


# ------------------------------------------------------------ efeitos por elemento
def moeda(rng, pico=-30):
    t = _t(0.12)
    x = (np.sin(2 * np.pi * 2600 * t) + 0.6 * np.sin(2 * np.pi * 3900 * t)) * np.exp(-t / 0.03)
    return _norm(_ataque(x, 0.5), pico)


def efeitos(plano, dur, ajuste_db):
    tr = np.zeros(int(dur * SR) + SR)
    g = db(ajuste_db)
    for k, c in enumerate(plano["cenas"]):
        r = rng_de(c["id"])
        if k > 0:
            if c.get("transicao", "corte") == "corte":
                colar(tr, clique(r, -27) * g, c["inicio"])
            else:
                colar(tr, whoosh(r, 0.42, -25) * g, c["inicio"] - 0.12)
        for e in c["elementos"]:
            r = rng_de(e["id"])
            t0, tipo = e["inicio"], e["tipo"]
            if tipo == "frase" and e.get("tamanho") == "g":
                colar(tr, impacto(r, -22) * g, t0 + 0.02)
            elif tipo == "numero":
                colar(tr, pop(-21) * g, t0 + 0.04)
                if e.get("contar", True) is not False:
                    for q in range(1, 9):
                        u = -np.log2(1 - q / 9 * (1 - 2 ** -10)) / 10
                        colar(tr, clique(r, -31) * g, t0 + 0.1 + u * e.get("contagem", 0.9))
            elif tipo == "icone":
                colar(tr, pop(-22) * g, t0 + 0.02)
            elif tipo == "personagem":
                colar(tr, pop(-22) * g, t0 + 0.05)
                if e.get("balao"):
                    colar(tr, pop(-25) * g, e.get("balao_em", t0 + 0.6))
            elif tipo == "cta":
                colar(tr, sino(-22) * g, t0 + 0.05)
            for it in e.get("itens", []):
                colar(tr, (pop(-24) if tipo == "icones" else clique(r, -24)) * g, it["em"] + 0.04)
            for ln in e.get("linhas", []):
                colar(tr, subida(0.6, -29) * g, ln["em"])
                colar(tr, pop(-25) * g, ln["em"] + 0.7)
            for m in e.get("marcos", []):
                colar(tr, pop(-25) * g, m["em"] + 0.03)
            for s in e.get("segmentos", []):
                colar(tr, subida(0.5, -30) * g, s["em"])
            for col in e.get("colunas", []):
                n = max(1, min(22, col.get("moedas", 5)))
                passo = min(0.09, 1.3 / n)
                for q in range(0, n, max(1, n // 10)):
                    colar(tr, moeda(r, -30) * g, col["em"] + q * passo + 0.3)
            if tipo == "grafico":
                dd = e.get("desenho", 1.6)
                colar(tr, subida(dd, -30) * g, t0 + 0.3)
                colar(tr, pop(-22) * g, t0 + 0.3 + dd)
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
    ap.add_argument("--so-trilha", action="store_true", help="gera só a trilha, para ouvir o clima")
    a = ap.parse_args()
    plano = json.load(open(a.plano, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(a.plano))
    saida = a.saida or os.path.join(base, "audio_final.wav" if not a.so_trilha else "trilha.wav")
    dur = float(plano["duracao"])
    n = int(dur * SR)

    voz = np.zeros(n)
    v = ler_audio(plano["audio"])[:n]
    voz[:len(v)] = v
    mix = np.zeros(n) if a.so_trilha else voz.copy()

    m = plano.get("musica", {})
    if m.get("ativa", True):
        mus = trilha(dur, float(m.get("bpm", 96)), m.get("estilo", "pulso"))
        mus = mus / (np.sqrt(np.mean(mus[mus != 0] ** 2)) + 1e-9) * db(float(m.get("volume", -28)))
        mix += mus if a.so_trilha else abaixar_sob_voz(mus, voz)
    if plano.get("sfx", True) and not a.so_trilha:
        mix += efeitos(plano, dur, float(plano.get("volume_sfx", 0)))[:n]

    tmp = tempfile.NamedTemporaryFile(suffix=".f32", delete=False)
    tmp.write(np.clip(mix, -1, 1).astype(np.float32).tobytes())
    tmp.close()
    wav = tmp.name + ".wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1",
                    "-i", tmp.name, wav], check=True)
    loudnorm(wav, saida, -14)
    os.unlink(tmp.name)
    os.unlink(wav)
    print(f"Áudio: {saida}  ({dur:.1f}s, trilha {'ligada' if m.get('ativa', True) else 'desligada'}, "
          f"{m.get('bpm', 96)} bpm, estilo {m.get('estilo', 'pulso')})")


if __name__ == "__main__":
    main()
