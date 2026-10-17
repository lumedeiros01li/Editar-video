#!/usr/bin/env python3
"""
Corta silêncios e respirações de um vídeo falado e entrega o Reel limpo.

Dependências: ffmpeg + ffprobe no PATH, Python 3.8+, numpy.

Uso básico:
    python cortar_silencios.py entrada.mp4
    python cortar_silencios.py entrada.mp4 -o saida.mp4 --min-silencio 0.3 --margem 0.05
    python cortar_silencios.py entrada.mp4 --analisar      # só mostra o plano de cortes

Como decide o que cortar:
 1. Extrai o áudio em 16 kHz mono e mede, a cada 10 ms, energia (dB),
    planicidade espectral (ruído x tom) e sonoridade (há vibração de voz?).
 2. Calcula o nível de fala e o piso de ruído do próprio vídeo e define o
    limiar de forma adaptativa (funciona com microfone de lapela ou celular).
 3. Trechos ativos sem vibração de voz, curtos e mais baixos que a fala
    são classificados como respiração e tratados como silêncio.
 4. Pausas maiores que --min-silencio são removidas, mantendo --margem
    de cada lado. Pausas menores ficam (são o ritmo natural da fala).
 5. Os pontos de corte são alinhados aos quadros do vídeo, cada trecho
    recebe micro fade de áudio (anti estalo) e o volume é normalizado
    em duas passadas para -14 LUFS.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import numpy as np
except ImportError:
    sys.exit("ERRO: numpy não está instalado. Rode: pip install numpy")

SR = 16000          # taxa de análise
HOP = 160           # 10 ms
WIN = 640           # 40 ms
NFFT = 1024
F0_MIN, F0_MAX = 70, 400   # faixa de frequência da voz humana falada


# ----------------------------------------------------------------- utilidades
def run(cmd, check=True):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode != 0:
        err = p.stderr.decode("utf-8", "replace")[-3000:]
        raise RuntimeError(f"Comando falhou: {' '.join(cmd[:6])}...\n{err}")
    return p


def checar_dependencias():
    faltando = [b for b in ("ffmpeg", "ffprobe") if shutil.which(b) is None]
    if faltando:
        sys.exit(
            "ERRO: não encontrei " + ", ".join(faltando) + " no PATH.\n"
            "  Mac:     brew install ffmpeg\n"
            "  Windows: winget install Gyan.FFmpeg  (depois feche e abra o terminal)"
        )


def versao_ffmpeg():
    out = run(["ffmpeg", "-version"]).stdout.decode("utf-8", "replace")
    m = re.search(r"ffmpeg version n?(\d+)", out)
    return int(m.group(1)) if m else 0


def fmt_t(s):
    m, s = divmod(max(s, 0), 60)
    return f"{int(m)}:{s:05.2f}"


# ----------------------------------------------------------------- leitura
def probe(path):
    out = run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", path,
    ]).stdout
    info = json.loads(out)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if a is None:
        sys.exit("ERRO: o arquivo não tem faixa de áudio.")
    dur = float(info["format"].get("duration") or a.get("duration") or 0)
    res = {"duracao": dur, "tem_video": v is not None}
    if v:
        w, h = int(v["width"]), int(v["height"])
        rot = 0
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = int(float(sd["rotation"]))
        rot = int(v.get("tags", {}).get("rotate", rot))
        if abs(rot) % 180 == 90:
            w, h = h, w
        num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1").split("/")
        fps = float(num) / float(den) if float(den) else 30.0
        if not (10 <= fps <= 120):
            fps = 30.0
        res.update({"largura": w, "altura": h, "fps": fps})
    return res


def extrair_audio(path):
    p = run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1",
             "-ar", str(SR), "-f", "f32le", "-"])
    x = np.frombuffer(p.stdout, dtype=np.float32).astype(np.float64)
    if x.size < WIN * 2:
        sys.exit("ERRO: áudio curto demais para análise.")
    return x


# ----------------------------------------------------------------- análise
def caracteristicas(x):
    """Retorna por quadro de 10 ms: energia (dB), planicidade, sonoridade."""
    x = np.concatenate([x, np.zeros(WIN)])
    n = 1 + (len(x) - WIN) // HOP
    janela = np.hanning(WIN)
    # autocorrelação da própria janela, para normalizar (método de Boersma)
    wspec = np.abs(np.fft.rfft(janela, NFFT)) ** 2
    wac = np.fft.irfft(wspec)[:NFFT // 2]
    wac = wac / wac[0]
    lag_min, lag_max = SR // F0_MAX, SR // F0_MIN
    freqs = np.fft.rfftfreq(NFFT, 1 / SR)
    banda = (freqs >= 150) & (freqs <= 7000)

    db = np.empty(n)
    flat = np.empty(n)
    voz = np.empty(n)
    passo = 2000
    vista = np.lib.stride_tricks.sliding_window_view(x, WIN)[::HOP][:n]
    for i in range(0, n, passo):
        f = np.array(vista[i:i + passo])
        db[i:i + passo] = 10 * np.log10(np.mean(f ** 2, axis=1) + 1e-12)
        f = f - f.mean(axis=1, keepdims=True)
        fw = f * janela
        spec = np.abs(np.fft.rfft(fw, NFFT, axis=1)) ** 2 + 1e-12
        sb = spec[:, banda]
        flat[i:i + passo] = np.exp(np.mean(np.log(sb), axis=1)) / np.mean(sb, axis=1)
        ac = np.fft.irfft(spec, axis=1)[:, :NFFT // 2]
        ac = ac / (ac[:, :1] + 1e-12)
        ac = ac[:, lag_min:lag_max] / wac[lag_min:lag_max]
        voz[i:i + passo] = ac.max(axis=1)
    return db, flat, voz


def corridas(mask):
    """Lista de (inicio, fim) em índices de quadro onde mask é True."""
    d = np.diff(np.concatenate([[0], mask.astype(np.int8), [0]]))
    ini = np.where(d == 1)[0]
    fim = np.where(d == -1)[0]
    return list(zip(ini, fim))


def planejar(x, dur, a):
    db, flat, voz = caracteristicas(x)
    t = lambda i: i * HOP / SR  # noqa: E731

    piso = float(np.percentile(db, 10))
    acima = db[db > piso + 10]
    fala = float(np.percentile(acima, 90)) if acima.size > 50 else float(np.percentile(db, 95))
    if a.limiar_db is not None:
        limiar = a.limiar_db
    else:
        limiar = max(piso + 8.0, fala - a.faixa_db)

    ativo = db > limiar
    sonoro = (voz > a.limiar_voz) & ativo

    runs = []
    respiracoes = []
    for i0, i1 in corridas(ativo):
        d = t(i1 - i0)
        if d < 0.04:          # estalo isolado
            continue
        frac_voz = float(sonoro[i0:i1].mean())
        nivel = float(np.percentile(db[i0:i1], 90))
        if a.respiracoes == "cortar":
            # respiração isolada: sem vibração de voz, curta e mais baixa que a fala
            if frac_voz < 0.12 and d <= 1.3 and nivel < fala - 4:
                respiracoes.append((t(i0), t(i1)))
                continue
            # respiração colada na fala: trecho surdo longo e baixo na borda
            j = i0
            while j < i1 and not sonoro[j]:
                j += 1
            if t(j - i0) >= a.resp_borda and np.mean(db[i0:j]) < fala - 10 and j < i1:
                respiracoes.append((t(i0), t(j)))
                i0 = j
            k = i1
            while k > i0 and not sonoro[k - 1]:
                k -= 1
            if t(i1 - k) >= a.resp_borda and np.mean(db[k:i1]) < fala - 10 and k > i0:
                respiracoes.append((t(k), t(i1)))
                i1 = k
        runs.append([t(i0), t(i1)])

    if not runs:
        sys.exit("ERRO: não detectei fala. Tente --faixa-db 45 ou --limiar-db -50.")

    # junta trechos separados por pausas curtas (ritmo natural)
    fundidos = [runs[0]]
    for r in runs[1:]:
        if r[0] - fundidos[-1][1] < a.min_silencio:
            fundidos[-1][1] = r[1]
        else:
            fundidos.append(r)

    # descarta "falas" curtas e isoladas que são ruído (batida, clique)
    fundidos = [r for r in fundidos if r[1] - r[0] >= a.min_fala]
    if not fundidos:
        sys.exit("ERRO: só encontrei ruídos curtos. Reduza --min-fala.")

    manter = []
    for s, e in fundidos:
        s, e = max(0.0, s - a.margem), min(dur, e + a.margem)
        if manter and s <= manter[-1][1]:
            manter[-1][1] = max(manter[-1][1], e)
        else:
            manter.append([s, e])

    cortes = []
    cursor = 0.0
    for s, e in manter:
        if s - cursor > 0.001:
            cortes.append([cursor, s])
        cursor = e
    if dur - cursor > 0.001:
        cortes.append([cursor, dur])

    def tipo(c):
        n_resp = sum(1 for r0, r1 in respiracoes if r0 < c[1] and r1 > c[0])
        return "respiração" if n_resp else "silêncio"

    return {
        "niveis_db": {"piso_ruido": round(piso, 1), "fala": round(fala, 1),
                      "limiar_usado": round(limiar, 1)},
        "manter": manter,
        "cortes": [{"inicio": round(c[0], 3), "fim": round(c[1], 3),
                    "duracao": round(c[1] - c[0], 3), "tipo": tipo(c)} for c in cortes],
        "respiracoes_detectadas": len(respiracoes),
    }


# ----------------------------------------------------------------- render
def medir_loudness(path, alvo):
    p = run(["ffmpeg", "-hide_banner", "-i", path, "-vn",
             "-af", f"loudnorm=I={alvo}:TP=-1.5:LRA=11:print_format=json",
             "-f", "null", "-"], check=False)
    err = p.stderr.decode("utf-8", "replace")
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        if float(d["input_i"]) < -70:   # áudio praticamente mudo
            return None
        return d
    except (ValueError, KeyError):
        return None


def alinhar_quadros(manter, fps, dur):
    out = []
    for s, e in manter:
        s = np.floor(s * fps) / fps
        e = min(np.ceil(e * fps), np.floor(dur * fps)) / fps
        if out and s <= out[-1][1]:
            out[-1][1] = e
        elif e - s >= 1.0 / fps:
            out.append([float(s), float(e)])
    return out


def montar_filtro(manter, info, a, loud):
    """Vídeo e áudio são concatenados em cadeias separadas.

    O vídeo é convertido para fps constante ANTES dos cortes, e os pontos de
    corte já estão alinhados a esse fps. Assim cada trecho de vídeo tem
    exatamente a duração do trecho de áudio e não há dessincronia acumulada,
    nem em vídeos de celular com fps variável.
    """
    n = len(manter)
    linhas = []
    if info["tem_video"]:
        rotulos = "".join(f"[s{i}]" for i in range(n))
        linhas.append(f"[0:v]fps={a.fps},split={n}{rotulos};")
        for i, (s, e) in enumerate(manter):
            # após o filtro fps a base de tempo é 1/fps, então pts = índice do quadro
            k0, k1 = int(round(s * a.fps)), int(round(e * a.fps))
            linhas.append(f"[s{i}]trim=start_pts={k0}:end_pts={k1},setpts=PTS-STARTPTS[v{i}];")
        linhas.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vc];")
        if a.formato == "reels":
            vf = ("scale=1080:1920:force_original_aspect_ratio=increase,"
                  "crop=1080:1920,setsar=1")
        else:
            vf = "scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1"
        linhas.append(f"[vc]{vf},format=yuv420p[vout];")

    rotulos_a = "".join(f"[r{i}]" for i in range(n))
    linhas.append(f"[0:a]asplit={n}{rotulos_a};")
    for i, (s, e) in enumerate(manter):
        d = e - s
        f = min(a.fade, d / 4)
        linhas.append(
            f"[r{i}]atrim=start={s:.5f}:end={e:.5f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d={f:.4f},afade=t=out:st={max(d - f, 0):.4f}:d={f:.4f}[a{i}];"
        )
    linhas.append("".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[ac];")

    if a.lufs is None:
        af = "anull"
    elif loud:
        af = (f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:"
              f"measured_I={loud['input_i']}:measured_TP={loud['input_tp']}:"
              f"measured_LRA={loud['input_lra']}:measured_thresh={loud['input_thresh']}:"
              f"offset={loud['target_offset']}:linear=true")
    else:
        af = f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11"
    linhas.append(f"[ac]{af},aresample=48000[aout]")
    return "\n".join(linhas)


def renderizar(entrada, saida, filtro, info, a):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    tmp.write(filtro)
    tmp.close()
    preset = "veryfast" if a.rapido else "medium"
    mapas = (["-map", "[vout]"] if info["tem_video"] else []) + ["-map", "[aout]"]
    cod_v = (["-c:v", "libx264", "-preset", preset, "-crf", str(a.crf),
              "-profile:v", "high", "-pix_fmt", "yuv420p"] if info["tem_video"] else [])
    cod_a = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    extra = ["-movflags", "+faststart"] if saida.lower().endswith((".mp4", ".mov", ".m4a")) else []

    variantes = [["-/filter_complex", tmp.name], ["-filter_complex_script", tmp.name]]
    if versao_ffmpeg() < 7:
        variantes.reverse()
    ultimo = None
    try:
        for var in variantes:
            cmd = (["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", entrada]
                   + var + mapas + cod_v + cod_a + extra + [saida])
            p = run(cmd, check=False)
            if p.returncode == 0:
                return
            ultimo = p.stderr.decode("utf-8", "replace")
            if not re.search(r"Unrecognized option|not found|Option .* not", ultimo):
                break
        raise RuntimeError("ffmpeg falhou ao renderizar:\n" + (ultimo or "")[-3000:])
    finally:
        os.unlink(tmp.name)


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Corta silêncios e respirações de vídeos falados.")
    ap.add_argument("entrada")
    ap.add_argument("-o", "--saida", help="arquivo de saída (padrão: <nome>_cortado.mp4)")
    ap.add_argument("--min-silencio", type=float, default=0.30,
                    help="pausas a partir deste tamanho (s) são cortadas. Padrão 0.30")
    ap.add_argument("--margem", type=float, default=0.05,
                    help="respiro mantido antes e depois de cada fala (s). Padrão 0.05")
    ap.add_argument("--min-fala", type=float, default=0.15,
                    help="trechos isolados menores que isso (s) são tratados como ruído. Padrão 0.15")
    ap.add_argument("--respiracoes", choices=["cortar", "manter"], default="cortar")
    ap.add_argument("--resp-borda", type=float, default=0.25,
                    help="trecho surdo mínimo (s) colado à fala para ser cortado como respiração")
    ap.add_argument("--faixa-db", type=float, default=32.0,
                    help="quanto abaixo do nível de fala começa o silêncio. Maior = corta menos")
    ap.add_argument("--limiar-db", type=float, default=None,
                    help="limiar fixo em dBFS (ignora o cálculo automático)")
    ap.add_argument("--limiar-voz", type=float, default=0.45, help=argparse.SUPPRESS)
    ap.add_argument("--fade", type=float, default=0.010, help="micro fade de áudio por corte (s)")
    ap.add_argument("--lufs", type=float, default=-14.0, help="volume alvo. Padrão -14 (Instagram)")
    ap.add_argument("--sem-normalizar", action="store_true", help="não mexe no volume")
    ap.add_argument("--formato", choices=["reels", "original"], default="reels",
                    help="reels = 1080x1920 com recorte central. original = mantém proporção")
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--crf", type=int, default=18, help="qualidade x264 (menor = melhor)")
    ap.add_argument("--rapido", action="store_true", help="render rápido para conferir cortes")
    ap.add_argument("--analisar", action="store_true", help="só gera o plano, sem renderizar")
    a = ap.parse_args()
    if a.sem_normalizar:
        a.lufs = None

    checar_dependencias()
    if not os.path.isfile(a.entrada):
        sys.exit(f"ERRO: arquivo não encontrado: {a.entrada}")

    base, _ = os.path.splitext(a.entrada)
    info = probe(a.entrada)
    saida = a.saida or (base + ("_cortado.mp4" if info["tem_video"] else "_cortado.m4a"))
    relatorio = os.path.splitext(saida)[0] + "_cortes.json"

    print(f"Analisando {os.path.basename(a.entrada)} ({fmt_t(info['duracao'])})...")
    x = extrair_audio(a.entrada)
    dur = min(info["duracao"], len(x) / SR) if info["duracao"] else len(x) / SR
    plano = planejar(x, dur, a)

    fps_alinhamento = a.fps if info["tem_video"] else 100.0
    manter = alinhar_quadros(plano["manter"], fps_alinhamento, dur)
    final = sum(e - s for s, e in manter)

    avisos = []
    if info["tem_video"] and a.formato == "reels" and info["largura"] > info["altura"]:
        avisos.append("Vídeo horizontal: o formato reels recorta o centro e perde as laterais. "
                      "Use --formato original se preferir manter o quadro inteiro.")
    if dur > 0 and final / dur < 0.4:
        avisos.append("Mais de 60% do vídeo seria removido. Confira se não cortou fala: "
                      "tente --faixa-db 40.")

    resumo = {
        "entrada": os.path.abspath(a.entrada),
        "saida": os.path.abspath(saida),
        "duracao_original_s": round(dur, 2),
        "duracao_final_s": round(final, 2),
        "reducao_pct": round(100 * (1 - final / dur), 1) if dur else 0,
        "trechos_mantidos": len(manter),
        "cortes": len(plano["cortes"]),
        "respiracoes_detectadas": plano["respiracoes_detectadas"],
        "niveis_db": plano["niveis_db"],
        "parametros": {k: getattr(a, k) for k in
                       ("min_silencio", "margem", "min_fala", "respiracoes", "faixa_db",
                        "limiar_db", "fade", "lufs", "formato", "fps")},
        "avisos": avisos,
        "lista_cortes": plano["cortes"],
        "trechos_mantidos_s": [[round(s, 3), round(e, 3)] for s, e in manter],
    }
    with open(relatorio, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    print(f"  Duração: {fmt_t(dur)} -> {fmt_t(final)} "
          f"({resumo['reducao_pct']}% removido, {len(plano['cortes'])} cortes, "
          f"{plano['respiracoes_detectadas']} respirações)")
    print(f"  Níveis: fala {plano['niveis_db']['fala']} dB, ruído {plano['niveis_db']['piso_ruido']} dB, "
          f"limiar {plano['niveis_db']['limiar_usado']} dB")
    for av in avisos:
        print("  AVISO: " + av)
    print(f"  Relatório: {relatorio}")

    if a.analisar:
        return

    loud = medir_loudness(a.entrada, a.lufs) if a.lufs is not None else None
    filtro = montar_filtro(manter, info, a, loud)
    print("Renderizando...")
    renderizar(a.entrada, saida, filtro, info, a)
    print(f"Pronto: {saida}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        sys.exit(f"ERRO: {e}")
