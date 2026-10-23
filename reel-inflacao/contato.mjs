// node contato.mjs [--eixo=linear|log] : folhas de contato em out/contact-sheets/<eixo>/
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { AQUI } from './util.mjs';
import { FPS, N_FRAMES } from './modelo.mjs';

const EIXO = process.argv.find((a) => a.startsWith('--eixo='))?.slice(7) === 'log' ? 'log' : 'linear';
const FR = path.join(AQUI, 'out', 'frames', EIXO), DEST = path.join(AQUI, 'out', 'contact-sheets', EIXO);
fs.mkdirSync(DEST, { recursive: true });
const tempos = [0, 1, 2.5, 4, 6, 8, 10, 12, 14, 16, 17.5, 19, 22, (N_FRAMES - 1) / FPS];
const folhas = [tempos.slice(0, 7), tempos.slice(7)];
folhas.forEach((ts, n) => {
  const args = ['-y', '-hide_banner', '-loglevel', 'error'];
  ts.forEach((t) => args.push('-i', path.join(FR, `f_${String(Math.round(t * FPS)).padStart(4, '0')}.png`)));
  const W = 360, H = 640;
  const esc = ts.map((_, i) => `[${i}:v]scale=${W}:${H}[s${i}]`).join(';');
  const layout = ts.map((_, i) => `${(i % 4) * W}_${Math.floor(i / 4) * H}`).join('|');
  const fc = `${esc};${ts.map((_, i) => `[s${i}]`).join('')}xstack=inputs=${ts.length}:layout=${layout}:fill=gray[o]`;
  args.push('-filter_complex', fc, '-map', '[o]', path.join(DEST, `folha-${n + 1}.png`));
  const r = spawnSync('ffmpeg', args, { stdio: 'inherit' });
  if (r.status !== 0) process.exit(1);
  console.log(`folha-${n + 1}.png:`, ts.map((t) => t + 's').join(', '));
});
