/* Motor da skill reels-animados.
 *
 * Contrato: window.seek(t) desenha o quadro do instante t. Função pura de t:
 * sem transição CSS, sem setTimeout, sem requestAnimationFrame, sem estado
 * carregado entre quadros. Ruído só com semente (mulberry32).
 */
(function () {
  'use strict';

  // ------------------------------------------------------------ utilidades
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, u) => a + (b - a) * u;
  const E = {
    outCubic: u => 1 - Math.pow(1 - u, 3),
    inCubic: u => u * u * u,
    inOutCubic: u => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2),
    outExpo: u => (u >= 1 ? 1 : 1 - Math.pow(2, -10 * u)),
    outBounce: u => {
      const n = 7.5625, d = 2.75;
      if (u < 1 / d) return n * u * u;
      if (u < 2 / d) return n * (u -= 1.5 / d) * u + 0.75;
      if (u < 2.5 / d) return n * (u -= 2.25 / d) * u + 0.9375;
      return n * (u -= 2.625 / d) * u + 0.984375;
    },
  };
  function mola(u, z = 0.6, w = 16) {
    if (u <= 0) return 0;
    const wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * u) * (Math.cos(wd * u) + (z * w / wd) * Math.sin(wd * u));
  }
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const semente = s => [...String(s)].reduce((h, c) => (Math.imul(h, 31) + c.charCodeAt(0)) | 0, 7);
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const marcar = s => esc(s)
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/\[\[(.+?)\]\]/g, '<span class="chip">$1</span>')
    .replace(/\n/g, '<br>');
  const el = (tag, cls, html) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  };
  // fase de um elemento. dout = 0 quando ele segura até o fim da cena (sem saída própria)
  function fase(t, ini, fim, din, dout) {
    if (t < ini || t >= fim) return null;
    return { u: t - ini, pin: clamp((t - ini) / din), pout: dout > 0 ? clamp((t - (fim - dout)) / dout) : 0 };
  }
  function lerNumero(txt) {
    const m = String(txt).match(/-?\d[\d.]*(?:,\d+)?/);
    if (!m) return null;
    const [int, frac] = m[0].split(',');
    return {
      pre: txt.slice(0, m.index), suf: txt.slice(m.index + m[0].length),
      val: parseFloat(int.replace(/\./g, '') + (frac ? '.' + frac : '')),
      dec: frac ? frac.length : 0, grupo: int.includes('.'),
    };
  }
  const fmtNumero = (n, v) => n.pre + v.toLocaleString('pt-BR', {
    minimumFractionDigits: n.dec, maximumFractionDigits: n.dec, useGrouping: n.grupo }) + n.suf;

  // revela de baixo para cima dentro da própria caixa
  const revela = (no, u, d = 0.3, dist = 40) => {
    const p = E.outCubic(clamp(u / d));
    no.style.transform = `translateY(${(1 - p) * dist}px)`;
    no.style.clipPath = `inset(0 0 ${(1 - p) * 100}% 0)`;
  };
  const desenharIcone = (svg, u, dur = 0.55) => {
    const tracos = svg.querySelectorAll('path,circle,rect');
    tracos.forEach((tr, k) => {
      const p = E.inOutCubic(clamp((u - k * 0.08) / dur));
      tr.style.strokeDasharray = '1';
      tr.style.strokeDashoffset = String(1 - p);
    });
  };
  const svgIcone = (nome, tam) => {
    const corpo = (window.ICONES[nome] || window.ICONES.alerta).replace(/<(path|circle|rect)\b/g, '<$1 pathLength="1"');
    return `<svg class="ico-svg" width="${tam}" height="${tam}" viewBox="0 0 48 48"><g class="tr-g">${corpo}</g></svg>`;
  };
  const pintarTracos = raiz => raiz.querySelectorAll('.tr-g > *').forEach(n => {
    n.classList.add('tr');
  });

  // ------------------------------------------------------------ estado fixo
  let P = null;
  let cenas = [];       // {cfg, raiz, conteudo, amb, elems:[{ev, raiz, atualizar}]}
  let grupos = [];
  const $ = id => document.getElementById(id);
  const SAIDA = 0.22;
  // display de cada tipo quando visível (o CSS deixa .el escondido)
  const DISPLAY = { icone: 'flex', icones: 'flex', personagem: 'flex', rosca: 'flex', cta: 'flex' };
  const mostrar = (c, vis) => { c.raiz.style.display = vis ? (DISPLAY[c.ev.tipo] || 'block') : 'none'; };

  // ------------------------------------------------------------ componentes
  const FAB = {};

  FAB.frase = ev => {
    const raiz = el('div', `el frase ${ev.tamanho || 'm'}${ev.alinhar === 'centro' ? ' centro-x' : ''}`);
    const ws = [];
    let negrito = false;
    String(ev.texto).split('\n').forEach((linha, li) => {
      if (li) raiz.appendChild(el('br'));
      linha.split(/\s+/).filter(Boolean).forEach(tok => {
        const n = (tok.match(/\*\*/g) || []).length;
        const b = negrito || tok.startsWith('**');
        const limpo = tok.replace(/\*\*/g, '');
        if (n % 2 === 1) negrito = !negrito;
        const w = el('span', 'w', `<span>${b ? `<b>${esc(limpo)}</b>` : esc(limpo)}</span>`);
        raiz.appendChild(w);
        ws.push(w.firstChild);
      });
    });
    let sub = null;
    if (ev.sub) { sub = el('div', 'sub', marcar(ev.sub)); raiz.appendChild(sub); }
    const tempos = ev.tempos || ws.map((_, i) => ev.inicio + i * 0.07);
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        ws.forEach((w, i) => {
          const p = E.outCubic(clamp((t - tempos[i]) / 0.26));
          const s = E.inCubic(clamp(f.pout * 1.4 - i * 0.03));
          w.style.transform = `translateY(${105 * (1 - p) - 105 * s}%)`;
        });
        if (sub) revela(sub, t - (ev.sub_em ?? tempos[tempos.length - 1] + 0.2));
        return true;
      },
    };
  };

  FAB.numero = ev => {
    const raiz = el('div', 'el numero' + (ev.alinhar === 'centro' ? ' centro-x' : ''));
    if (ev.alinhar === 'centro') raiz.style.textAlign = 'center';
    const topo = ev.topo ? el('div', 'topo', marcar(ev.topo)) : null;
    const v = el('div', 'valor', esc(ev.valor));
    const rot = ev.rotulo ? el('div', 'rotulo', marcar(ev.rotulo)) : null;
    const fonte = ev.fonte ? el('div', 'fonte', esc(ev.fonte)) : null;
    [topo, v, rot, fonte].forEach(n => n && raiz.appendChild(n));
    v.style.transformOrigin = ev.alinhar === 'centro' ? '50% 70%' : '0 70%';
    const n = ev.contar === false ? null : lerNumero(ev.valor);
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        if (topo) revela(topo, f.u);
        const s = mola(f.u - 0.06, 0.55, 15);
        const sai = E.inCubic(f.pout);
        v.style.transform = `translateY(${(1 - s) * 80}px) scale(${0.7 + 0.3 * s - 0.1 * sai})`;
        v.style.opacity = String(clamp(f.u / 0.08) * (1 - sai));
        if (n) {
          const p = E.outExpo(clamp((f.u - 0.1) / (ev.contagem ?? 0.9)));
          v.textContent = p >= 1 ? ev.valor : fmtNumero(n, lerp(ev.de ?? 0, n.val, p));
        }
        if (rot) revela(rot, f.u - 0.35);
        if (fonte) revela(fonte, f.u - 0.5, 0.25, 20);
        raiz.style.opacity = String(1 - sai);
        return true;
      },
    };
  };

  FAB.icone = ev => {
    const raiz = el('div', 'el icone ico');
    const disco = el('div', 'disco', svgIcone(ev.icone, 250));
    raiz.appendChild(disco);
    pintarTracos(raiz);
    const rot = ev.rotulo ? el('div', 'rot', marcar(ev.rotulo)) : null;
    if (rot) raiz.appendChild(rot);
    const svg = disco.querySelector('svg');
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        const s = mola(f.u, 0.5, 14) * (1 - E.inCubic(f.pout));
        const flutua = Math.sin((t - ev.inicio) * 2.2) * 6;
        disco.style.transform = `translateY(${flutua}px) scale(${s})`;
        desenharIcone(svg, f.u - 0.12);
        if (rot) revela(rot, f.u - 0.25);
        raiz.style.opacity = String(1 - E.inCubic(f.pout));
        return true;
      },
    };
  };

  FAB.icones = ev => {
    const raiz = el('div', 'el icones ico');
    const cels = (ev.itens || []).map(it => {
      const c = el('div', 'cel');
      const disco = el('div', 'disco', svgIcone(it.icone, 140));
      const rot = el('div', 'rot', marcar(it.rotulo || ''));
      c.append(disco, rot);
      raiz.appendChild(c);
      return { it, c, disco, rot, svg: disco.querySelector('svg') };
    });
    pintarTracos(raiz);
    if (cels.length < 3) raiz.style.justifyContent = 'space-around';
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        for (const o of cels) {
          const u = t - o.it.em;
          o.c.style.visibility = u >= 0 ? 'visible' : 'hidden';
          o.disco.style.transform = `scale(${mola(u, 0.5, 15)})`;
          desenharIcone(o.svg, u - 0.1, 0.45);
          revela(o.rot, u - 0.2);
        }
        raiz.style.opacity = String(1 - E.inCubic(f.pout));
        return true;
      },
    };
  };

  const BOCA = { feliz: 'M-24 6 Q0 30 24 6', preocupado: 'M-20 22 Q0 6 20 22', neutro: 'M-18 14 L18 14' };
  FAB.personagem = ev => {
    const raiz = el('div', 'el personagem');
    const fig = el('div', 'fig');
    fig.style.position = 'relative';
    fig.innerHTML = `
      <svg width="360" height="420" viewBox="-180 -60 360 420" style="overflow:visible">
        <g class="corpo-g">
          <path d="M-150 360 C-150 220 -90 170 0 170 C90 170 150 220 150 360 Z" fill="var(--destaque)"/>
          <g class="cab"><circle cx="0" cy="60" r="100" fill="var(--tinta)"/>
            <g class="olhos"><circle cx="-36" cy="50" r="12" fill="var(--fundo)"/><circle cx="36" cy="50" r="12" fill="var(--fundo)"/></g>
            <path class="boca" d="${BOCA[ev.humor] || BOCA.neutro}" transform="translate(0 90)" fill="none" stroke="var(--fundo)" stroke-width="9" stroke-linecap="round"/>
          </g>
        </g>
      </svg>`;
    raiz.appendChild(fig);
    const nome = ev.nome ? el('div', 'nome', marcar(ev.nome)) : null;
    const desc = ev.descricao ? el('div', 'desc', marcar(ev.descricao)) : null;
    if (nome) raiz.appendChild(nome);
    if (desc) raiz.appendChild(desc);
    let balao = null;
    if (ev.balao) { balao = el('div', 'balao', marcar(ev.balao)); fig.appendChild(balao); }
    const corpo = fig.querySelector('.corpo-g'), olhos = fig.querySelector('.olhos'), cab = fig.querySelector('.cab');
    // piscadas com semente: mesmo plano, mesmas piscadas
    const r = mulberry32(semente(ev.id));
    const piscadas = [];
    for (let k = 0, tt = ev.inicio + 0.8 + r() * 1.5; k < 40; k++, tt += 2.2 + r() * 2.4) piscadas.push(tt);
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.4, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        const s = mola(f.u, 0.55, 13);
        const bob = Math.sin((t - ev.inicio) * 2.6) * 7;
        corpo.style.transform = `translateY(${(1 - s) * 260 + bob}px)`;
        corpo.style.transformOrigin = '0 360px';
        cab.style.transform = `rotate(${Math.sin((t - ev.inicio) * 1.7) * 2.5}deg)`;
        cab.style.transformOrigin = '0 160px';
        const pis = piscadas.some(p => t >= p && t < p + 0.12);
        olhos.style.transform = `scaleY(${pis ? 0.12 : 1})`;
        olhos.style.transformOrigin = '0 50px';
        fig.style.clipPath = 'inset(-400px -400px 0 -400px)';
        if (nome) revela(nome, f.u - 0.3);
        if (desc) revela(desc, f.u - 0.42);
        if (balao) {
          const ub = t - (ev.balao_em ?? ev.inicio + 0.6);
          const sb = mola(ub, 0.5, 16);
          balao.style.display = ub >= 0 ? 'block' : 'none';
          balao.style.transform = `scale(${sb})`;
          balao.style.transformOrigin = '0 100%';
        }
        raiz.style.opacity = String(1 - E.inCubic(f.pout));
        return true;
      },
    };
  };

  FAB.comparacao = ev => {
    const raiz = el('div', 'el comparacao');
    if (ev.titulo) raiz.appendChild(el('div', 'h', marcar(ev.titulo)));
    const linhas = ev.linhas || [];
    const max = Math.max(...linhas.map(l => l.valor), 1e-9);
    const objs = linhas.map(l => {
      const box = el('div', 'linha-comp' + (l.destaque ? ' dest' : ''));
      const rot = el('div', 'rot', `<span>${marcar(l.rotulo)}</span>`);
      const num = el('span', 'num', esc(l.texto ?? ''));
      rot.appendChild(num);
      const trilho = el('div', 'trilho');
      const barra = el('div', 'barra');
      barra.style.width = (100 * l.valor / max) + '%';
      trilho.appendChild(barra);
      box.append(rot, trilho);
      raiz.appendChild(box);
      return { l, barra, num, n: l.texto ? lerNumero(l.texto) : null };
    });
    const h = raiz.querySelector('.h');
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        if (h) revela(h, f.u);
        for (const o of objs) {
          const p = E.outExpo(clamp((t - o.l.em) / 0.8));
          o.barra.style.transform = `scaleX(${p})`;
          if (o.n) o.num.textContent = p >= 1 ? o.l.texto : (t < o.l.em ? '' : fmtNumero(o.n, o.n.val * p));
        }
        raiz.style.opacity = String(1 - E.inCubic(f.pout));
        return true;
      },
    };
  };

  FAB.grafico = ev => {
    const raiz = el('div', 'el grafico');
    if (ev.titulo) raiz.appendChild(el('div', 'h', marcar(ev.titulo)));
    const W = 900, H = 560, padT = 60, padB = 70;
    const vals = ev.valores || [0, 1];
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const xs = vals.map((_, i) => 10 + (i / (vals.length - 1)) * (W - 40));
    const ys = vals.map(v => padT + (1 - (v - lo) / (hi - lo || 1)) * (H - padT - padB));
    const d = xs.map((x, i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(' ');
    const area = `${d} L${xs[xs.length - 1]} ${H - padB} L${xs[0]} ${H - padB} Z`;
    const rot = ev.rotulos || [];
    const xF = xs[xs.length - 1], yF = ys[ys.length - 1];
    raiz.insertAdjacentHTML('beforeend', `
      <svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
        <path class="area" d="${area}" fill="var(--superficie)"/>
        <line x1="0" y1="${H - padB}" x2="${W}" y2="${H - padB}" stroke="var(--sec)" stroke-opacity=".35" stroke-width="4"/>
        <path class="ln" d="${d}" pathLength="1" fill="none" stroke="var(--destaque)" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
        <circle class="pt" cx="${xF}" cy="${yF}" r="20" fill="var(--destaque)"/>
        <text class="final" x="${xF - 40}" y="${yF + 24}" text-anchor="end">${esc(ev.final ?? '')}</text>
        <text class="eixo" x="0" y="${H - 14}">${esc(rot[0] ?? '')}</text>
        <text class="eixo" x="${W}" y="${H - 14}" text-anchor="end">${esc(rot[rot.length - 1] ?? '')}</text>
      </svg>`);
    const ln = raiz.querySelector('.ln'), ar = raiz.querySelector('.area');
    const pt = raiz.querySelector('.pt'), fin = raiz.querySelector('.final'), h = raiz.querySelector('.h');
    const desenho = ev.desenho ?? 1.6;
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        if (h) revela(h, f.u);
        const p = E.inOutCubic(clamp((f.u - 0.3) / desenho));
        ln.style.strokeDasharray = '1';
        ln.style.strokeDashoffset = String(1 - p);
        ar.style.clipPath = `inset(0 ${100 * (1 - p)}% 0 0)`;
        const fd = 0.3 + desenho;
        pt.style.transformOrigin = `${xF}px ${yF}px`;
        pt.style.transform = `scale(${f.u > fd ? mola(f.u - fd, 0.45, 18) : 0})`;
        fin.style.opacity = String(clamp((f.u - fd) / 0.15));
        raiz.style.opacity = String(1 - E.inCubic(f.pout));
        return true;
      },
    };
  };

  FAB.moedas = ev => {
    const raiz = el('div', 'el moedas');
    if (ev.titulo) raiz.appendChild(el('div', 'h', marcar(ev.titulo)));
    const pil = el('div', 'pilhas'), rots = el('div', 'rots');
    raiz.append(pil, rots);
    const cols = (ev.colunas || []).map(c => {
      const col = el('div', 'col');
      const n = Math.max(1, Math.min(22, c.moedas || 5));
      const coins = [];
      for (let k = 0; k < n; k++) {
        const m = el('div', 'coin');
        m.style.bottom = (k * 24) + 'px';
        col.appendChild(m);
        coins.push(m);
      }
      const val = el('div', 'val', esc(c.texto || ''));
      val.style.bottom = (n * 24 + 40) + 'px';
      col.appendChild(val);
      pil.appendChild(col);
      rots.appendChild(el('div', '', marcar(c.rotulo || '')));
      return { c, coins, val, passo: Math.min(0.09, 1.3 / n) };
    });
    const h = raiz.querySelector('.h');
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        if (h) revela(h, f.u);
        for (const o of cols) {
          o.coins.forEach((m, k) => {
            const u = clamp((t - o.c.em - k * o.passo) / 0.38);
            m.style.visibility = u > 0 ? 'visible' : 'hidden';
            m.style.transform = `translateY(${-(1 - E.outBounce(u)) * 520}px)`;
          });
          const fimQueda = o.c.em + o.coins.length * o.passo + 0.38;
          revela(o.val, t - fimQueda, 0.25, 30);
        }
        raiz.style.opacity = String(1 - E.inCubic(f.pout));
        return true;
      },
    };
  };

  const CHECK = '<svg viewBox="0 0 70 70"><path d="M19 36 L31 48 L52 23" pathLength="1" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  FAB.lista = ev => {
    const raiz = el('div', 'el lista');
    if (ev.titulo) raiz.appendChild(el('div', 'h', marcar(ev.titulo)));
    const itens = (ev.itens || []).map(it => {
      const linha = el('div', 'item');
      const chk = el('div', 'chk', CHECK);
      const mask = el('div', 'mask');
      const txt = el('div', 'txt', marcar(it.texto));
      const vazio = el('div', 'vazio');
      mask.appendChild(txt);
      linha.append(chk, mask, vazio);
      raiz.appendChild(linha);
      return { it, chk, path: chk.querySelector('path'), mask, txt, vazio };
    });
    const h = raiz.querySelector('.h');
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        if (h) revela(h, f.u);
        for (const o of itens) {
          const v = clamp((t - o.it.em) / 0.3);
          o.mask.style.display = t >= o.it.em ? 'block' : 'none';
          o.vazio.style.display = t >= o.it.em ? 'none' : 'block';
          o.mask.style.clipPath = `inset(0 ${100 * (1 - E.outExpo(v))}% 0 0)`;
          o.txt.style.transform = `translateX(${-40 * (1 - E.outCubic(v))}px)`;
          const c = clamp((t - o.it.em - 0.05) / 0.25);
          o.path.style.strokeDasharray = '1';
          o.path.style.strokeDashoffset = String(1 - E.outCubic(c));
          o.chk.style.background = c > 0 ? 'var(--destaque)' : 'var(--superficie)';
          o.chk.style.transform = `scale(${1 + 0.12 * Math.sin(Math.PI * c)})`;
        }
        raiz.style.opacity = String(1 - E.inCubic(f.pout));
        return true;
      },
    };
  };

  FAB.linha_tempo = ev => {
    const raiz = el('div', 'el tempo');
    if (ev.titulo) raiz.appendChild(el('div', 'h', marcar(ev.titulo)));
    const corpo = el('div', '');
    corpo.style.position = 'relative';
    const eixo = el('div', 'eixo', '<i></i>');
    corpo.appendChild(eixo);
    const marcos = (ev.marcos || []).map(m => {
      const box = el('div', 'marco');
      const ponto = el('div', 'ponto');
      const q = el('div', 'quando', marcar(m.quando || ''));
      const o = el('div', 'oque', marcar(m.texto || ''));
      box.append(ponto, q, o);
      corpo.appendChild(box);
      return { m, ponto, q, o };
    });
    raiz.appendChild(corpo);
    const n = marcos.length;
    eixo.style.height = Math.max(0, (n - 1) * 170) + 'px';
    const barra = eixo.firstChild, h = raiz.querySelector('.h');
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        if (h) revela(h, f.u);
        let alcance = 0;
        marcos.forEach((o, k) => {
          const u = t - o.m.em;
          if (u >= 0) alcance = k;
          o.ponto.style.transform = `scale(${mola(u, 0.45, 18)})`;
          revela(o.q, u - 0.05);
          revela(o.o, u - 0.15);
        });
        const ultimo = marcos[alcance];
        const prox = alcance > 0 ? E.outCubic(clamp((t - ultimo.m.em) / 0.4)) : 1;
        const frac = n > 1 ? ((alcance - 1 + prox) / (n - 1)) : 0;
        barra.style.transform = `scaleY(${clamp(alcance === 0 ? 0 : frac)})`;
        raiz.style.opacity = String(1 - E.inCubic(f.pout));
        return true;
      },
    };
  };

  FAB.rosca = ev => {
    const raiz = el('div', 'el rosca');
    if (ev.titulo) raiz.appendChild(el('div', 'h', marcar(ev.titulo)));
    const segs = ev.segmentos || [];
    const tot = segs.reduce((a, s) => a + s.valor, 0) || 1;
    let acc = 0;
    const tons = ['var(--destaque)', 'var(--sec)', 'var(--tinta)'];
    const circ = segs.map((s, k) => {
      const ini = acc; acc += 100 * s.valor / tot;
      const cor = s.destaque ? 'var(--destaque)' : tons[1 + (k % 2)];
      const op = s.destaque ? 1 : (k % 2 ? 0.35 : 0.6);
      return { s, ini, tam: 100 * s.valor / tot, cor, op };
    });
    raiz.insertAdjacentHTML('beforeend', `
      <svg width="560" height="560" viewBox="-280 -280 560 560">
        <circle r="200" fill="none" stroke="var(--superficie)" stroke-width="80"/>
        ${circ.map((c, k) => `<circle class="sg" data-k="${k}" r="200" fill="none" stroke="${c.cor}" stroke-opacity="${c.op}" stroke-width="80" pathLength="100" transform="rotate(${-90 + c.ini * 3.6})"/>`).join('')}
        <text class="centro" y="52" text-anchor="middle">${esc(ev.centro ?? '')}</text>
      </svg>`);
    const leg = el('div', 'leg', circ.map(c => `<span><i style="background:${c.cor};opacity:${c.op}"></i>${marcar(c.s.rotulo)}</span>`).join(''));
    raiz.appendChild(leg);
    const sgs = [...raiz.querySelectorAll('.sg')], centro = raiz.querySelector('.centro'), h = raiz.querySelector('.h');
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        if (h) revela(h, f.u);
        sgs.forEach((g, k) => {
          const c = circ[k];
          const p = E.inOutCubic(clamp((t - c.s.em) / 0.6));
          g.style.strokeDasharray = `${c.tam * p} 100`;
        });
        const s = mola(f.u - 0.5, 0.5, 15);
        centro.style.transform = `scale(${Math.max(0, s)})`;
        revela(leg, f.u - 0.6);
        raiz.style.opacity = String(1 - E.inCubic(f.pout));
        return true;
      },
    };
  };

  FAB.cta = ev => {
    const raiz = el('div', 'el cta');
    const c = el('div', 'caixa', marcar(ev.texto));
    raiz.appendChild(c);
    return {
      raiz, oculta_legenda: true, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.34, ev.segura ? 0 : SAIDA);
        if (!f) return false;
        const s = mola(f.u, 0.5, 15);
        c.style.transform = `translateY(${(1 - s) * 60}px) scale(${0.86 + 0.14 * s})`;
        c.style.clipPath = `inset(${100 * (1 - E.outExpo(clamp(f.u / 0.3)))}% 0 0 0 round 30px)`;
        return true;
      },
    };
  };

  FAB.aviso = ev => {
    const raiz = el('div', 'el aviso');
    const s = el('span', '', esc(ev.texto));
    raiz.appendChild(s);
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.25, ev.segura ? 0 : 0.2);
        if (!f) return false;
        const p = E.outCubic(f.pin) * (1 - E.inCubic(f.pout));
        s.style.clipPath = `inset(0 ${100 * (1 - p)}% 0 0 round 10px)`;
        return true;
      },
    };
  };

  // ------------------------------------------------------------ fundo ambiente
  function montarAmbiente(cena) {
    const r = mulberry32(semente(cena.id + cena.fundo));
    const formas = [];
    for (let k = 0; k < 3; k++) {
      formas.push({ x: 100 + r() * 880, y: 300 + r() * 1300, raio: 260 + r() * 360,
                    ph: r() * 6.28, vel: 0.08 + r() * 0.1, anel: r() < 0.5 });
    }
    const svg = `<svg width="1080" height="1920">${formas.map(f =>
      f.anel ? `<circle r="${f.raio}" fill="none" stroke="var(--tom)" stroke-width="56"/>`
             : `<circle r="${f.raio}" fill="var(--tom)"/>`).join('')}</svg>`;
    return { svg, formas };
  }

  // ------------------------------------------------------------ legenda
  function montarGrupos(palavras, cfg) {
    const max = cfg.max_palavras ?? 4, maxCar = cfg.max_caracteres ?? 24;
    const out = []; let g = [];
    palavras.forEach((w, i) => {
      g.push(w);
      const prox = palavras[i + 1];
      const txt = g.map(x => x.texto).join(' ');
      if (!prox || g.length >= max || /[.!?,;:]$/.test(w.texto) || prox.ini - w.fim > 0.35 ||
          (txt.length + 1 + prox.texto.length) > maxCar) { out.push(g); g = []; }
    });
    return out.map((ws, k) => {
      const prox = out[k + 1], fimFala = ws[ws.length - 1].fim;
      return { ws, ini: ws[0].ini, fim: prox ? Math.min(prox[0].ini, fimFala + 0.6) : fimFala + 0.6 };
    });
  }
  const TEMA_LEG = { branco: ['#000', '#9966FF'], lilas: ['#000', '#9966FF'], roxo: ['#fff', '#000'], preto: ['#fff', '#9966FF'] };
  function atualizarLegenda(t, ocultar, fundo) {
    const box = $('legenda');
    const g = !ocultar && grupos.find(x => t >= x.ini - 0.04 && t < x.fim);
    if (!g) { box.style.display = 'none'; box.innerHTML = ''; return; }
    const [tinta, dest] = TEMA_LEG[fundo] || TEMA_LEG.branco;
    box.style.setProperty('--leg-tinta', tinta);
    box.style.setProperty('--leg-destaque', dest);
    box.style.display = 'flex';
    let ativo = -1;
    g.ws.forEach((w, i) => {
      const prox = g.ws[i + 1];
      if (t >= w.ini && (prox ? t < prox.ini : t < w.fim + 0.15)) ativo = i;
    });
    box.innerHTML = g.ws.map((w, i) => i !== ativo ? `<span class="p">${esc(w.texto)}</span>`
      : `<span class="p ativo" style="transform:scale(${1 + 0.06 * Math.sin(Math.PI * clamp((t - w.ini) / 0.09))})">${esc(w.texto)}</span>`).join('');
    const v = E.outCubic(clamp((t - g.ini + 0.04) / 0.14));
    box.style.transform = `translateY(${16 * (1 - v)}px) scale(${0.94 + 0.06 * v})`;
    if (P.legenda && P.legenda.y) box.style.top = P.legenda.y + 'px';
  }

  // ------------------------------------------------------------ API
  window.carregar = async function (plano) {
    P = plano;
    await Promise.all(["700 80px 'Barlow'", "600 80px 'Barlow'", "500 40px 'Inter'", "700 40px 'Inter'", "800 40px 'Inter'"]
      .map(f => document.fonts.load(f)));
    await document.fonts.ready;
    const visiveis = (P.palavras || []).filter(w => String(w.texto).trim() !== '');
    grupos = (P.legenda && P.legenda.ativa === false) ? [] : montarGrupos(visiveis, P.legenda || {});
    const raizCenas = $('cenas');
    raizCenas.innerHTML = '';
    cenas = [];
    const medidas = [];
    for (const cfg of P.cenas) {
      const raiz = el('div', `cena t-${cfg.fundo || 'branco'}`);
      const amb = montarAmbiente(cfg);
      const ambEl = el('div', 'ambiente', amb.svg);
      const conteudo = el('div', 'conteudo');
      raiz.append(ambEl, conteudo);
      raizCenas.appendChild(raiz);
      const elems = [];
      for (const ev of cfg.elementos) {
        if (!FAB[ev.tipo]) continue;
        const c = FAB[ev.tipo](ev);
        c.ev = ev;
        conteudo.appendChild(c.raiz);
        elems.push(c);
      }
      // posiciona: alto = 360, centro = centralizado em 800, baixo = base em 1190
      raiz.style.display = 'block';
      for (const c of elems) {
        mostrar(c, true);
        const h = c.raiz.offsetHeight;
        mostrar(c, false);
        const pos = c.ev.pos || 'centro';
        let top = c.ev.y ?? (pos === 'alto' ? 360 : pos === 'baixo' ? 1190 - h : Math.round(800 - h / 2));
        if (c.ev.tipo === 'aviso' && c.ev.y === undefined) top = 1392;
        if (c.ev.tipo === 'cta' && c.ev.y === undefined) top = 1250;
        c.raiz.style.top = top + 'px';
        medidas.push({ id: c.ev.id, tipo: c.ev.tipo, topo: top, altura: h });
      }
      raiz.style.display = 'none';
      cenas.push({ cfg, raiz, conteudo, circulos: [...ambEl.querySelectorAll('circle')], formas: amb.formas, elems });
    }
    $('guias').style.display = P.guias ? 'block' : 'none';
    window.pronto = true;
    return medidas;
  };

  function desenharCena(c, t, tEl) {
    const cfg = c.cfg;
    c.raiz.style.display = 'block';
    c.formas.forEach((f, k) => {
      const x = f.x + Math.sin(t * f.vel + f.ph) * 60, y = f.y + Math.cos(t * f.vel * 0.8 + f.ph) * 80;
      c.circulos[k].setAttribute('cx', x.toFixed(1));
      c.circulos[k].setAttribute('cy', y.toFixed(1));
    });
    const dur = Math.max(cfg.fim - cfg.inicio, 0.5);
    const push = 1 + 0.025 * clamp((t - cfg.inicio) / dur);
    c.conteudo.style.transform = `scale(${push})`;
    let oculta = false;
    for (const e of c.elems) {
      const vis = e.atualizar(tEl);
      mostrar(e, vis);
      if (vis && e.oculta_legenda) oculta = true;
    }
    return oculta;
  }

  window.seek = async function (t) {
    let idx = 0;
    for (let i = 0; i < cenas.length; i++) if (t >= cenas[i].cfg.inicio) idx = i;
    const atual = cenas[idx];
    const ant = idx > 0 ? cenas[idx - 1] : null;
    const tr = atual.cfg.transicao || 'corte';
    const dTr = tr === 'corte' ? 0 : (atual.cfg.dur_transicao ?? 0.5);
    const emTr = ant && t < atual.cfg.inicio + dTr;
    const p = emTr ? E.inOutCubic(clamp((t - atual.cfg.inicio) / dTr)) : 1;

    for (const c of cenas) {
      c.raiz.style.display = 'none';
      c.raiz.style.transform = '';
      c.raiz.style.clipPath = '';
      c.raiz.style.zIndex = '0';
    }
    let oculta = false;
    if (emTr) {
      // a cena que sai congela no último instante dela, sem animação de saída
      oculta = desenharCena(ant, t, Math.min(t, ant.cfg.fim - 0.001)) || oculta;
      ant.raiz.style.zIndex = '1';
      if (tr === 'empurra') ant.raiz.style.transform = `translateY(${-p * 100}%)`;
      if (tr === 'lateral') ant.raiz.style.transform = `translateX(${-p * 100}%)`;
    }
    oculta = desenharCena(atual, t, t) || oculta;
    atual.raiz.style.zIndex = '2';
    if (emTr) {
      const [ox, oy] = atual.cfg.origem || [540, 900];
      if (tr === 'cortina') atual.raiz.style.clipPath = `inset(${(1 - p) * 100}% 0 0 0)`;
      if (tr === 'circulo') atual.raiz.style.clipPath = `circle(${p * 2250}px at ${ox}px ${oy}px)`;
      if (tr === 'empurra') atual.raiz.style.transform = `translateY(${(1 - p) * 100}%)`;
      if (tr === 'lateral') atual.raiz.style.transform = `translateX(${(1 - p) * 100}%)`;
    }
    for (const [a, b] of (P.legenda && P.legenda.ocultar) || []) if (t >= a && t < b) oculta = true;
    const fundoLeg = (emTr && p < 0.5 ? ant : atual).cfg.fundo || 'branco';
    atualizarLegenda(t, oculta, fundoLeg);
    return true;
  };
})();
