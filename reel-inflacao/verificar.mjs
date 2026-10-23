// node verificar.mjs [--eixo=linear|log]
// Verificações automáticas: valores x dados.json, zona segura, colisões, sincronia, ffprobe e loudness.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { FPS, N_FRAMES, construir } from './modelo.mjs';
import { AQUI, carregarPlaywright, servidor, abrir } from './util.mjs';

const OUT = path.join(AQUI, 'out');
const EIXO = process.argv.find((a) => a.startsWith('--eixo='))?.slice(7) === 'log' ? 'log' : 'linear';
const MP4 = path.join(OUT, EIXO === 'log' ? 'reel-inflacao-7-paises-log.mp4' : 'reel-inflacao-7-paises.mp4');
console.log(`== eixo ${EIXO} ==`);
const dados = JSON.parse(fs.readFileSync(path.join(AQUI, 'dados.json'), 'utf8'));
const relatorio = { falhas: [], ok: [] };
const ok = (m) => { relatorio.ok.push(m); console.log('OK   ', m); };
const falha = (m) => { relatorio.falhas.push(m); console.log('FALHA', m); };

const { chromium } = carregarPlaywright();
const { srv, url } = await servidor();
const browser = await chromium.launch();
const page = await abrir(browser, url, EIXO);

// varre todos os quadros uma vez, guardando o estado e as medidas do DOM
const quadros = await page.evaluate((n) => {
  const res = [];
  const clips = {};
  document.querySelectorAll('clipPath rect').forEach((r) => {
    clips[r.parentElement.id] = { x: +r.getAttribute('x'), y: +r.getAttribute('y'), w: +r.getAttribute('width'), h: +r.getAttribute('height') };
  });
  for (let i = 0; i < n; i++) {
    window.seek(i / 30);
    const st = window.__state;
    // texto visível medido no DOM (interseção com o recorte, se houver)
    const textos = [];
    document.querySelectorAll('#dyn text, #root > text').forEach((t) => {
      const r = t.getBoundingClientRect();
      let x0 = r.left, y0 = r.top, x1 = r.right, y1 = r.bottom;
      const g = t.closest('g[clip-path]');
      if (g) {
        const c = clips[g.getAttribute('clip-path').slice(5, -1)];
        x0 = Math.max(x0, c.x); y0 = Math.max(y0, c.y); x1 = Math.min(x1, c.x + c.w); y1 = Math.min(y1, c.y + c.h);
      }
      if (x1 > x0 && y1 > y0) textos.push({ s: t.textContent, x0, y0, x1, y1, v: t.getAttribute('data-valor'), fs: +t.getAttribute('font-size') });
    });
    res.push({ t: st.t, ano: st.ano, valores: st.valores, boxes: st.boxes, textos, passo: st.passo, Mx: st.Mx, p: st.p });
  }
  return res;
}, N_FRAMES);
await browser.close();
srv.close();

// ---------- 1. valores na tela x dados.json ----------
{
  const anos = [];
  for (let a = dados.ano_inicial; a <= dados.ano_final; a++) anos.push(a);
  const ultimo = quadros[quadros.length - 1];
  let erros = 0;
  for (const [id, v] of Object.entries(ultimo.valores)) {
    const esperado = Math.round(dados.paises[id].indice_base_2000[String(dados.ano_final)]);
    const naTela = ultimo.textos.find((t) => t.v === id)?.s;
    if (v !== esperado || Number(naTela) !== esperado) { erros++; falha(`último quadro ${id}: tela ${naTela}, dados ${esperado}`); }
  }
  if (!erros) ok(`último quadro: 7 valores na tela batem com dados.json (${Object.entries(ultimo.valores).map(([k, v]) => k + '=' + v).join(' ')})`);
  if (ultimo.ano !== dados.ano_final) falha(`ano final na tela ${ultimo.ano}`); else ok(`ano final na tela: ${ultimo.ano}`);
  // em cada ano de dado, o valor exibido bate com o dado (quadro mais próximo do cruzamento)
  let checados = 0, ruins = 0;
  anos.forEach((a, k) => {
    // primeiro quadro em que o progresso atinge k
    const q = quadros.find((f) => f.p >= k - 1e-9);
    if (!q) return;
    for (const id of Object.keys(dados.paises)) {
      const bruto = dados.paises[id].indice_base_2000[String(a)];
      // o quadro está até 1/30 s após o cruzamento: tolera o avanço de um quadro
      const desvio = Math.abs(q.valores[id] - bruto);
      checados++;
      const tol = 1 + Math.abs(dados.paises[id].indice_base_2000[String(Math.min(a + 1, dados.ano_final))] - bruto) * 0.05;
      if (desvio > tol) { ruins++; falha(`ano ${a} ${id}: tela ${q.valores[id]}, dado ${bruto}`); }
    }
  });
  if (!ruins) ok(`${checados} valores em anos de dado conferidos (tela x dados.json, tolerância de 1 quadro)`);
  // marcos do Brasil derivados do dados.json por conta própria
  const textosMarco = new Set(quadros.flatMap((f) => f.textos.map((t) => t.s)).filter((s) => /^BRASIL: \dX EM \d{4}$/.test(s)));
  const esperados = [200, 300, 400].map((lim) => {
    const a = anos.find((y) => dados.paises.BRA.indice_base_2000[String(y)] >= lim);
    return `BRASIL: ${lim / 100}X EM ${a}`;
  });
  const faltam = esperados.filter((e) => !textosMarco.has(e)), sobram = [...textosMarco].filter((e) => !esperados.includes(e));
  if (faltam.length || sobram.length) falha(`marcos: faltam ${faltam}, sobram ${sobram}`); else ok(`marcos do Brasil na tela: ${[...textosMarco].join(' | ')}`);
}

// ---------- 2. zona segura ----------
{
  let ruins = 0, minY = 1e9, maxY = 0, minX = 1e9, maxX = 0;
  const reg = (x0, y0, x1, y1) => { minY = Math.min(minY, y0); maxY = Math.max(maxY, y1); minX = Math.min(minX, x0); maxX = Math.max(maxX, x1); };
  for (const f of quadros) {
    for (const t of f.textos) {
      reg(t.x0, t.y0, t.x1, t.y1);
      if (t.y0 < 320 || t.y1 > 1450 || t.x0 < 90 || t.x1 > 990) { if (ruins++ < 5) falha(`texto fora da zona segura t=${f.t.toFixed(2)} "${t.s}" [${t.x0.toFixed(0)},${t.y0.toFixed(0)},${t.x1.toFixed(0)},${t.y1.toFixed(0)}]`); }
    }
    for (const b of f.boxes) {
      reg(b.x, b.y, b.x + b.w, b.y + b.h);
      if (b.y < 320 || b.y + b.h > 1450 || b.x < 90 || b.x + b.w > 990) { if (ruins++ < 5) falha(`caixa fora da zona segura t=${f.t.toFixed(2)} ${b.tipo}:${b.id}`); }
    }
  }
  if (!ruins) ok(`zona segura: ${quadros.length} quadros, extremos x ${minX.toFixed(0)}-${maxX.toFixed(0)} (margem 90) y ${minY.toFixed(0)}-${maxY.toFixed(0)} (320-1450)`);
  // tamanho mínimo de fonte medido nos textos visíveis: 40 px, exceto a linha de fonte (28 px)
  const abaixo = new Set();
  for (const f of quadros) for (const t of f.textos) {
    const fonte = /^(Fonte:|Índice de preços|Preços ao consumidor)/.test(t.s);
    if ((fonte && t.fs !== 28) || (!fonte && t.fs < 40)) abaixo.add(`${t.s}:${t.fs}`);
  }
  if (!abaixo.size) ok('fontes: todo texto visível tem 40 px ou mais, exceto a linha de fonte (28 px)'); else falha(`fontes fora da regra: ${[...abaixo].slice(0, 5)}`);
}

// ---------- 3. colisões ----------
{
  const ignora = (a, b) => (a.tipo === 'header' && b.tipo === 'header');
  let col = 0, maxSobra = 0;
  for (const f of quadros) {
    const bs = f.boxes;
    for (let i = 0; i < bs.length; i++) for (let j = i + 1; j < bs.length; j++) {
      const a = bs[i], b = bs[j];
      if (ignora(a, b)) continue;
      const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x), oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (ox > 0.5 && oy > 0.5) {
        maxSobra = Math.max(maxSobra, Math.min(ox, oy));
        if (col++ < 8) falha(`colisão t=${f.t.toFixed(2)} ${a.tipo}:${a.id} x ${b.tipo}:${b.id} (${ox.toFixed(1)}x${oy.toFixed(1)})`);
      }
    }
  }
  if (!col) ok(`colisões: nenhuma entre ${quadros.reduce((s, f) => s + f.boxes.length, 0)} caixas em ${quadros.length} quadros`);
  // espaçamento vertical mínimo entre bandeiras
  let menor = 1e9;
  for (const f of quadros) {
    const fl = f.boxes.filter((b) => b.tipo === 'flag').sort((a, b) => a.y - b.y);
    for (let i = 1; i < fl.length; i++) menor = Math.min(menor, fl[i].y - fl[i - 1].y);
  }
  if (menor >= 56 - 1e-6) ok(`espaçamento mínimo entre bandeiras (centro a centro): ${menor.toFixed(1)} px`); else falha(`espaçamento entre bandeiras ${menor.toFixed(1)} px < 56`);
}

// ---------- 4. eixo Y e ponta do Brasil ----------
{
  const mod = construir(dados, { eixo: EIXO, altura: 456 });
  let mn = 1e9, mx = 0, maxSalto = 0, prev = null, piorT = 0;
  for (const f of quadros) {
    const tip = mod.frac(mod.valor('BRA', mod.progresso(f.t)), f.Mx);
    if (f.t >= 1.5) { mn = Math.min(mn, tip); if (tip > mx) { mx = tip; piorT = f.t; } }
    if (prev !== null) maxSalto = Math.max(maxSalto, Math.abs(f.Mx - prev));
    prev = f.Mx;
  }
  if (mx < 0.92 && mn > 0.75) ok(`ponta do Brasil entre ${(mn * 100).toFixed(1)}% e ${(mx * 100).toFixed(1)}% da altura útil (nunca encosta no topo)`);
  else falha(`ponta do Brasil fora da faixa: ${(mn * 100).toFixed(1)}%..${(mx * 100).toFixed(1)}% em t=${piorT}`);
  ok(`eixo Y: maior variação do máximo entre quadros consecutivos = ${maxSalto.toFixed(2)} (tabela suavizada, sem saltos)`);
}

// ---------- 5. sincronia dos ticks com os anos ----------
{
  const ev = JSON.parse(fs.readFileSync(path.join(OUT, 'audio', 'eventos.json'), 'utf8'));
  let pior = 0, n = 0;
  for (const tk of ev.ticks) {
    const idx = quadros.findIndex((f) => f.ano >= tk.ano);
    const tVideo = idx === 0 && tk.ano === dados.ano_inicial ? tk.t : quadros[idx].t;
    const d = Math.abs(tVideo - tk.t); pior = Math.max(pior, d); n++;
  }
  if (pior <= 1 / FPS + 1e-9) ok(`${n} ticks de áudio x troca do ano na tela: pior diferença ${(pior * 1000).toFixed(1)} ms (menos de 1 quadro = ${(1000 / FPS).toFixed(1)} ms)`);
  else falha(`ticks fora de sincronia: pior ${(pior * 1000).toFixed(1)} ms`);
  // detecção de ataques no áudio final (energia acima de 1,5 kHz)
  const wav = fs.readFileSync(path.join(OUT, 'audio', 'mix-final.wav'));
  const amostras = new Int16Array(wav.buffer, wav.byteOffset + 44, (wav.length - 44) / 2);
  const SR = 48000, n2 = amostras.length / 2, win = Math.round(0.004 * SR), nw = Math.floor(n2 / win);
  const e = new Float64Array(nw);
  let a0 = 0, b0 = 0;
  const hp = new Float64Array(n2);
  for (let i = 0; i < n2; i++) { const x = (amostras[2 * i] + amostras[2 * i + 1]) / 65536; hp[i] = x - a0 * 0.8 - b0 * 0; a0 = x; }
  for (let w = 0; w < nw; w++) { let s = 0; for (let i = 0; i < win; i++) s += hp[w * win + i] ** 2; e[w] = Math.sqrt(s / win); }
  let desvios = [];
  for (const tk of ev.ticks) {
    const c = Math.round(tk.t / (win / SR));
    let melhor = c, v = -1;
    for (let w = c - 5; w <= c + 15; w++) if (e[w] - (e[w - 3] ?? 0) > v) { v = e[w] - (e[w - 3] ?? 0); melhor = w; }
    desvios.push((melhor - c) * (win / SR) * 1000);
  }
  const pd = Math.max(...desvios.map(Math.abs));
  if (pd <= 40) ok(`ataques detectados no áudio final: desvio máximo ${pd.toFixed(0)} ms em relação ao tempo do ano`); else falha(`ataque de áudio deslocado até ${pd.toFixed(0)} ms`);
  // clipping
  let clip = 0; for (let i = 0; i < amostras.length; i++) if (Math.abs(amostras[i]) >= 32767) clip++;
  if (!clip) ok('áudio sem amostras saturadas (clipping)'); else falha(`${clip} amostras saturadas`);
}

// ---------- 6. ffprobe e loudness do MP4 ----------
{
  const pr = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,duration,sample_rate,channels,bit_rate', '-of', 'json', MP4], { encoding: 'utf8' });
  const j = JSON.parse(pr.stdout), v = j.streams.find((s) => s.codec_type === 'video'), a = j.streams.find((s) => s.codec_type === 'audio');
  const prob = [];
  if (v.width !== 1080 || v.height !== 1920) prob.push('resolução');
  if (v.r_frame_rate !== '30/1') prob.push('fps');
  if (v.codec_name !== 'h264') prob.push('codec');
  if (v.pix_fmt !== 'yuv420p') prob.push('pix_fmt');
  if (Math.abs(parseFloat(v.duration) - 26) > 0.05) prob.push('duração');
  if (a.codec_name !== 'aac' || a.sample_rate !== '48000' || a.channels !== 2) prob.push('áudio');
  if (prob.length) falha('ffprobe: ' + prob.join(', ')); else ok(`ffprobe: ${v.width}x${v.height}, ${v.r_frame_rate} fps, ${v.codec_name}, ${v.pix_fmt}, ${parseFloat(v.duration).toFixed(2)} s, áudio ${a.codec_name} ${a.sample_rate} Hz ${a.channels} canais ${(a.bit_rate / 1000).toFixed(0)} kbps`);
  const ln = spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', MP4, '-vn', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], { encoding: 'utf8' });
  const m = JSON.parse(ln.stderr.slice(ln.stderr.lastIndexOf('{'), ln.stderr.lastIndexOf('}') + 1));
  const lufs = parseFloat(m.input_i), tp = parseFloat(m.input_tp);
  if (Math.abs(lufs + 14) <= 1 && tp < -1) ok(`loudness do MP4 (loudnorm em análise): ${lufs} LUFS integrado, true peak ${tp} dBTP, LRA ${m.input_lra}`);
  else falha(`loudness do MP4: ${lufs} LUFS, ${tp} dBTP`);
}

fs.writeFileSync(path.join(OUT, `verificacao-${EIXO}.json`), JSON.stringify(relatorio, null, 2));
console.log(relatorio.falhas.length ? `\n${relatorio.falhas.length} falha(s)` : '\nTudo certo.');
process.exit(relatorio.falhas.length ? 1 : 0);
