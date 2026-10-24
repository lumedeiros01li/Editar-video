// node verificar.mjs
// Verificações: valores x planilha, flashes recalculados, ranking, limites, colisões, loop, sincronia, ffprobe e loudness.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { FPS, N_FRAMES, T_RANKING, T_VOLTA, FLASH_DUR } from './modelo.mjs';
import { AQUI, carregarPlaywright, servidor, abrir } from './util.mjs';
import { MP4 } from './render.mjs';

const OUT = path.join(AQUI, 'out');
const dados = JSON.parse(fs.readFileSync(path.join(AQUI, 'dados.json'), 'utf8'));
const rel = { falhas: [], ok: [], avisos: [] };
const ok = (m) => { rel.ok.push(m); console.log('OK   ', m); };
const falha = (m) => { rel.falhas.push(m); console.log('FALHA', m); };
const aviso = (m) => { rel.avisos.push(m); console.log('AVISO', m); };

const { chromium } = carregarPlaywright();
const { srv, url } = await servidor();
const browser = await chromium.launch();
const page = await abrir(browser, url);
const quadros = await page.evaluate((n) => {
  const clips = {};
  document.querySelectorAll('clipPath rect').forEach((r) => {
    clips[r.parentElement.id] = { x: +r.getAttribute('x'), y: +r.getAttribute('y'), w: +r.getAttribute('width'), h: +r.getAttribute('height') };
  });
  const res = [];
  for (let i = 0; i < n; i++) {
    window.seek(i / 30);
    const st = window.__state, textos = [];
    document.querySelectorAll('#dyn text').forEach((t) => {
      const r = t.getBoundingClientRect();
      let x0 = r.left, y0 = r.top, x1 = r.right, y1 = r.bottom;
      const g = t.closest('g[clip-path]');
      if (g) { const c = clips[g.getAttribute('clip-path').slice(5, -1)]; x0 = Math.max(x0, c.x); y0 = Math.max(y0, c.y); x1 = Math.min(x1, c.x + c.w); y1 = Math.min(y1, c.y + c.h); }
      if (x1 > x0 && y1 > y0) textos.push({ s: t.textContent, x0, y0, x1, y1, fs: +t.getAttribute('font-size'), v: t.getAttribute('data-valor') });
    });
    res.push({ t: st.t, p: st.p, ano: st.ano, valores: st.valores, boxes: st.boxes, flash: st.flash, textos });
  }
  return res;
}, N_FRAMES);
await browser.close();
srv.close();

const milhar = (n) => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
const finalDe = (id) => dados.series[id].valores.at(-1);

// 1. valores revelados x dados.json x roteiro
{
  const q = quadros.find((f) => f.t >= T_RANKING + 0.5);
  const roteiro = { POU: 593, IBOV: 1222, SPX: 1523, CDI: 1836, OURO: 4212, IPCA: 456 };
  let ruins = 0;
  for (const [id, n] of Object.entries(roteiro)) {
    const esperado = `R$ ${milhar(finalDe(id))}`;
    const tela = q.textos.find((t) => t.v === id)?.s;
    if (tela !== esperado) { ruins++; falha(`${id}: tela "${tela}", dados "${esperado}"`); }
    if (Math.round(finalDe(id)) !== n) { ruins++; falha(`${id}: dados ${Math.round(finalDe(id))} diferente do roteiro ${n}`); }
  }
  if (!ruins) ok(`valores no ranking batem com dados.json e com o roteiro: ${Object.keys(roteiro).map((id) => `${id} ${q.textos.find((t) => t.v === id).s}`).join(' | ')}`);
  // ordem vertical do ranking = ordem dos valores
  const rot = q.boxes.filter((b) => b.tipo === 'rotulo').sort((a, b) => a.y - b.y).map((b) => b.id);
  const esperado = Object.keys(roteiro).sort((a, b) => finalDe(b) - finalDe(a));
  if (rot.join() === esperado.join()) ok(`ranking na tela, de cima para baixo: ${rot.join(' > ')}`); else falha(`ranking na tela ${rot} != ${esperado}`);
  // início neutro: a ordem dos nomes no quadro 0 não entrega o vencedor
  const ini = quadros[0].boxes.filter((b) => b.tipo === 'rotulo').sort((a, b) => a.y - b.y).map((b) => b.id);
  if (ini[0] !== esperado[0]) ok(`quadro inicial não entrega o ranking (topo: ${ini[0]})`); else falha('quadro inicial mostra o vencedor no topo');
  // poupança acima da inflação ao ano
  const a = (Math.pow(finalDe('POU') / finalDe('IPCA'), 1 / dados.anos_periodo) - 1) * 100;
  const titulo = quadros.find((f) => f.t >= T_RANKING + 0.5).textos.map((t) => t.s).join(' ');
  if (titulo.includes(`${Math.round(a)}% AO ANO`)) ok(`"cerca de ${Math.round(a)}% ao ano acima da inflação" confere: ${a.toFixed(2)}% a.a. em ${dados.anos_periodo} anos`);
  else falha('frase da poupança x inflação não confere');
}

// 2. flashes recalculados por conta própria e tempo de tela
{
  const anos = dados.anos, k = (a) => anos.indexOf(String(a));
  const pct = (r) => `${r > 0 ? '+' : ''}${Math.round(r * 100)}%`;
  const s = dados.series;
  let kSpx = -1;
  for (let j = anos.length - 1; j > 0 && s.SPX.valores[j] > s.POU.valores[j]; j--) kSpx = j;
  const esperados = [
    `2008: IBOVESPA ${pct(s.IBOV.retornos[k(2008) - 1])}`,
    `${anos[kSpx]}: S&P PASSA A POUPANÇA`,
    `2024: DÓLAR ${pct(s.USD.retornos[k(2024) - 1])}`,
  ];
  for (const e of esperados) {
    const n = quadros.filter((f) => f.flash === e).length;
    if (n / FPS >= 1) ok(`flash "${e}" confere com os dados e fica ${(n / FPS).toFixed(2)} s parado na tela`);
    else falha(`flash "${e}": ${(n / FPS).toFixed(2)} s na tela`);
  }
  const antes = s.SPX.valores.findIndex((v, j) => j > 0 && v > s.POU.valores[j]);
  aviso(`S&P em R$ já tinha passado a poupança em ${anos[antes]} e voltou para trás; fica acima de vez a partir de ${anos[kSpx]} (${s.SPX.valores[kSpx].toFixed(0)} x ${s.POU.valores[kSpx].toFixed(0)})`);
}

// 3. limites (176 a 1678, margem 90) e fontes
{
  const ZT = 176 - 4, ZB = 1678 + 4;
  let ruins = 0, mnY = 1e9, mxY = 0, mnX = 1e9, mxX = 0;
  for (const f of quadros) {
    for (const t of f.textos) {
      mnY = Math.min(mnY, t.y0); mxY = Math.max(mxY, t.y1); mnX = Math.min(mnX, t.x0); mxX = Math.max(mxX, t.x1);
      if (t.y0 < ZT || t.y1 > ZB || t.x0 < 90 || t.x1 > 990) if (ruins++ < 5) falha(`texto fora t=${f.t.toFixed(2)} "${t.s}"`);
    }
    for (const b of f.boxes) if (b.y < ZT || b.y + b.h > ZB || b.x < 90 || b.x + b.w > 990) if (ruins++ < 5) falha(`caixa fora t=${f.t.toFixed(2)} ${b.tipo}:${b.id}`);
  }
  if (!ruins) ok(`limites: textos entre x ${mnX.toFixed(0)}-${mxX.toFixed(0)} e y ${mnY.toFixed(0)}-${mxY.toFixed(0)} (alvo 176-1678, margem 90)`);
  const fora = new Set();
  for (const f of quadros) for (const t of f.textos) {
    const rod = t.y0 > 1540;
    if ((rod && t.fs !== 28) || (!rod && t.fs < 40)) fora.add(`${t.s}:${t.fs}`);
  }
  if (!fora.size) ok('fontes: 40 px ou mais, rodapé em 28 px'); else falha(`fontes fora da regra: ${[...fora].slice(0, 4)}`);
}

// 4. colisões (ultrapassagens entre rótulos são contadas à parte)
{
  let col = 0, ultra = 0, quadrosUltra = new Set();
  for (const f of quadros) {
    const bs = f.boxes;
    for (let i = 0; i < bs.length; i++) for (let j = i + 1; j < bs.length; j++) {
      const a = bs[i], b = bs[j];
      if (a.tipo === 'header' && b.tipo === 'header') continue;
      const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x), oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (ox <= 0.5 || oy <= 0.5) continue;
      if (a.tipo === 'rotulo' && b.tipo === 'rotulo') { ultra++; quadrosUltra.add(f.t.toFixed(2)); continue; }
      if (col++ < 6) falha(`colisão t=${f.t.toFixed(2)} ${a.tipo}:${a.id} x ${b.tipo}:${b.id} (${ox.toFixed(0)}x${oy.toFixed(0)})`);
    }
  }
  if (!col) ok('colisões: nenhuma entre textos, chips, eixos e rótulos de tipos diferentes');
  if (quadrosUltra.size) aviso(`rótulos se cruzando em ultrapassagens: ${quadrosUltra.size} quadros de ${quadros.length} (${(quadrosUltra.size / FPS).toFixed(2)} s)`);
  else ok('rótulos: nenhuma sobreposição, nem nas ultrapassagens');
}

// 5. loop: último quadro igual ao primeiro (pixels)
{
  const a = path.join(OUT, 'frames', 'f_0000.png'), b = path.join(OUT, 'frames', `f_${String(N_FRAMES - 1).padStart(4, '0')}.png`);
  const r = spawnSync('ffmpeg', ['-hide_banner', '-i', a, '-i', b, '-lavfi', 'psnr', '-f', 'null', '-'], { encoding: 'utf8' });
  const m = r.stderr.match(/average:(\S+)/);
  const psnr = m ? m[1] : '?';
  if (psnr === 'inf' || parseFloat(psnr) > 45) ok(`loop: último quadro igual ao primeiro (PSNR ${psnr} dB)`); else falha(`loop: último quadro difere do primeiro (PSNR ${psnr} dB)`);
}

// 6. sincronia: troca do ano x tick, revelação x valor na tela
{
  const ev = JSON.parse(fs.readFileSync(path.join(OUT, 'audio', 'eventos.json'), 'utf8'));
  let pior = 0;
  for (const tk of ev.ticks) {
    const q = quadros.find((f) => f.ano >= tk.ano && f.t >= 1.9);
    pior = Math.max(pior, Math.abs(q.t - tk.t));
  }
  if (pior <= 1 / FPS + 1e-9) ok(`${ev.ticks.length} ticks x troca do ano: pior diferença ${(pior * 1000).toFixed(0)} ms (< 1 quadro)`); else falha(`ticks fora de sincronia: ${(pior * 1000).toFixed(0)} ms`);
  let piorR = 0;
  for (const r of ev.revelacoes) {
    const q = quadros.find((f) => f.valores[r.id]);
    piorR = Math.max(piorR, Math.abs(q.t - r.t));
  }
  if (piorR <= 1 / FPS + 1e-9) ok(`revelações: som e valor na tela juntos (pior ${(piorR * 1000).toFixed(0)} ms)`); else falha(`revelação fora de sincronia ${(piorR * 1000).toFixed(0)} ms`);
  const wav = fs.readFileSync(path.join(OUT, 'audio', 'mix-final.wav'));
  const am = new Int16Array(wav.buffer, wav.byteOffset + 44, (wav.length - 44) / 2);
  let clip = 0; for (const x of am) if (Math.abs(x) >= 32767) clip++;
  if (!clip) ok('áudio sem clipping'); else falha(`${clip} amostras saturadas`);
}

// 7. ffprobe e loudness do MP4
{
  const pr = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,duration,sample_rate,channels,bit_rate', '-of', 'json', MP4], { encoding: 'utf8' });
  const j = JSON.parse(pr.stdout), v = j.streams.find((s) => s.codec_type === 'video'), a = j.streams.find((s) => s.codec_type === 'audio');
  const prob = [];
  if (v.width !== 1080 || v.height !== 1920) prob.push('resolução');
  if (v.r_frame_rate !== '30/1') prob.push('fps');
  if (v.codec_name !== 'h264' || v.pix_fmt !== 'yuv420p') prob.push('codec');
  if (Math.abs(parseFloat(v.duration) - N_FRAMES / FPS) > 0.05) prob.push('duração');
  if (a.codec_name !== 'aac' || a.sample_rate !== '48000' || a.channels !== 2) prob.push('áudio');
  if (prob.length) falha('ffprobe: ' + prob.join(', ')); else ok(`ffprobe: ${v.width}x${v.height}, ${v.r_frame_rate} fps, ${v.codec_name}, ${v.pix_fmt}, ${parseFloat(v.duration).toFixed(2)} s, ${a.codec_name} ${a.sample_rate} Hz ${a.channels} canais`);
  const ln = spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', MP4, '-vn', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], { encoding: 'utf8' });
  const m = JSON.parse(ln.stderr.slice(ln.stderr.lastIndexOf('{'), ln.stderr.lastIndexOf('}') + 1));
  if (Math.abs(parseFloat(m.input_i) + 14) <= 1 && parseFloat(m.input_tp) < -1) ok(`loudness: ${m.input_i} LUFS, true peak ${m.input_tp} dBTP`); else falha(`loudness: ${m.input_i} LUFS, ${m.input_tp} dBTP`);
}

fs.writeFileSync(path.join(OUT, 'verificacao.json'), JSON.stringify(rel, null, 2));
console.log(rel.falhas.length ? `\n${rel.falhas.length} falha(s)` : '\nTudo certo.');
process.exit(rel.falhas.length ? 1 : 0);
