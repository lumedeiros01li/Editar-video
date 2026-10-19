/* Motor de composição da skill edicao-grafica. Dois estilos: blueprint e brutalista.
 *
 * Contrato: window.seek(t) desenha o quadro do instante t (segundos).
 * Tudo é função pura de t. Nada de transição CSS, setTimeout,
 * requestAnimationFrame ou estado carregado de um quadro para o outro.
 * Cada seek reescreve todas as propriedades animadas de todas as camadas.
 *
 * Blueprint: painéis escuros quadriculados, traços que se desenham, nada quica.
 * Brutalista: cartões brancos com borda e sombra dura, entram de uma vez, tremor com semente.
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
  };
  // ruído com semente, nunca Math.random
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  window.mulberry32 = mulberry32;
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
  const NS = 'http://www.w3.org/2000/svg';
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

  // ------------------------------------------------------------ estado fixo
  let P = null;
  let BR = false;
  let grupos = [];
  let comps = [];
  let tremores = [];
  const $ = id => document.getElementById(id);
  const saida = () => (BR ? 0 : 0.2);

  // ------------------------------------------------------------ linguagem de movimento
  const entra = (u, d = 0.4) => (u < 0 ? 0 : (BR ? 1 : E.outCubic(clamp(u / d))));
  function revela(no, u, d = 0.32, dist = 30) {
    if (BR) { no.style.visibility = u >= 0 ? 'visible' : 'hidden'; no.style.transform = ''; no.style.clipPath = ''; return; }
    const p = E.outCubic(clamp(u / d));
    no.style.visibility = 'visible';
    no.style.transform = `translateY(${(1 - p) * dist}px)`;
    no.style.clipPath = `inset(0 0 ${(1 - p) * 100}% 0)`;
  }
  function pancada(no, u, base = 14) {
    if (!BR) return;
    if (u < 0) { no.style.translate = ''; no.style.scale = ''; no.style.boxShadow = 'none'; return; }
    const k = 1 - E.outCubic(clamp(u / 0.1));
    no.style.translate = `${(-10 * k).toFixed(2)}px ${(-10 * k).toFixed(2)}px`;
    no.style.scale = String(1 + 0.05 * k);
    no.style.boxShadow = `${(base + 10 * k).toFixed(2)}px ${(base + 10 * k).toFixed(2)}px 0 ${no.dataset.sombra || '#9966FF'}`;
  }
  // destaque: no Brutalista um bloco roxo varre por trás e o texto fica branco.
  // No Blueprint o destaque é o peso semibold, sem animação própria.
  function varrer(b, u) {
    if (!BR) return;
    const p = u <= 0 ? 0 : clamp(u / 0.14);
    b.style.setProperty('--v', (p * 100).toFixed(2) + '%');
    b.style.color = p >= 0.5 ? '#FFF' : '';
  }
  function contar(u, dur) {
    if (u <= 0) return 0;
    if (BR) return Math.min(1, Math.ceil(clamp(u / 0.5) * 6) / 6);
    return E.outExpo(clamp(u / dur));
  }
  function caber(no, larg, min = 90) {
    let tam = parseFloat(getComputedStyle(no).fontSize);
    while (no.offsetWidth > larg && tam > min) { tam -= 4; no.style.fontSize = tam + 'px'; }
  }
  const larguraUtil = raiz => {
    const cs = getComputedStyle(raiz);
    return raiz.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  };

  // ------------------------------------------------------------ caneta (Blueprint)
  function suave(pts) {
    const f = n => n.toFixed(1);
    let d = `M${f(pts[0][0])} ${f(pts[0][1])}`;
    for (let i = 1; i < pts.length - 1; i++) {
      const mx = (pts[i][0] + pts[i + 1][0]) / 2, my = (pts[i][1] + pts[i + 1][1]) / 2;
      d += ` Q${f(pts[i][0])} ${f(pts[i][1])} ${f(mx)} ${f(my)}`;
    }
    const l = pts[pts.length - 1];
    return d + ` L${f(l[0])} ${f(l[1])}`;
  }
  function tracoCaneta(w, h, seed, modo, x0 = 0, y0 = 0) {
    const r = mulberry32(seed);
    const ph = r() * 6.28, ph2 = r() * 6.28;
    const pts = [];
    if (modo === 'sublinha') {
      const n = 26;
      for (let i = 0; i <= n; i++) {
        const u = i / n;
        pts.push([x0 - 10 + (w + 24) * u, y0 + h + 12 + Math.sin(u * 5.2 + ph) * 3 - u * 5]);
      }
      return suave(pts);
    }
    const cx = x0 + w / 2, cy = y0 + h / 2, rx = w / 2 + 34, ry = h / 2 + 22, n = 72;
    for (let i = 0; i <= n; i++) {
      const u = i / n, a = -2.5 + Math.PI * 2 * 1.1 * u;
      const j = 1 + 0.025 * Math.sin(u * 9 + ph) + 0.015 * Math.sin(u * 23 + ph2) + 0.07 * u;
      pts.push([cx + Math.cos(a) * rx * j, cy + Math.sin(a) * ry * j]);
    }
    return suave(pts);
  }
  function caneta(alvo, modo, seed) {
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'caneta');
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('pathLength', '1');
    svg.appendChild(path);
    alvo.style.position = 'relative';
    alvo.appendChild(svg);
    return {
      medir() {
        const w = alvo.offsetWidth, h = alvo.offsetHeight;
        svg.setAttribute('width', w); svg.setAttribute('height', h);
        path.setAttribute('d', tracoCaneta(w, h, seed, modo));
      },
      desenhar(u) {
        const p = u <= 0 ? 0 : E.inOutCubic(clamp(u / (modo === 'sublinha' ? 0.32 : 0.5)));
        path.style.strokeDasharray = '1';
        path.style.strokeDashoffset = String(1 - p);
        svg.style.visibility = p > 0 ? 'visible' : 'hidden';
      },
    };
  }
  // etiqueta: comentário de código no Blueprint, colchetes em caixa alta no Brutalista
  const etiquetaDe = ev => (ev.etiqueta ? el('div', 'etiqueta', BR ? '[ ' + esc(String(ev.etiqueta).toUpperCase()) + ' ]'
    : '// ' + esc(String(ev.etiqueta).toLowerCase())) : null);
  const apagarParenteses = html => html.replace(/\(([^)]*)\)/g, '<span class="dim">($1)</span>');

  // ------------------------------------------------------------ componentes
  const FAB = {};

  // painel (Blueprint) ou cartão (Brutalista): título e cartões usam a mesma base
  function caixa(ev, classes, montar, opts = {}) {
    const raiz = el('div', `camada ${classes} ${BR ? 'cartao-b' : 'painel'}`);
    const etq = etiquetaDe(ev);
    if (etq) raiz.appendChild(etq);
    if (ev.topo) raiz.appendChild(el('div', 'topo', marcar(ev.topo)));
    if (ev.titulo) raiz.appendChild(el('div', 'h', marcar(ev.titulo)));
    const r = montar(raiz) || {};
    const animar = typeof r === 'function' ? r : r.animar;
    const filhos = [...raiz.children].filter(n => n.classList.contains('etiqueta') || n.classList.contains('topo') || n.classList.contains('h'));
    const bs = [...raiz.querySelectorAll('b')];
    return {
      raiz, cartao: !!opts.cartao, medir: r.medir, tremor: BR ? 9 : 0,
      atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.34, saida());
        if (!f) return false;
        if (BR) pancada(raiz, f.u);
        else {
          // o painel se abre da esquerda para a direita, como um traço de régua
          const p = E.outCubic(clamp(f.u / 0.4));
          const s = E.inCubic(f.pout);
          raiz.style.clipPath = p >= 1 ? 'none' : `inset(-4px ${(1 - p) * 100}% -4px -4px)`;
          raiz.style.transform = `translateX(${(-20 * (1 - p)).toFixed(2)}px) translateY(${(24 * s).toFixed(2)}px)`;
          raiz.style.opacity = String(1 - s);
        }
        filhos.forEach((n, k) => revela(n, f.u - (BR ? 0 : 0.08 + k * 0.05)));
        bs.forEach(b => varrer(b, f.u - (BR ? 0.05 : 0.38)));
        if (animar) animar(tm, f);
        return true;
      },
    };
  }

  FAB.titulo = ev => {
    const c = caixa(ev, 'titulo', raiz => { raiz.appendChild(el('div', 't', marcar(ev.texto))); });
    c.raiz.style.top = (ev.y ?? 380) + 'px';
    return c;
  };

  FAB.palavra = ev => {
    const raiz = el('div', 'camada palavra');
    const linha = el('div', 'linha');
    let letras = [];
    if (BR) linha.textContent = String(ev.texto);
    else {
      letras = [...String(ev.texto)].map(c => {
        const s = el('span', 'l', c === ' ' ? '&nbsp;' : esc(c));
        linha.appendChild(s);
        return s;
      });
    }
    raiz.appendChild(linha);
    raiz.style.top = (ev.y ?? 780) + 'px';
    const pen = BR ? null : caneta(linha, 'sublinha', semente(ev.id));
    return {
      raiz, tremor: BR ? 12 : 0,
      medir() { caber(linha, 880, 80); if (pen) pen.medir(); },
      atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.3, saida());
        if (!f) return false;
        if (BR) {
          // bloco limão bate da esquerda para a direita em 4 quadros
          const p = clamp(f.u / 0.12);
          linha.style.clipPath = p >= 1 ? 'none' : `inset(-20px ${(1 - p) * 100}% -20px -20px)`;
          linha.dataset.sombra = '#000';
          pancada(linha, f.u, 16);
          return true;
        }
        letras.forEach((s, i) => {
          const d = E.outCubic(clamp((f.u - i * 0.028) / 0.32));
          const sai = E.inCubic(clamp(f.pout * 1.3 - i * 0.04));
          s.style.transform = `translateY(${110 * (1 - d) - 110 * sai}%)`;
        });
        linha.style.clipPath = f.pout > 0 ? 'inset(-40% -10% 0 -10%)' : 'inset(-40% -10% -60px -10%)';
        if (pen) pen.desenhar(f.u - 0.12 - letras.length * 0.028);
        return true;
      },
    };
  };

  FAB.numero = ev => caixa(ev, 'cartao numero', raiz => {
    const v = el('div', 'valor');
    const txt = el('span', 'txt', esc(ev.valor));
    v.appendChild(txt);
    raiz.appendChild(v);
    const rot = ev.rotulo ? el('div', 'rotulo', marcar(ev.rotulo)) : null;
    const fonte = ev.fonte ? el('div', 'fonte', esc(ev.fonte)) : null;
    if (rot) raiz.appendChild(rot);
    if (fonte) raiz.appendChild(fonte);
    const n = ev.contar === false ? null : lerNumero(ev.valor);
    const dur = ev.contagem ?? 0.9;
    const modo = ev.caneta === false ? null : (ev.caneta || 'sublinha');
    const pen = !BR && modo ? caneta(v, modo, semente(ev.id)) : null;
    if (pen && modo === 'circula') v.style.margin = '20px 0 16px 34px';
    return {
      medir() { caber(v, larguraUtil(raiz) - (pen && modo === 'circula' ? 110 : 0)); if (pen) pen.medir(); },
      animar(tm, f) {
        if (BR) v.style.visibility = 'visible';
        else {
          const p = E.outCubic(clamp((f.u - 0.1) / 0.36));
          v.style.clipPath = p >= 1 ? 'none' : `inset(-30% ${(1 - p) * 100}% -30% -10%)`;
        }
        if (n) {
          const p = contar(f.u - 0.1, dur);
          txt.textContent = p >= 1 ? ev.valor : fmtNumero(n, lerp(ev.de ?? 0, n.val, p));
        }
        if (pen) pen.desenhar(f.u - (n ? 0.1 + dur : 0.5));
        if (rot) revela(rot, f.u - (BR ? 0 : 0.3));
        if (fonte) revela(fonte, f.u - (BR ? 0 : 0.45), 0.25, 16);
      },
    };
  }, { cartao: true });

  const CHECK = '<svg viewBox="0 0 54 54"><path d="M14 28 L23 37 L40 17" pathLength="1" fill="none" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  FAB.lista = ev => caixa(ev, 'cartao lista', raiz => {
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
    return tm => {
      for (const o of itens) {
        const u = tm - o.it.em;
        o.mask.style.display = u >= 0 ? 'block' : 'none';
        o.vazio.style.display = u >= 0 ? 'none' : 'block';
        o.path.style.strokeDasharray = '1';
        if (BR) {
          o.path.style.strokeDashoffset = u >= 0 ? '0' : '1';
          o.chk.style.background = u >= 0 ? '#EBFF70' : '#FFF';
          pancada(o.chk, u, 0);
        } else {
          const v = clamp(u / 0.32);
          o.mask.style.clipPath = `inset(0 ${100 * (1 - E.outCubic(v))}% 0 0)`;
          o.txt.style.transform = `translateX(${-30 * (1 - E.outCubic(v))}px)`;
          o.path.style.strokeDashoffset = String(1 - E.inOutCubic(clamp((u - 0.08) / 0.28)));
        }
      }
    };
  }, { cartao: true });

  FAB.comparacao = ev => caixa(ev, 'cartao comparacao', raiz => {
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
    return tm => {
      for (const o of objs) {
        const u = tm - o.l.em;
        const p = BR ? (u >= 0 ? 1 : 0) : E.outExpo(clamp(u / 0.75));
        o.barra.style.transform = `scaleX(${p})`;
        if (o.n) o.num.textContent = u < 0 ? '' : (p >= 1 ? o.l.texto : fmtNumero(o.n, o.n.val * p));
      }
    };
  }, { cartao: true });

  FAB.grafico = ev => caixa(ev, 'cartao grafico', raiz => {
    const W = 700, H = 400, padT = 40, padB = 56, padL = 6;
    const vals = ev.valores || [0, 1];
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const xs = vals.map((_, i) => padL + (i / (vals.length - 1)) * (W - padL - 24));
    const ys = vals.map(v => padT + (1 - (v - lo) / (hi - lo || 1)) * (H - padT - padB));
    const d = xs.map((x, i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(' ');
    const area = `${d} L${xs[xs.length - 1]} ${H - padB} L${xs[0]} ${H - padB} Z`;
    const rot = ev.rotulos || [];
    const xF = xs[xs.length - 1], yF = ys[ys.length - 1];
    const cor = BR ? '#000' : '#FFFFFF';
    raiz.insertAdjacentHTML('beforeend', `
      <div class="grafico"><svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
        ${BR ? `<path class="area" d="${area}" fill="#EBFF70" stroke="#000" stroke-width="5"/>` : ''}
        <line class="eixo" x1="${padL}" y1="${H - padB}" x2="${W}" y2="${H - padB}" pathLength="1" stroke="${cor}" stroke-opacity="${BR ? 1 : 0.85}" stroke-width="${BR ? 6 : 3}"/>
        <line class="eixo" x1="${padL}" y1="${H - padB}" x2="${padL}" y2="${padT - 20}" pathLength="1" stroke="${cor}" stroke-opacity="${BR ? 1 : 0.85}" stroke-width="${BR ? 6 : 3}"/>
        <path class="ln" d="${d}" pathLength="1" fill="none" stroke="${cor}" stroke-width="${BR ? 11 : 8}" stroke-linecap="${BR ? 'square' : 'round'}" stroke-linejoin="${BR ? 'miter' : 'round'}"/>
        ${BR ? `<rect class="pt" x="${xF - 14}" y="${yF - 14}" width="28" height="28" fill="#000"/>` : `<circle class="pt" cx="${xF}" cy="${yF}" r="14" fill="#EBFF70"/>`}
        <rect class="fundo-final" fill="#EBFF70" width="0" height="0"/>
        <text class="final" x="${xF - 36}" y="${yF + 20}" text-anchor="end">${esc(ev.final ?? '')}</text>
        <path class="pen" pathLength="1" fill="none" stroke="#EBFF70" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
        <text class="eixo-t" x="${padL}" y="${H - 10}">${esc(rot[0] ?? '')}</text>
        <text class="eixo-t" x="${W}" y="${H - 10}" text-anchor="end">${esc(rot[rot.length - 1] ?? '')}</text>
      </svg></div>`);
    const q = s => raiz.querySelector(s);
    const ln = q('.ln'), ar = q('.area'), pt = q('.pt'), fin = q('.final'), pen = q('.pen'), ff = q('.fundo-final');
    const eixos = [...raiz.querySelectorAll('.eixo')];
    const desenho = ev.desenho ?? 1.4;
    const nPts = vals.length - 1;
    return {
      medir() {
        const bb = fin.getBBox();
        if (BR) { ff.setAttribute('x', bb.x - 10); ff.setAttribute('y', bb.y - 2); ff.setAttribute('width', bb.width + 20); ff.setAttribute('height', bb.height + 4); }
        else pen.setAttribute('d', tracoCaneta(bb.width, bb.height, semente(ev.id), 'circula', bb.x, bb.y));
      },
      animar(tm, f) {
        const ue = f.u - 0.1;
        eixos.forEach(e => { e.style.strokeDasharray = '1'; e.style.strokeDashoffset = String(1 - (BR ? (ue >= 0 ? 1 : 0) : E.inOutCubic(clamp(ue / 0.35)))); });
        const pr = clamp((f.u - 0.3) / desenho);
        const p = BR ? Math.floor(pr * nPts) / nPts : E.inOutCubic(pr);
        ln.style.strokeDasharray = '1';
        ln.style.strokeDashoffset = String(1 - p);
        if (ar) ar.style.clipPath = `inset(0 ${100 * (1 - p)}% 0 0)`;
        const uf = f.u - 0.3 - desenho;
        pt.style.visibility = uf >= 0 ? 'visible' : 'hidden';
        fin.style.visibility = uf >= 0 ? 'visible' : 'hidden';
        if (BR) { ff.style.visibility = uf >= 0 ? 'visible' : 'hidden'; pen.style.display = 'none'; }
        else {
          ff.style.display = 'none';
          const pp = uf - 0.3 <= 0 ? 0 : E.inOutCubic(clamp((uf - 0.3) / 0.5));
          pen.style.strokeDasharray = '1';
          pen.style.strokeDashoffset = String(1 - pp);
          pen.style.visibility = pp > 0 ? 'visible' : 'hidden';
        }
      },
    };
  }, { cartao: true });

  // quadro de conta (Blueprint): cada linha entra quando o número é dito
  FAB.conta = ev => caixa(ev, 'cartao conta', raiz => {
    const box = el('div', 'linhas');
    raiz.appendChild(box);
    const objs = (ev.linhas || []).map((l, k) => {
      let regra = null;
      if (l.resultado) { regra = el('div', 'regra'); box.appendChild(regra); }
      const duas = l.valor !== undefined;
      const ln = el('div', 'ln' + (l.resultado ? ' res' : '') + (duas ? ' duas' : ''));
      const tt = el('span', 't');
      let alvo = tt;
      if (duas) {
        tt.innerHTML = `<span class="r">${apagarParenteses(marcar(l.rotulo ?? ''))}</span>`;
        alvo = el('span', 'v', marcar(l.valor));
        tt.appendChild(alvo);
      } else tt.innerHTML = apagarParenteses(marcar(l.texto ?? ''));
      ln.appendChild(tt);
      box.appendChild(ln);
      const modo = ev.caneta === false ? null : (ev.caneta || 'sublinha');
      const pen = !BR && l.resultado && modo ? caneta(alvo, modo, semente(ev.id + ':' + k)) : null;
      const chars = duas ? String(l.rotulo ?? '') + String(l.valor) : String(l.texto ?? '');
      return { l, ln, tt, regra, pen, n: Math.max(1, [...chars.replace(/\*\*/g, '')].length) };
    });
    const fonte = ev.fonte ? el('div', 'fonte', esc(ev.fonte)) : null;
    if (fonte) raiz.appendChild(fonte);
    return {
      medir() { objs.forEach(o => o.pen && o.pen.medir()); },
      animar(tm) {
        for (const o of objs) {
          const u = tm - o.l.em;
          if (o.regra) o.regra.style.transform = `scaleX(${BR ? (u >= 0 ? 1 : 0) : E.inOutCubic(clamp(u / 0.24))})`;
          const ue = o.regra ? u - (BR ? 0 : 0.16) : u;
          const dEsc = Math.min(0.42, 0.05 + o.n * 0.022);
          const p = ue <= 0 ? 0 : (BR ? 1 : clamp(ue / dEsc));
          const pc = p >= 1 ? 1 : Math.floor(p * o.n) / o.n;
          o.ln.style.visibility = ue >= 0 ? 'visible' : 'hidden';
          o.tt.style.clipPath = pc >= 1 ? 'none' : `inset(-30% ${(1 - pc) * 100}% -30% 0)`;
          if (o.pen) o.pen.desenhar(ue - dEsc - 0.08);
        }
        if (fonte) revela(fonte, tm - Math.max(...objs.map(o => o.l.em), ev.inicio) - 0.6, 0.25, 16);
      },
    };
  }, { cartao: true });

  FAB.carimbo = ev => {
    const raiz = el('div', 'camada carimbo' + (ev.destaque ? ' dest' : ''));
    const selo = el('div', 'selo', esc(ev.texto));
    selo.style.setProperty('--giro', (ev.giro ?? -7) + 'deg');
    raiz.appendChild(selo);
    raiz.style.top = (ev.y ?? 700) + 'px';
    return {
      raiz, display: 'flex', tremor: BR ? 14 : 0,
      atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.1, saida());
        if (!f) return false;
        selo.style.scale = String(1 + 0.5 * (1 - E.outCubic(clamp(f.u / 0.09))));
        return true;
      },
    };
  };

  FAB.sticker = ev => {
    const raiz = el('div', 'camada sticker' + (ev.alinhar === 'esquerda' ? ' esq' : ''));
    const s = el('div', 's', marcar(ev.texto));
    const r = mulberry32(semente(ev.id));
    s.style.setProperty('--giro', (ev.giro ?? ((r() < 0.5 ? -1 : 1) * (4 + r() * 4))).toFixed(1) + 'deg');
    raiz.appendChild(s);
    raiz.style.top = (ev.y ?? 560) + 'px';
    return {
      raiz,
      atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.1, saida());
        if (!f) return false;
        s.style.scale = String(1 + 0.25 * (1 - E.outCubic(clamp(f.u / 0.08))));
        return true;
      },
    };
  };

  FAB.emoji = ev => {
    const raiz = el('div', 'camada emoji', esc(ev.emoji));
    raiz.style.left = (ev.x ?? 860) + 'px';
    raiz.style.top = (ev.y ?? 1120) + 'px';
    return {
      raiz, atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.3, saida());
        if (!f) return false;
        const s = BR ? 1 + 0.2 * (1 - E.outCubic(clamp(f.u / 0.08))) : (0.6 + 0.4 * E.outCubic(clamp(f.u / 0.3))) * (1 - E.inCubic(f.pout));
        raiz.style.transform = `scale(${s.toFixed(3)}) rotate(${BR ? 0 : ((1 - E.outCubic(clamp(f.u / 0.3))) * -12).toFixed(2)}deg)`;
        return true;
      },
    };
  };

  FAB.aviso = ev => {
    const raiz = el('div', 'camada aviso');
    const s = el('span', '', esc(ev.texto));
    raiz.appendChild(s);
    return {
      raiz, atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.25, saida());
        if (!f) return false;
        const p = BR ? 1 : E.outCubic(f.pin) * (1 - E.inCubic(f.pout));
        s.style.clipPath = `inset(0 ${100 * (1 - p)}% 0 0)`;
        return true;
      },
    };
  };

  FAB.cta = ev => {
    const raiz = el('div', 'camada cta');
    const c = el('div', 'caixa', marcar(ev.texto));
    raiz.appendChild(c);
    return {
      raiz, display: 'flex', oculta_legenda: true, tremor: BR ? 9 : 0,
      atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.34, saida());
        if (!f) return false;
        if (BR) { pancada(c, f.u); return true; }
        const p = E.outCubic(clamp(f.u / 0.38)), s = E.inCubic(f.pout);
        c.style.clipPath = `inset(-4px ${(1 - p) * 100}% -4px -4px)`;
        c.style.transform = `translateX(${(-24 * (1 - p)).toFixed(2)}px) translateY(${(24 * s).toFixed(2)}px)`;
        c.style.opacity = String(1 - s);
        return true;
      },
    };
  };

  // ------------------------------------------------------------ legenda
  function montarGrupos(palavras, cfg) {
    const max = cfg.max_palavras ?? 4, maxCar = cfg.max_caracteres ?? 24;
    const out = [];
    let g = [];
    palavras.forEach((w, i) => {
      g.push(w);
      const prox = palavras[i + 1];
      const txt = g.map(x => x.texto).join(' ');
      const fecha = !prox || g.length >= max || /[.!?,;:]$/.test(w.texto) ||
        prox.ini - w.fim > 0.35 || (txt.length + 1 + prox.texto.length) > maxCar;
      if (fecha) { out.push(g); g = []; }
    });
    return out.map((ws, k) => {
      const prox = out[k + 1];
      const fimFala = ws[ws.length - 1].fim;
      return { ws, ini: ws[0].ini, fimFala, fim: prox ? Math.min(prox[0].ini, fimFala + 0.6) : fimFala + 0.6 };
    });
  }

  function atualizarLegenda(t, ocultar) {
    const box = $('legenda');
    const g = !ocultar && grupos.find(x => t >= x.ini - 0.04 && t < x.fim);
    if (!g) { box.style.display = 'none'; box.innerHTML = ''; return; }
    box.style.display = 'flex';
    let ativo = -1;
    g.ws.forEach((w, i) => {
      const prox = g.ws[i + 1];
      if (t >= w.ini && (prox ? t < prox.ini : t < w.fim + 0.15)) ativo = i;
    });
    box.innerHTML = g.ws.map((w, i) => {
      if (i !== ativo) return `<span class="p">${esc(w.texto)}</span>`;
      const v = BR ? 100 : 100 * E.outCubic(clamp((t - w.ini) / 0.12));
      return `<span class="p ativo" style="--v:${v.toFixed(1)}%">${esc(w.texto)}</span>`;
    }).join('');
    if (BR) box.style.transform = '';
    else {
      const v = E.outCubic(clamp((t - g.ini + 0.04) / 0.16));
      box.style.transform = `translateY(${(12 * (1 - v)).toFixed(2)}px)`;
    }
    if (P.legenda && P.legenda.y) box.style.top = P.legenda.y + 'px';
  }

  // ------------------------------------------------------------ fundo
  function escalaFundo(t) {
    let base = 1;
    for (const z of P.zoom_base || []) if (t >= z.ini && t < z.fim) { base = z.escala; break; }
    let s = base, foco = P.foco || [540, 760];
    for (const ev of P.eventos) {
      if (ev.tipo !== 'zoom' || t < ev.inicio || t >= ev.fim) continue;
      if (ev.foco) foco = ev.foco;
      if ((ev.modo || (BR ? 'seco' : 'suave')) === 'seco') s = ev.escala;
      else {
        const r = ev.rampa ?? 0.4;
        const a = E.inOutCubic(clamp((t - ev.inicio) / r));
        const b = E.inOutCubic(clamp((ev.fim - t) / r));
        s = lerp(base, ev.escala, Math.min(a, b));
      }
    }
    return { s, foco };
  }

  function quadroDoFundo(t) {
    const fr = P.frames;
    const idx = Math.min(fr.total, Math.max(1, Math.floor(t * P.fps + 1e-6) + 1));
    return fr.dir + 'f_' + String(idx).padStart(6, '0') + '.jpg';
  }

  // ------------------------------------------------------------ API
  window.carregar = async function (plano) {
    P = plano;
    BR = P.estilo === 'brutalista';
    document.body.className = BR ? 'brutalista' : 'blueprint';
    await Promise.all(["300 80px 'Barlow'", "600 80px 'Barlow'", "700 80px 'Barlow'", "500 40px 'JetBrains Mono'",
      "700 40px 'JetBrains Mono'", "400 80px 'Archivo Black'"].map(f => document.fonts.load(f)));
    await document.fonts.ready;
    // palavras com texto vazio continuam existindo para os índices, mas não entram na legenda
    const visiveis = (P.palavras || []).filter(w => String(w.texto).trim() !== '');
    grupos = (P.legenda && P.legenda.ativa === false) ? [] : montarGrupos(visiveis, P.legenda || {});
    const cam = $('camadas');
    cam.innerHTML = '';
    comps = [];
    tremores = [];
    for (const ev of P.eventos) {
      if (!FAB[ev.tipo]) continue;
      const c = FAB[ev.tipo](ev);
      c.ev = ev;
      cam.appendChild(c.raiz);
      comps.push(c);
    }
    // mede; cartões centralizados em y=900, base nunca abaixo de 1190, topo nunca acima de 330
    for (const c of comps) {
      c.raiz.style.display = c.display || 'block';
      if (c.medir) c.medir();
      const h = c.raiz.offsetHeight;
      c.raiz.style.display = 'none';
      if (c.cartao) {
        const top = c.ev.y ?? Math.round(Math.max(330, Math.min(900 - h / 2, 1190 - h)));
        c.raiz.style.top = top + 'px';
        c.altura = h;
        c.topo = top;
      }
      if (c.tremor > 0) {
        const r = mulberry32(semente('tremor:' + c.ev.id));
        tremores.push({ ini: c.ev.inicio, amp: c.tremor, offs: [...Array(6)].map(() => [r() * 2 - 1, r() * 2 - 1]) });
      }
    }
    $('guias').style.display = P.guias ? 'block' : 'none';
    window.pronto = true;
    return comps.filter(c => c.cartao).map(c => ({ id: c.ev.id, tipo: c.ev.tipo, topo: c.topo, altura: c.altura }));
  };

  window.seek = async function (t) {
    const img = $('frame');
    const src = quadroDoFundo(t);
    if (img.getAttribute('src') !== src) img.setAttribute('src', src);
    const { s, foco } = escalaFundo(t);
    const bg = $('bg');
    bg.style.transformOrigin = `${foco[0]}px ${foco[1]}px`;
    bg.style.transform = `scale(${s})`;

    let veu = 0, ocultar = false;
    for (const c of comps) {
      const vis = c.atualizar(t);
      c.raiz.style.display = vis ? (c.display || 'block') : 'none';
      if (!vis) continue;
      if (c.oculta_legenda) ocultar = true;
      const alvo = c.ev.veu ?? (c.cartao ? 0.35 : (c.ev.tipo === 'palavra' ? 0.45 : (c.ev.tipo === 'carimbo' ? 0.35 : 0)));
      if (alvo > 0) {
        const f = fase(t, c.ev.inicio, c.ev.fim, 0.3, 0.2);
        veu = Math.max(veu, BR ? alvo : alvo * E.outCubic(f.pin) * (1 - E.inCubic(f.pout)));
      }
    }
    $('veu').style.opacity = String(veu);
    for (const [a, b] of (P.legenda && P.legenda.ocultar) || []) if (t >= a && t < b) ocultar = true;
    atualizarLegenda(t, ocultar);

    // tremor de tela (Brutalista), com semente
    let dx = 0, dy = 0, treme = false;
    const fps = P.fps || 30;
    for (const tm of tremores) {
      const u = t - tm.ini;
      if (u < 0 || u >= 6 / fps) continue;
      const k = Math.min(5, Math.floor(u * fps + 1e-6));
      const dec = 1 - k / 6;
      dx += tm.offs[k][0] * tm.amp * dec;
      dy += tm.offs[k][1] * tm.amp * dec;
      treme = true;
    }
    $('tela').style.transform = treme ? `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px) scale(1.03)` : '';

    if (img.getAttribute('src')) { try { await img.decode(); } catch (e) { /* quadro ausente */ } }
    return true;
  };
})();
