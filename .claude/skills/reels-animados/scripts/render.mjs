#!/usr/bin/env node
/*
 * Render do motor reels-animados (animação pura, sem vídeo de fundo).
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

async function abrirMotor() {
  const navegador = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const pagina = await navegador.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  pagina.on('pageerror', e => console.error('Erro no motor:', e.message));
  await pagina.goto(pathToFileURL(MOTOR).href);
  const medidas = await pagina.evaluate(p => window.carregar(p), plano);
  for (const m of medidas) {
    if (['aviso', 'cta'].includes(m.tipo)) continue;
    if (m.topo + m.altura > 1200 || m.topo < 330) {
      console.log(`  AVISO: ${m.id} ocupa ${m.topo} a ${m.topo + m.altura} px, fora da área útil (330 a 1190).`);
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
  for (const c of plano.cenas) {
    for (const e of c.elementos) {
      const fimVis = Math.min(e.fim, c.fim) - 0.05;
      marcos.set(Math.min(e.inicio + 0.5, fimVis), `${e.id}`);
      for (const it of ['itens', 'linhas', 'colunas', 'marcos', 'segmentos'].flatMap(k => e[k] || [])) {
        marcos.set(Math.min(it.em + 0.45, fimVis), `${e.id} item`);
      }
    }
    if (c.transicao && c.transicao !== 'corte') marcos.set(c.inicio + 0.2, `${c.id} transição`);
  }
  for (let t = 0.5; t < plano.duracao; t += 2) {
    if (![...marcos.keys()].some(k => Math.abs(k - t) < 0.6)) marcos.set(t, 'ritmo');
  }
  marcos.set(Math.max(plano.duracao - 0.2, 0), 'final');
  // até 36 quadros por imagem; vídeo longo sai em páginas (folha.png, folha_2.png, ...)
  const tempos = [...marcos.keys()].sort((a, b) => a - b);
  const base = opt('saida', path.join(pastaPlano, 'folha_contato.png'));
  const paginas = Math.ceil(tempos.length / 36);
  for (let pg = 0; pg < paginas; pg++) {
    const parte = tempos.slice(pg * 36, (pg + 1) * 36);
    const imgs = [];
    for (const t of parte) imgs.push({ buf: await quadro(pagina, t, 'jpeg'), rotulo: `${fmt(t)}  ${marcos.get(t)}` });
    const saida = pg === 0 ? base : base.replace(/(\.png)?$/, `_${pg + 1}.png`);
    await grade(navegador, imgs, 6, 270, saida,
      `Folha de contato · ${fmt(plano.duracao)} · página ${pg + 1}/${paginas} · ${imgs.length} quadros` +
      `${plano.guias ? ' · guias de zona segura' : ''}`);
    console.log(`Folha de contato: ${saida}`);
  }
  await navegador.close();
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
  if (!audio || audio === true) {
    console.error('ERRO: informe --audio audio_final.wav (gerado pelo audio.py).');
    process.exit(1);
  }
  const saida = opt('saida', path.join(pastaPlano, 'final.mp4'));
  const { navegador, pagina } = await abrirMotor();
  const entradaAudio = audio;
  const ff = spawn('ffmpeg', ['-y', '-v', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-i', entradaAudio, '-map', '0:v', '-map', '1:a:0',
    '-c:v', 'libx264', '-preset', rapido ? 'veryfast' : 'slow', '-crf', rapido ? '22' : '16',
    '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-r', String(fps),
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', String(plano.duracao), '-movflags', '+faststart', saida],
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
