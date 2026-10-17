#!/usr/bin/env node
/*
 * Render do motor edicao-grafica.
 *
 *   node render.mjs plano_resolvido.json --folha [--guias] [--saida folha.png]
 *   node render.mjs plano_resolvido.json --quadros 0.4,3.2,7.9 [--guias] [--saida pasta]
 *   node render.mjs plano_resolvido.json --movimento 3.2 [--dur 0.6] [--saida tira.png]
 *   node render.mjs plano_resolvido.json --final --audio audio_final.wav [--saida final.mp4] [--rapido]
 *
 * Contrato: cada quadro é window.seek(t). H.264 yuv420p, CRF 16.
 */
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const MOTOR = path.join(AQUI, '..', 'engine', 'engine.html');

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  console.error('ERRO: Playwright não instalado. Rode, na pasta scripts da skill:\n' +
    '  npm install\n  npx playwright install chromium');
  process.exit(1);
}

// ------------------------------------------------------------ argumentos
const args = process.argv.slice(2);
const opt = (nome, padrao) => {
  const i = args.indexOf('--' + nome);
  if (i < 0) return padrao;
  const v = args[i + 1];
  return v === undefined || v.startsWith('--') ? true : v;
};
const arqPlano = args.find(a => a.endsWith('.json'));
if (!arqPlano) {
  console.error('Uso: node render.mjs plano_resolvido.json --folha | --quadros t1,t2 | --movimento t | --final');
  process.exit(1);
}
const plano = JSON.parse(fs.readFileSync(arqPlano, 'utf8'));
const pastaPlano = path.dirname(path.resolve(arqPlano));
const fps = plano.fps || 30;
const total = Math.round(plano.duracao * fps);
plano.guias = !!opt('guias', false);

// ------------------------------------------------------------ quadros do vídeo
function extrairQuadros() {
  const dir = path.join(pastaPlano, `.quadros_${fps}`);
  const marca = path.join(dir, 'pronto.json');
  const st = fs.statSync(plano.video);
  const assinatura = JSON.stringify({ video: plano.video, mtime: st.mtimeMs, fps });
  if (fs.existsSync(marca) && fs.readFileSync(marca, 'utf8') === assinatura) {
    return { dir, n: fs.readdirSync(dir).filter(f => f.endsWith('.jpg')).length };
  }
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  process.stdout.write('Extraindo quadros do vídeo... ');
  const r = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', plano.video, '-vf',
    `fps=${fps},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1`,
    '-q:v', '2', path.join(dir, 'f_%06d.jpg')], { stdio: ['ignore', 'ignore', 'pipe'] });
  if (r.status !== 0) {
    console.error('\nERRO no ffmpeg:\n' + r.stderr.toString().slice(-2000));
    process.exit(1);
  }
  fs.writeFileSync(marca, assinatura);
  const n = fs.readdirSync(dir).filter(f => f.endsWith('.jpg')).length;
  console.log(`${n} quadros.`);
  return { dir, n };
}

async function abrirMotor() {
  const q = extrairQuadros();
  plano.frames = { dir: pathToFileURL(q.dir).href + '/', total: q.n };
  const navegador = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-web-security'] });
  const pagina = await navegador.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  pagina.on('pageerror', e => console.error('Erro no motor:', e.message));
  await pagina.goto(pathToFileURL(MOTOR).href);
  const cartoes = await pagina.evaluate(p => window.carregar(p), plano);
  for (const c of cartoes) {
    if (c.topo + c.altura > 1200 || c.topo < 330) {
      console.log(`  AVISO: ${c.id} ocupa ${c.topo} a ${c.topo + c.altura} px, fora da área útil (330 a 1190).`);
    }
  }
  return { navegador, pagina };
}

const fmt = t => `${Math.floor(t / 60)}:${(t % 60).toFixed(2).padStart(5, '0')}`;

async function quadro(pagina, t, tipo = 'png') {
  await pagina.evaluate(x => window.seek(x), t);
  return pagina.screenshot(tipo === 'png' ? { type: 'png' } : { type: 'jpeg', quality: 95 });
}

// monta várias imagens numa grade e fotografa a grade
// (os quadros vão para arquivos JPEG: leve o bastante para não travar a página)
async function grade(navegador, imgs, colunas, larguraCel, saida, titulo) {
  const tmp = fs.mkdtempSync(path.join(pastaPlano, '.grade_'));
  const cel = imgs.map((i, k) => {
    const arq = path.join(tmp, `q${k}.jpg`);
    fs.writeFileSync(arq, i.buf);
    return `<figure><img src="q${k}.jpg"><figcaption>${i.rotulo}</figcaption></figure>`;
  }).join('');
  const html = path.join(tmp, 'grade.html');
  fs.writeFileSync(html, `<html><body style="margin:0;background:#1b1b1b;font:600 15px sans-serif;color:#eee">
    <div style="padding:12px 20px;font-size:18px">${titulo}</div>
    <div style="display:grid;grid-template-columns:repeat(${colunas},${larguraCel}px);gap:0;padding:0 20px 20px">
    ${cel}</div>
    <style>figure{margin:0 0 8px;padding:4px}img{width:100%;display:block;border-radius:6px}
    figcaption{padding:4px 2px;color:#ccc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}</style>
    </body></html>`);
  const pg = await navegador.newPage({ viewport: { width: colunas * larguraCel + 40, height: 400 } });
  await pg.goto(pathToFileURL(html).href, { timeout: 120000 });
  await pg.screenshot({ path: saida, fullPage: true, timeout: 120000 });
  await pg.close();
  fs.rmSync(tmp, { recursive: true, force: true });
}

// ------------------------------------------------------------ modos
async function folha() {
  const { navegador, pagina } = await abrirMotor();
  // um quadro por novidade (logo após a entrada) e um a cada 2 s
  const marcos = new Map();
  for (const e of plano.eventos) {
    if (e.tipo === 'zoom') continue;
    marcos.set(Math.min(e.inicio + 0.45, e.fim - 0.05), `${e.id}`);
    for (const it of [...(e.itens || []), ...(e.linhas || [])]) {
      marcos.set(Math.min(it.em + 0.4, e.fim - 0.05), `${e.id} item`);
    }
  }
  for (let t = 0.5; t < plano.duracao; t += 2) {
    if (![...marcos.keys()].some(k => Math.abs(k - t) < 0.6)) marcos.set(t, 'ritmo');
  }
  marcos.set(Math.max(plano.duracao - 0.2, 0), 'final');
  const tempos = [...marcos.keys()].sort((a, b) => a - b).slice(0, 36);
  const imgs = [];
  for (const t of tempos) imgs.push({ buf: await quadro(pagina, t, 'jpeg'), rotulo: `${fmt(t)}  ${marcos.get(t)}` });
  const saida = opt('saida', path.join(pastaPlano, 'folha_contato.png'));
  await grade(navegador, imgs, 6, 270, saida,
    `Folha de contato · ${fmt(plano.duracao)} · ${imgs.length} quadros${plano.guias ? ' · guias de zona segura' : ''}`);
  await navegador.close();
  console.log(`Folha de contato: ${saida}`);
}

async function quadros() {
  const { navegador, pagina } = await abrirMotor();
  const tempos = String(opt('quadros')).split(',').map(Number).filter(n => !Number.isNaN(n));
  const pasta = opt('saida', path.join(pastaPlano, 'quadros'));
  fs.mkdirSync(pasta, { recursive: true });
  for (const t of tempos) {
    const arq = path.join(pasta, `q_${t.toFixed(2)}.png`);
    fs.writeFileSync(arq, await quadro(pagina, t));
    console.log(arq);
  }
  await navegador.close();
}

async function movimento() {
  const { navegador, pagina } = await abrirMotor();
  const ini = Number(opt('movimento'));
  const dur = Number(opt('dur', 0.6));
  const passo = 1 / 15;
  const imgs = [];
  for (let t = ini; t <= ini + dur + 1e-6; t += passo) {
    imgs.push({ buf: await quadro(pagina, t, 'jpeg'), rotulo: `${fmt(t)}  +${Math.round((t - ini) * 1000)} ms` });
  }
  const saida = opt('saida', path.join(pastaPlano, `movimento_${ini.toFixed(2)}.png`));
  await grade(navegador, imgs, Math.min(imgs.length, 5), 240, saida, `Movimento a partir de ${fmt(ini)} (15 qps)`);
  await navegador.close();
  console.log(`Tira de movimento: ${saida}`);
}

async function final() {
  const rapido = !!opt('rapido', false);
  const audio = opt('audio', null);
  const saida = opt('saida', path.join(pastaPlano, 'final.mp4'));
  const { navegador, pagina } = await abrirMotor();
  const entradaAudio = audio && audio !== true ? audio : plano.video;
  const ff = spawn('ffmpeg', ['-y', '-v', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-i', entradaAudio, '-map', '0:v', '-map', '1:a:0',
    '-c:v', 'libx264', '-preset', rapido ? 'veryfast' : 'slow', '-crf', rapido ? '22' : '16',
    '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-r', String(fps),
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', saida],
    { stdio: ['pipe', 'inherit', 'pipe'] });
  let errFF = '';
  ff.stderr.on('data', d => { errFF += d; });
  const escrever = buf => new Promise(res => (ff.stdin.write(buf) ? res() : ff.stdin.once('drain', res)));
  const t0 = Date.now();
  let ultimo = -1;
  for (let i = 0; i < total; i++) {
    await escrever(await quadro(pagina, i / fps, 'jpeg'));
    const pct = Math.floor((100 * (i + 1)) / total);
    if (pct % 10 === 0 && pct !== ultimo) {
      ultimo = pct;
      const seg = (Date.now() - t0) / 1000;
      console.log(`  ${pct}%  (${i + 1}/${total} quadros, ${seg.toFixed(0)}s)`);
    }
  }
  ff.stdin.end();
  const cod = await new Promise(res => ff.on('close', res));
  await navegador.close();
  if (cod !== 0) {
    console.error('ERRO no ffmpeg:\n' + errFF.slice(-2000));
    process.exit(1);
  }
  console.log(`Pronto: ${saida}`);
}

if (opt('folha', false)) await folha();
else if (opt('quadros', false)) await quadros();
else if (opt('movimento', false) !== false) await movimento();
else if (opt('final', false)) await final();
else console.error('Escolha um modo: --folha, --quadros, --movimento ou --final');
