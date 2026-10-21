#!/usr/bin/env python3
"""Pipeline completo de um Reel R7.

Uso:
  python3 r7.py <ID> --roteiros <prompt.md> [--inicio 0] [--base ~/reels-r7] [--tmp DIR]

Lê o roteiro do ID no arquivo de prompt, prepara o vídeo, detecta o rosto, calcula o layout,
renderiza os balões, monta a trilha e exporta em <base>/saida/<ID>/:
  <ID>.mp4, <ID>_sem_audio.mp4, <ID>_capa.png, <ID>_contato.jpg
A folha de conferência (com área segura e zonas do rosto) fica na pasta temporária, nunca na saída.
Códigos de saída: 0 ok, 2 rosto sem solução (quadro de problema gerado), 3 vídeo curto, 1 erro.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(SKILL, 'scripts')
FONTS = os.path.join(SKILL, 'assets', 'fonts')
MODEL = os.path.join(SKILL, 'assets', 'blaze_face_short_range.tflite')
FPS, FRAMES, DUR = 30, 210, 7.0
ENTRY = {'2': 36, '3': 72, '4': 108, 'c': 138}   # 1,2 s  2,4 s  3,6 s  4,6 s
SHEET_TIMES = [0.0, 1.3, 2.5, 3.7, 4.7, 6.9]
AREA = (50, 258, 893, 1525)
EXPANSAO = (30, 228, 990, 1590)  # limite da expansão leve (direita 940 abaixo de y 1080)


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def ff(*args):
    run(['ffmpeg', '-v', 'error', '-y', *args])


# ---------- roteiro ----------
def parse_roteiro(md_path, rid):
    txt = open(md_path, encoding='utf-8').read()
    blocks = re.split(r'^###\s+', txt, flags=re.M)
    for blk in blocks[1:]:
        head, _, body = blk.partition('\n')
        if head.split('·')[0].strip() != rid:
            continue
        b, aviso, capa = {}, {}, None
        for line in body.splitlines():
            if line.startswith('#'):
                break
            m = re.match(r'^\s*([1-4])\.\s+(.*\S)\s*$', line)
            if m:
                b[int(m.group(1))] = m.group(2)
                continue
            m = re.match(r'^\s*Aviso no bal[ãa]o\s+([1-4])\s*:\s*(.*\S)\s*$', line)
            if m:
                aviso[m.group(1)] = m.group(2)
                continue
            m = re.match(r'^\s*Capa\s*:\s*(.*\S)\s*$', line)
            if m:
                capa = m.group(1)
        if len(b) != 4 or not capa:
            sys.exit(f'Roteiro de {rid} incompleto: {len(b)} balões, capa={capa!r}')
        return {'b': [b[i] for i in range(1, 5)], 'aviso': aviso, 'capa': capa, 'titulo': head.split('·', 1)[-1].strip()}
    sys.exit(f'ID {rid} não encontrado em {md_path}')


# ---------- vídeo ----------
def probe(src):
    j = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', src]))
    v = next(s for s in j['streams'] if s['codec_type'] == 'video')
    w, h = int(v['width']), int(v['height'])
    rot = 0
    for sd in v.get('side_data_list', []):
        if 'rotation' in sd:
            rot = int(sd['rotation'])
    if abs(rot) % 180 == 90:
        w, h = h, w
    dur = float(v.get('duration') or j['format']['duration'])
    return {'w': w, 'h': h, 'dur': dur, 'fps': v.get('r_frame_rate')}


def prepare_video(src, start, out):
    vf = (f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps={FPS},'
          f'tpad=stop_mode=clone:stop_duration=2,setsar=1')
    ff('-ss', str(start), '-i', src, '-t', str(DUR + 1), '-vf', vf, '-frames:v', str(FRAMES), '-an',
       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '8', '-pix_fmt', 'yuv420p', out)


# ---------- rosto ----------
def egl_env(tmp):
    env = dict(os.environ)
    try:
        import ctypes
        ctypes.CDLL('libEGL.so.1')
        return env
    except OSError:
        pass
    # sem libEGL no sistema: usa a do Chromium do Playwright (nada é instalado)
    cands = glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/libEGL.so') + \
        glob.glob(os.path.expanduser('~/.cache/ms-playwright/chromium-*/chrome-linux/libEGL.so'))
    if not cands:
        return env
    d = os.path.dirname(cands[0])
    lib = os.path.join(tmp, 'egl')
    os.makedirs(lib, exist_ok=True)
    for a, b in [('libEGL.so', 'libEGL.so.1'), ('libGLESv2.so', 'libGLESv2.so.2')]:
        p = os.path.join(lib, b)
        if not os.path.exists(p):
            os.symlink(os.path.join(d, a), p)
    env['LD_LIBRARY_PATH'] = lib + ':' + d + ':' + env.get('LD_LIBRARY_PATH', '')
    return env


def detect_face(base_mp4, tmp):
    fdir = os.path.join(tmp, 'rosto')
    os.makedirs(fdir, exist_ok=True)
    ff('-i', base_mp4, '-vf', 'fps=4', '-frames:v', '28',
       os.path.join(fdir, 'q_%02d.png'))
    out = os.path.join(tmp, 'rosto.json')
    run([sys.executable, os.path.join(SCRIPTS, 'face.py'), fdir, MODEL, out], env=egl_env(tmp),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.load(open(out))


# ---------- música ----------
def music(base, tmp):
    files = sorted(f for f in glob.glob(os.path.join(base, 'musica', '*')) if f.lower().endswith(('.mp3', '.wav')))
    raw = os.path.join(tmp, 'musica_bruta.wav')
    if files:
        ff('-i', files[0], '-t', str(DUR), '-ac', '2', '-ar', '48000', raw)
        origem = 'pasta: ' + os.path.basename(files[0])
    else:
        run(['node', os.path.join(SCRIPTS, 'synth.mjs'), raw, str(DUR)])
        origem = 'sintetizada'
    # loudnorm em duas passadas, linear: -14 LUFS, pico -1 dBTP
    p1 = subprocess.run(['ffmpeg', '-hide_banner', '-i', raw, '-af', 'loudnorm=I=-14:TP=-1:LRA=11:print_format=json',
                         '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(p1[p1.rindex('{'):p1.rindex('}') + 1])
    out = os.path.join(tmp, 'musica.wav')
    ff('-i', raw, '-af', f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
       f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,"
       f"aresample=48000", '-t', str(DUR), out)
    return out, origem


def loudness(path):
    e = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', e)
    pk = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', e)
    return (float(i[-1]) if i else None, float(pk[-1]) if pk else None)


# ---------- composição ----------
def compose(base_mp4, png, lay, out_noaudio):
    inputs, chains, cur, idx = ['-i', base_mp4], [], '[0:v]', 1
    for s in lay['shots']:
        k = s['k']
        if k == '1':
            en, y = 'gte(n,0)', s['y']
        elif s['final']:
            en, y = f"gte(n,{ENTRY[k] + 6})", s['y']
        else:
            en, y = f"eq(n,{ENTRY[k] + s['si']})", s['y'] + round(40 * (1 - s['e']))
        inputs += ['-loop', '1', '-framerate', str(FPS), '-t', str(DUR), '-i', os.path.join(png, s['name'])]
        nxt = f'[v{idx}]'
        chains.append(f"{cur}[{idx}:v]overlay=x={s['x']}:y={y}:enable='{en}':eof_action=pass{nxt}")
        cur, idx = nxt, idx + 1
    chains[-1] = chains[-1][:chains[-1].rindex('[')] + '[vout]'
    ff(*inputs, '-filter_complex', ';'.join(chains), '-map', '[vout]', '-frames:v', str(FRAMES),
       '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', str(FPS),
       '-movflags', '+faststart', '-an', out_noaudio)


def frame_at(mp4, t, out):
    ff('-i', mp4, '-vf', f'select=eq(n\\,{round(t * FPS)})', '-frames:v', '1', out)


def sheets(frames, capa, out_clean, out_check, face):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 360, 640
    sc = W / 1080
    try:
        fnt = ImageFont.load_default(size=24)
    except TypeError:
        fnt = ImageFont.load_default()
    labels = [f'{t:.1f}s' for t in SHEET_TIMES] + ['capa']
    imgs = [Image.open(f).convert('RGB').resize((W, H)) for f in frames + [capa]]
    for check, out in [(False, out_clean), (True, out_check)]:
        sheet = Image.new('RGB', (W * 4, H * 2), 'white')
        for n, (im, lab) in enumerate(zip(imgs, labels)):
            im = im.copy()
            d = ImageDraw.Draw(im)
            if check:
                box = lambda r, c: d.rectangle([v * sc for v in r], outline=c, width=2)
                if lab != 'capa':
                    box(AREA, (0, 200, 0))
                    box(EXPANSAO, (0, 200, 220))
                else:
                    box((0, 285, 1079, 1635), (0, 80, 255))
                if face.get('zona'):
                    box(face['zona'], (255, 210, 0))
                    box(face['proibida'], (255, 0, 0))
            d.rectangle([4, 4, 4 + 12 * len(lab) + 8, 34], fill='white')
            d.text((8, 6), lab, fill='black', font=fnt)
            sheet.paste(im, ((n % 4) * W, (n // 4) * H))
        sheet.save(out, quality=92)


def problem_frame(base_mp4, face, fail, out, tmp):
    from PIL import Image, ImageDraw
    f = os.path.join(tmp, 'problema_base.png')
    frame_at(base_mp4, 3.0, f)
    im = Image.open(f).convert('RGB')
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle(AREA, outline=(0, 200, 0), width=5)
    if face.get('zona'):
        d.rectangle(face['zona'], outline=(255, 210, 0), width=5)
        d.rectangle(face['proibida'], outline=(255, 0, 0), width=5, fill=(255, 0, 0, 70))
    for p in fail.get('pos', {}).values():
        d.rectangle([p['x'], p['y'], p['x'] + p['w'], p['y'] + p['h']], outline=(255, 0, 255), width=5)
    c = fail.get('chip')
    if c:
        d.rectangle([c['x'], c['y'], c['x'] + c['w'], c['y'] + c['h']], outline=(0, 0, 0), width=5)
    im.resize((540, 960)).save(out, quality=88)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('id')
    ap.add_argument('--roteiros', required=True)
    ap.add_argument('--inicio', type=float, default=0.0)
    ap.add_argument('--base', default=os.path.expanduser('~/reels-r7'))
    ap.add_argument('--tmp')
    ap.add_argument('--capa-tempo', type=float, default=0.5, help='segundo do vídeo usado como fundo da capa (padrão 0,5)')
    ap.add_argument('--ultrapassar', action='store_true', help='libera a área segura (olhos e boca continuam proibidos)')
    a = ap.parse_args()
    rid, base = a.id, a.base
    tmp = a.tmp or tempfile.mkdtemp(prefix=f'r7_{rid}_')
    os.makedirs(tmp, exist_ok=True)
    alerts = []
    if a.ultrapassar:
        alerts.append('modo ultrapassar: balões e chamada podem sair da área segura')

    roteiro = parse_roteiro(a.roteiros, rid)
    srcs = [p for p in glob.glob(os.path.join(base, 'entrada', rid + '.*')) if p.lower().endswith(('.mp4', '.mov', '.m4v'))]
    if not srcs:
        sys.exit(f'Vídeo {rid} não encontrado em {base}/entrada/')
    src = srcs[0]
    info = probe(src)
    if info['w'] > info['h']:
        alerts.append('vídeo horizontal (cortado no centro para 9:16)')
    avail = info['dur'] - a.inicio
    if avail < DUR - 1.0:
        print(json.dumps({'ok': False, 'erro': f'vídeo curto: {avail:.2f} s a partir de {a.inicio} s (mínimo 6 s)'}, ensure_ascii=False))
        sys.exit(3)
    if avail < DUR:
        alerts.append(f'último quadro congelado por {DUR - avail:.2f} s')

    base_mp4 = os.path.join(tmp, 'base.mp4')
    prepare_video(src, a.inicio, base_mp4)
    face = detect_face(base_mp4, tmp)
    if not face.get('proibida'):
        alerts.append('rosto não detectado: layout padrão sem a regra do rosto')
    elif face['sem_rosto']:
        alerts.append(f"rosto não detectado em {len(face['sem_rosto'])} de {face['quadros']} quadros analisados")

    png = os.path.join(tmp, 'png')
    job = {'roteiro': roteiro, 'face': {'proibida': face['proibida'], 'zona': face['zona']} if face.get('proibida') else None,
           'out': png, 'fonts': FONTS, 'livre': a.ultrapassar}
    jp = os.path.join(tmp, 'job.json')
    json.dump(job, open(jp, 'w'), ensure_ascii=False)
    r = subprocess.run(['node', os.path.join(SCRIPTS, 'render.mjs'), jp])
    if r.returncode == 2:
        fail = json.load(open(os.path.join(png, 'falha.json')))
        pf = os.path.join(tmp, f'{rid}_problema.jpg')
        problem_frame(base_mp4, face, fail, pf, tmp)
        print(json.dumps({'ok': False, 'erro': fail['motivo'], 'quadro_problema': pf, 'rosto': face.get('union'),
                          'proibida': face.get('proibida'), 'altura_pilha_minima': fail.get('alturaPilhaMin')}, ensure_ascii=False))
        sys.exit(2)
    if r.returncode != 0:
        sys.exit('render falhou')
    lay = json.load(open(os.path.join(png, 'layout.json')))
    if not lay.get('capa'):
        alerts.append('capa não coube sem tocar olhos e boca')
    if lay.get('expansao'):
        alerts.append('expansão leve além da área segura: ' + ', '.join(lay['expansao']))
    if lay['margem']:
        alerts.append('sobreposição só na margem da zona do rosto: ' + ', '.join(lay['margem']))
    if lay['capa'] and lay['capa'].get('margem'):
        alerts.append('capa encosta na margem da zona do rosto')

    out = os.path.join(base, 'saida', rid)
    os.makedirs(out, exist_ok=True)
    noaudio = os.path.join(out, f'{rid}_sem_audio.mp4')
    final = os.path.join(out, f'{rid}.mp4')
    compose(base_mp4, png, lay, noaudio)
    wav, origem = music(base, tmp)
    ff('-i', noaudio, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
       '-t', str(DUR), '-movflags', '+faststart', final)

    # capa
    capa = os.path.join(out, f'{rid}_capa.png')
    cf = os.path.join(tmp, 'capa_fundo.png')
    frame_at(base_mp4, a.capa_tempo, cf)
    if lay.get('capa'):
        ff('-i', cf, '-i', os.path.join(png, 'capa_balao.png'), '-filter_complex', 'overlay=0:0', '-frames:v', '1', capa)
    else:
        shutil.copy(cf, capa)

    # folhas
    frames = []
    for n, t in enumerate(SHEET_TIMES):
        f = os.path.join(tmp, f'folha_{n}.png')
        frame_at(final, t, f)
        frames.append(f)
    check = os.path.join(tmp, f'{rid}_contato_conferencia.jpg')
    sheets(frames, capa, os.path.join(out, f'{rid}_contato.jpg'), check, face)

    # verificação técnica
    nfr = [int(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries',
                                        'stream=nb_read_frames', '-of', 'csv=p=0', p]).decode().strip()) for p in (final, noaudio)]
    lufs, peak = loudness(wav)
    print(json.dumps({
        'ok': True, 'id': rid, 'titulo': roteiro['titulo'], 'saida': out, 'conferencia': check, 'tmp': tmp,
        'fontes': lay['fontes'], 'larguras': lay['larguras'], 'linhas': lay['linhas'], 'chamada': lay['chamada'],
        'centroX': lay['centroX'], 'passos_rosto': lay['passos'], 'capa_fonte': lay['capa']['size'] if lay.get('capa') else None,
        'musica': origem, 'lufs': lufs, 'pico_dbfs': peak, 'quadros': nfr, 'alertas': alerts,
        'rosto': face.get('union'), 'proibida': face.get('proibida'),
    }, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
