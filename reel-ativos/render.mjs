// node render.mjs [--eixo=log|linear|ambos] [--so-frames] [--frames=a,b,c]
// Captura os quadros com Playwright (1080x1920, 30 fps), gera o áudio e monta o MP4 com ffmpeg.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { FPS, DUR, N_FRAMES } from './modelo.mjs';
import { AQUI, carregarPlaywright, servidor, abrir } from './util.mjs';

const OUT = path.join(AQUI, 'out');
export const pastaQuadros = (eixo) => path.join(OUT, 'frames', eixo);
export const arquivoMp4 = (eixo) => path.join(OUT, `reel-r100-em-2000-${eixo}.mp4`);
const args = process.argv.slice(2);
const soFrames = args.includes('--so-frames');
const lista = args.find((a) => a.startsWith('--frames='))?.slice(9).split(',').map(Number);
const WORKERS = 4;
const eixoArg = args.find((a) => a.startsWith('--eixo='))?.slice(7) ?? 'ambos';
const eixos = eixoArg === 'ambos' ? ['log', 'linear'] : [eixoArg];

async function capturar(eixo) {
  const FRAMES = pastaQuadros(eixo);
  fs.mkdirSync(FRAMES, { recursive: true });
  const { chromium } = carregarPlaywright();
  const { srv, url } = await servidor();
  const browser = await chromium.launch();
  const pages = await Promise.all(Array.from({ length: WORKERS }, () => abrir(browser, url, eixo)));
  const idx = lista ?? Array.from({ length: N_FRAMES }, (_, i) => i);
  let prox = 0;
  await Promise.all(pages.map(async (page) => {
    while (prox < idx.length) {
      const i = idx[prox++];
      await page.evaluate((t) => window.seek(t), i / FPS);
      await page.screenshot({ path: path.join(FRAMES, `f_${String(i).padStart(4, '0')}.png`), type: 'png' });
    }
  }));
  await browser.close();
  srv.close();
}

function sh(cmd, a) {
  const r = spawnSync(cmd, a, { stdio: 'inherit' });
  if (r.status !== 0) throw new Error(`${cmd} falhou`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  for (const eixo of eixos) await capturar(eixo);
  if (!soFrames) sh('node', [path.join(AQUI, 'audio.mjs')]);
  for (const eixo of soFrames ? [] : eixos) {
    sh('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(pastaQuadros(eixo), 'f_%04d.png'),
      '-i', path.join(OUT, 'audio', 'mix-final.wav'), '-t', String(DUR),
      '-vf', 'scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS),
      '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
      '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-movflags', '+faststart', arquivoMp4(eixo)]);
    console.log('pronto:', arquivoMp4(eixo));
  }
}
