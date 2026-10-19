/* Motor da skill reels-animados. Dois estilos: blueprint e brutalista.
 *
 * Contrato: window.seek(t) desenha o quadro do instante t. Função pura de t:
 * sem transição CSS, sem setTimeout, sem requestAnimationFrame, sem estado
 * carregado entre quadros. Ruído só com semente (mulberry32).
 *
 * Blueprint: movimento preciso e calmo, traços que se desenham, nada quica (sem mola).
 * Brutalista: movimento seco, entradas de uma vez com tremor de tela com semente.
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
  const NS = 'http://www.w3.org/2000/svg';
  // dout = 0: segura até o fim da cena, sem saída própria
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
  let BR = false;          // true = brutalista, false = blueprint
  let cenas = [];
  let grupos = [];
  let tremores = [];       // {ini, amp, offs}
  let linhasPapel = [];    // {no, ini}
  const $ = id => document.getElementById(id);
  const saida = () => (BR ? 0 : 0.22);
  const CARTOES_BR = new Set(['numero', 'comparacao', 'grafico', 'moedas', 'lista', 'linha_tempo', 'rosca']);
  // etiqueta: comentário de código no Blueprint, colchetes em caixa alta no Brutalista
  const textoEtiqueta = ev => (BR ? '[ ' + esc(String(ev.etiqueta).toUpperCase()) + ' ]' : '// ' + esc(String(ev.etiqueta).toLowerCase()));
  // parênteses na conta ficam apagados: "÷ taxa (6% a.a.)"
  const apagarParenteses = html => html.replace(/\(([^)]*)\)/g, '<span class="dim">($1)</span>');
  const DISPLAY = { icone: 'flex', icones: 'flex', personagem: 'flex', rosca: 'flex', cta: 'flex', carimbo: 'flex' };
  const mostrar = (c, vis) => { c.raiz.style.display = vis ? (DISPLAY[c.ev.tipo] || 'block') : 'none'; };

  // ------------------------------------------------------------ linguagem de movimento
  // progresso de entrada: Blueprint desliza sem passar do ponto, Brutalista chega de uma vez
  const entra = (u, d = 0.4) => (u < 0 ? 0 : (BR ? 1 : E.outCubic(clamp(u / d))));
  function revela(no, u, d = 0.32, dist = 36) {
    if (BR) {
      no.style.visibility = u >= 0 ? 'visible' : 'hidden';
      no.style.transform = ''; no.style.clipPath = '';
      return;
    }
    const p = E.outCubic(clamp(u / d));
    no.style.visibility = 'visible';
    no.style.transform = `translateY(${(1 - p) * dist}px)`;
    no.style.clipPath = `inset(0 0 ${(1 - p) * 100}% 0)`;
  }
  // cartão brutalista: chega levantado e assenta na sombra dura em 0,1 s
  function pancada(no, u, base = 14) {
    if (!BR) return;
    const k = u < 0 ? 1 : 1 - E.outCubic(clamp(u / 0.1));
    no.style.translate = `${(-10 * k).toFixed(2)}px ${(-10 * k).toFixed(2)}px`;
    no.style.scale = String(1 + 0.05 * k);
    no.style.boxShadow = `${(base + 10 * k).toFixed(2)}px ${(base + 10 * k).toFixed(2)}px 0 var(--sombra)`;
  }
  // destaque: no Brutalista um bloco roxo varre por trás e o texto fica branco.
  // No Blueprint o destaque é o peso semibold, que entra junto com a palavra.
  function varrer(b, u) {
    if (!BR) return;
    const p = u <= 0 ? 0 : clamp(u / 0.14);
    b.style.setProperty('--v', (p * 100).toFixed(2) + '%');
    b.style.color = p >= 0.5 ? '#FFF' : '';
  }
  // contagem: suave no Blueprint, em 6 degraus secos no Brutalista
  function contar(u, dur) {
    if (u <= 0) return 0;
    if (BR) return Math.min(1, Math.ceil(clamp(u / 0.5) * 6) / 6);
    return E.outExpo(clamp(u / dur));
  }
  // diminui a fonte até o texto caber na largura (medido uma vez no carregar)
  function caber(no, larg, min = 96) {
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
    // circula: elipse feita à mão, um pouco mais de uma volta, abrindo para fora
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

  // ------------------------------------------------------------ ícones
  const desenharIcone = (svg, u, dur = 0.55) => {
    svg.querySelectorAll('path,circle,rect').forEach((tr, k) => {
      const p = BR ? (u >= 0 ? 1 : 0) : E.inOutCubic(clamp((u - k * 0.08) / dur));
      tr.style.strokeDasharray = '1';
      tr.style.strokeDashoffset = String(1 - p);
    });
  };
  const svgIcone = (nome, tam) => {
    const corpo = (window.ICONES[nome] || window.ICONES.alerta).replace(/<(path|circle|rect)\b/g, '<$1 pathLength="1"');
    return `<svg class="ico-svg" width="${tam}" height="${tam}" viewBox="0 0 48 48"><g class="tr-g">${corpo}</g></svg>`;
  };
  const pintarTracos = raiz => raiz.querySelectorAll('.tr-g > *').forEach(n => n.classList.add('tr'));

  // ------------------------------------------------------------ base dos blocos
  // etiqueta, título, cartão brutalista, destaques e saída ficam aqui.
  function bloco(ev, classes, montar, opts = {}) {
    const cartao = BR && CARTOES_BR.has(ev.tipo);
    const raiz = el('div', `el ${classes}${cartao ? ' cartao-b' : ''}`);
    const etq = ev.etiqueta ? el('div', 'etiqueta', textoEtiqueta(ev)) : null;
    if (etq) raiz.appendChild(etq);
    const h = ev.titulo ? el('div', 'h', marcar(ev.titulo)) : null;
    if (h) raiz.appendChild(h);
    const r = montar(raiz) || {};
    const animar = typeof r === 'function' ? r : r.animar;
    const bs = [...raiz.querySelectorAll('b')];
    return {
      raiz, medir: r.medir, oculta_legenda: !!opts.oculta_legenda,
      tremor: BR ? (cartao ? 9 : (opts.tremor || 0)) : 0,
      atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : saida());
        if (!f) return false;
        if (cartao) pancada(raiz, f.u);
        if (etq) revela(etq, f.u);
        if (h) revela(h, f.u);
        bs.forEach(b => varrer(b, f.u - (BR ? 0.05 : 0.3)));
        if (animar) animar(t, f);
        if (!BR) {
          const s = E.inCubic(f.pout);
          raiz.style.opacity = String(1 - s);
          raiz.style.translate = `0 ${(-24 * s).toFixed(2)}px`;
        }
        return true;
      },
    };
  }

  // ------------------------------------------------------------ componentes
  const FAB = {};

  FAB.frase = ev => {
    const raiz = el('div', `el frase ${ev.tamanho || 'm'}${ev.alinhar === 'centro' ? ' centro-x' : ''}`);
    const etq = ev.etiqueta ? el('div', 'etiqueta', textoEtiqueta(ev)) : null;
    if (etq) { raiz.appendChild(etq); raiz.appendChild(el('br')); }
    const ws = [];
    let negrito = false;
    String(ev.texto).split('\n').forEach((linha, li) => {
      if (li) raiz.appendChild(el('br'));
      linha.split(/\s+/).filter(Boolean).forEach(tok => {
        const n = (tok.match(/\*\*/g) || []).length;
        const b = negrito || tok.startsWith('**');
        // pontuação depois do ** fica fora do destaque: **dividendos**. -> [dividendos].
        const m = tok.match(/^(.*\*\*)([.,!?:;]+)$/);
        const corpo = (m ? m[1] : tok).replace(/\*\*/g, '');
        const pont = m ? m[2] : '';
        if (n % 2 === 1) negrito = !negrito;
        const w = el('span', 'w', `<span>${b ? `<b>${esc(corpo)}</b>${esc(pont)}` : esc(corpo + pont)}</span>`);
        raiz.appendChild(w);
        ws.push({ no: w.firstChild, b: w.querySelector('b') });
      });
    });
    let sub = null;
    if (ev.sub) { sub = el('div', 'sub', marcar(ev.sub)); raiz.appendChild(sub); }
    const tempos = ev.tempos || ws.map((_, i) => ev.inicio + i * (BR ? 0.05 : 0.07));
    return {
      raiz, tremor: BR && (ev.tamanho || 'm') === 'g' ? 8 : 0,
      atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.3, ev.segura ? 0 : saida());
        if (!f) return false;
        if (etq) revela(etq, f.u);
        ws.forEach((w, i) => {
          const u = t - tempos[i];
          if (BR) {
            w.no.style.transform = u >= 0 ? 'none' : 'translateY(110%)';
          } else {
            const p = E.outCubic(clamp(u / 0.3));
            const s = E.inCubic(clamp(f.pout * 1.4 - i * 0.03));
            w.no.style.transform = `translateY(${105 * (1 - p) - 105 * s}%)`;
          }
          if (w.b) varrer(w.b, u - (BR ? 0.03 : 0.2));
        });
        if (sub) revela(sub, t - (ev.sub_em ?? tempos[tempos.length - 1] + 0.2));
        return true;
      },
    };
  };

  FAB.numero = ev => bloco(ev, 'numero' + (ev.alinhar === 'centro' ? ' centro-x' : ''), raiz => {
    const topo = ev.topo ? el('div', 'topo', marcar(ev.topo)) : null;
    const v = el('div', 'valor');
    const txt = el('span', 'txt', esc(ev.valor));
    v.appendChild(txt);
    const rot = ev.rotulo ? el('div', 'rotulo', marcar(ev.rotulo)) : null;
    const fonte = ev.fonte ? el('div', 'fonte', esc(ev.fonte)) : null;
    [topo, v, rot, fonte].forEach(n => n && raiz.appendChild(n));
    const n = ev.contar === false ? null : lerNumero(ev.valor);
    const dc = ev.contagem ?? 0.9;
    const modo = ev.caneta === false ? null : (ev.caneta || 'sublinha');
    const pen = !BR && modo ? caneta(v, modo, semente(ev.id)) : null;
    // o círculo da caneta precisa de folga para não invadir a margem nem o rótulo de cima
    if (pen && modo === 'circula') v.style.margin = ev.alinhar === 'centro' ? '24px 0 18px' : '24px 0 18px 36px';
    return {
      medir() { caber(v, larguraUtil(raiz) - (pen && modo === 'circula' ? 110 : 0), 110); if (pen) pen.medir(); },
      animar(t, f) {
        if (topo) revela(topo, f.u);
        if (BR) {
          v.style.visibility = 'visible';
        } else {
          const p = E.outCubic(clamp((f.u - 0.04) / 0.36));
          v.style.transform = `translateY(${(1 - p) * 40}px)`;
          v.style.clipPath = p >= 1 ? 'none' : `inset(-30% ${(1 - p) * 100}% -30% -10%)`;
        }
        if (n) {
          const p = contar(f.u - 0.1, dc);
          txt.textContent = p >= 1 ? ev.valor : fmtNumero(n, lerp(ev.de ?? 0, n.val, p));
        }
        if (pen) pen.desenhar(f.u - (n ? 0.1 + dc : 0.45));
        if (rot) revela(rot, f.u - (BR ? 0 : 0.35));
        if (fonte) revela(fonte, f.u - (BR ? 0 : 0.5), 0.25, 20);
      },
    };
  }, { tremor: 9 });

  // quadro de conta: cada linha aparece quando o número é dito, o resultado ganha a caneta
  FAB.conta = ev => bloco(ev, 'conta', raiz => {
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
      animar(t, f) {
        for (const o of objs) {
          const u = t - o.l.em;
          if (o.regra) {
            const pr = BR ? (u >= 0 ? 1 : 0) : E.inOutCubic(clamp(u / 0.24));
            o.regra.style.transform = `scaleX(${pr})`;
          }
          const ue = o.regra ? u - (BR ? 0 : 0.16) : u;
          const dEsc = Math.min(0.42, 0.05 + o.n * 0.022);
          const p = ue <= 0 ? 0 : (BR ? 1 : clamp(ue / dEsc));
          const pc = p >= 1 ? 1 : Math.floor(p * o.n) / o.n;   // escreve caractere por caractere
          o.ln.style.visibility = ue >= 0 ? 'visible' : 'hidden';
          o.tt.style.clipPath = pc >= 1 ? 'none' : `inset(-30% ${(1 - pc) * 100}% -30% 0)`;
          if (o.pen) o.pen.desenhar(ue - dEsc - 0.08);
        }
        if (fonte) revela(fonte, t - Math.max(...objs.map(o => o.l.em), ev.inicio) - 0.6, 0.25, 20);
      },
    };
  });

  FAB.icone = ev => bloco(ev, 'icone ico', raiz => {
    const disco = el('div', 'disco', svgIcone(ev.icone, 250));
    raiz.appendChild(disco);
    pintarTracos(disco);
    const rot = ev.rotulo ? el('div', 'rot', marcar(ev.rotulo)) : null;
    if (rot) raiz.appendChild(rot);
    const svg = disco.querySelector('svg');
    return (t, f) => {
      if (BR) pancada(disco, f.u);
      else disco.style.clipPath = `circle(${(entra(f.u, 0.42) * 75).toFixed(2)}% at 50% 50%)`;
      desenharIcone(svg, f.u - (BR ? 0 : 0.12));
      if (rot) revela(rot, f.u - (BR ? 0 : 0.25));
    };
  }, { tremor: 9 });

  FAB.icones = ev => bloco(ev, 'icones ico', raiz => {
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
    return t => {
      for (const o of cels) {
        const u = t - o.it.em;
        o.c.style.visibility = u >= 0 ? 'visible' : 'hidden';
        if (BR && u >= 0) pancada(o.disco, u, 10);
        else o.disco.style.clipPath = `circle(${(entra(u, 0.38) * 75).toFixed(2)}% at 50% 50%)`;
        desenharIcone(o.svg, u - (BR ? 0 : 0.1), 0.45);
        revela(o.rot, u - (BR ? 0 : 0.2));
      }
    };
  });

  const BOCA = { feliz: 'M-24 6 Q0 30 24 6', preocupado: 'M-20 22 Q0 6 20 22', neutro: 'M-18 14 L18 14' };
  FAB.personagem = ev => bloco(ev, 'personagem', raiz => {
    const fig = el('div', 'fig');
    fig.style.position = 'relative';
    fig.innerHTML = `
      <svg width="360" height="420" viewBox="-180 -60 360 420" style="overflow:visible">
        <g class="corpo-g">
          <path class="corpo" d="M-150 360 C-150 220 -90 170 0 170 C90 170 150 220 150 360 Z"/>
          <g class="cab"><circle cx="0" cy="60" r="100" fill="var(--tinta)"/>
            <g class="olhos"><circle cx="-36" cy="50" r="12" fill="var(--base)"/><circle cx="36" cy="50" r="12" fill="var(--base)"/></g>
            <path class="boca" d="${BOCA[ev.humor] || BOCA.neutro}" transform="translate(0 90)" fill="none" stroke="var(--base)" stroke-width="9" stroke-linecap="round"/>
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
    const r = mulberry32(semente(ev.id));
    const piscadas = [];
    for (let k = 0, tt = ev.inicio + 0.8 + r() * 1.5; k < 40; k++, tt += 2.2 + r() * 2.4) piscadas.push(tt);
    return (t, f) => {
      const s = entra(f.u, 0.45);
      const resp = BR ? 0 : Math.sin((t - ev.inicio) * 2.2) * 5;
      corpo.style.transform = `translateY(${(1 - s) * 260 + resp}px)`;
      corpo.style.transformOrigin = '0 360px';
      cab.style.transform = BR ? '' : `rotate(${Math.sin((t - ev.inicio) * 1.6) * 2}deg)`;
      cab.style.transformOrigin = '0 160px';
      const pis = piscadas.some(p => t >= p && t < p + 0.12);
      olhos.style.transform = `scaleY(${pis ? 0.12 : 1})`;
      olhos.style.transformOrigin = '0 50px';
      fig.style.clipPath = 'inset(-400px -400px 0 -400px)';
      if (nome) revela(nome, f.u - (BR ? 0 : 0.3));
      if (desc) revela(desc, f.u - (BR ? 0 : 0.42));
      if (balao) {
        const ub = t - (ev.balao_em ?? ev.inicio + 0.6);
        balao.style.display = ub >= 0 ? 'block' : 'none';
        if (BR) pancada(balao, ub, 10);
        else balao.style.clipPath = `inset(0 ${((1 - entra(ub, 0.3)) * 100).toFixed(2)}% 0 0)`;
      }
    };
  });

  FAB.comparacao = ev => bloco(ev, 'comparacao', raiz => {
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
      return { l, box, barra, num, n: l.texto ? lerNumero(l.texto) : null };
    });
    return t => {
      for (const o of objs) {
        const u = t - o.l.em;
        const p = BR ? (u >= 0 ? 1 : 0) : E.outExpo(clamp(u / 0.8));
        o.barra.style.transform = `scaleX(${p})`;
        if (o.n) o.num.textContent = u < 0 ? '' : (p >= 1 ? o.l.texto : fmtNumero(o.n, o.n.val * p));
      }
    };
  });

  FAB.grafico = ev => bloco(ev, 'grafico', raiz => {
    const W = BR ? 790 : 900, H = 520, padT = 60, padB = 70, padL = 10;
    const vals = ev.valores || [0, 1];
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const xs = vals.map((_, i) => padL + (i / (vals.length - 1)) * (W - padL - 30));
    const ys = vals.map(v => padT + (1 - (v - lo) / (hi - lo || 1)) * (H - padT - padB));
    const d = xs.map((x, i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(' ');
    const area = `${d} L${xs[xs.length - 1]} ${H - padB} L${xs[0]} ${H - padB} Z`;
    const rot = ev.rotulos || [];
    const xF = xs[xs.length - 1], yF = ys[ys.length - 1];
    let grade = '';
    if (!BR) {   // papel milimetrado dentro da área do gráfico
      for (let x = padL; x <= W; x += 30) grade += `<line x1="${x}" y1="${padT - 30}" x2="${x}" y2="${H - padB}" stroke="#9966FF" stroke-opacity="${(x - padL) % 150 === 0 ? 0.32 : 0.14}" stroke-width="1.5"/>`;
      for (let y = H - padB; y >= padT - 30; y -= 30) grade += `<line x1="${padL}" y1="${y}" x2="${W}" y2="${y}" stroke="#9966FF" stroke-opacity="${(H - padB - y) % 150 === 0 ? 0.32 : 0.14}" stroke-width="1.5"/>`;
    }
    raiz.insertAdjacentHTML('beforeend', `
      <svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
        <g class="grade">${grade}</g>
        ${BR ? `<path class="area" d="${area}" fill="#EBFF70" stroke="#000" stroke-width="5"/>` : ''}
        <line class="eixo-x" x1="${padL}" y1="${H - padB}" x2="${W}" y2="${H - padB}" pathLength="1" stroke="${BR ? '#000' : '#FFFFFF'}" stroke-opacity="${BR ? 1 : 0.85}" stroke-width="${BR ? 6 : 3}"/>
        <line class="eixo-y" x1="${padL}" y1="${H - padB}" x2="${padL}" y2="${padT - 30}" pathLength="1" stroke="${BR ? '#000' : '#FFFFFF'}" stroke-opacity="${BR ? 1 : 0.85}" stroke-width="${BR ? 6 : 3}"/>
        <path class="ln" d="${d}" pathLength="1" fill="none" stroke="${BR ? '#000' : '#FFFFFF'}" stroke-width="${BR ? 12 : 8}" stroke-linecap="${BR ? 'square' : 'round'}" stroke-linejoin="${BR ? 'miter' : 'round'}"/>
        ${BR ? `<rect class="pt" x="${xF - 16}" y="${yF - 16}" width="32" height="32" fill="#000"/>`
             : `<circle class="pt" cx="${xF}" cy="${yF}" r="15" fill="#EBFF70"/>`}
        <rect class="fundo-final" fill="#EBFF70" width="0" height="0"/>
        <text class="final" x="${xF - 40}" y="${yF + 22}" text-anchor="end">${esc(ev.final ?? '')}</text>
        <path class="pen" pathLength="1" fill="none" stroke="#EBFF70" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
        <text class="eixo-t" x="${padL}" y="${H - 16}">${esc(rot[0] ?? '')}</text>
        <text class="eixo-t" x="${W}" y="${H - 16}" text-anchor="end">${esc(rot[rot.length - 1] ?? '')}</text>
      </svg>`);
    const q = s => raiz.querySelector(s);
    const ln = q('.ln'), ar = q('.area'), pt = q('.pt'), fin = q('.final'), pen = q('.pen'), ff = q('.fundo-final');
    const eixos = [q('.eixo-x'), q('.eixo-y')], grd = q('.grade');
    const desenho = ev.desenho ?? 1.6;
    const nPts = vals.length - 1;
    return {
      medir() {
        const bb = fin.getBBox();
        if (BR) { ff.setAttribute('x', bb.x - 10); ff.setAttribute('y', bb.y - 2); ff.setAttribute('width', bb.width + 20); ff.setAttribute('height', bb.height + 4); }
        else pen.setAttribute('d', tracoCaneta(bb.width, bb.height, semente(ev.id), 'circula', bb.x, bb.y));
      },
      animar(t, f) {
        const ue = f.u - 0.1;
        eixos.forEach(e => { e.style.strokeDasharray = '1'; e.style.strokeDashoffset = String(1 - (BR ? (ue >= 0 ? 1 : 0) : E.inOutCubic(clamp(ue / 0.35)))); });
        if (!BR) grd.style.opacity = String(E.outCubic(clamp(ue / 0.35)));
        // Blueprint: traço contínuo. Brutalista: um segmento por vez, seco
        const pr = clamp((f.u - 0.3) / desenho);
        const p = BR ? Math.floor(pr * nPts) / nPts : E.inOutCubic(pr);
        ln.style.strokeDasharray = '1';
        ln.style.strokeDashoffset = String(1 - p);
        if (ar) ar.style.clipPath = `inset(0 ${100 * (1 - p)}% 0 0)`;
        const fd = 0.3 + desenho;
        const uf = f.u - fd;
        pt.style.visibility = uf >= 0 ? 'visible' : 'hidden';
        fin.style.visibility = uf >= 0 ? 'visible' : 'hidden';
        if (BR) { ff.style.visibility = uf >= 0 ? 'visible' : 'hidden'; pen.style.display = 'none'; }
        else {
          fin.style.clipPath = `inset(0 0 0 ${(1 - entra(uf, 0.3)) * 100}%)`;
          const pp = uf - 0.35 <= 0 ? 0 : E.inOutCubic(clamp((uf - 0.35) / 0.5));
          pen.style.strokeDasharray = '1';
          pen.style.strokeDashoffset = String(1 - pp);
          pen.style.visibility = pp > 0 ? 'visible' : 'hidden';
          ff.style.display = 'none';
        }
      },
    };
  });

  FAB.moedas = ev => bloco(ev, 'moedas', raiz => {
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
    return t => {
      for (const o of cols) {
        o.coins.forEach((m, k) => {
          const u = t - o.c.em - k * o.passo;
          m.style.visibility = u >= 0 ? 'visible' : 'hidden';
          m.style.transform = BR ? '' : `translateY(${(-(1 - E.outCubic(clamp(u / 0.24))) * 110).toFixed(2)}px)`;
        });
        revela(o.val, t - (o.c.em + o.coins.length * o.passo + (BR ? 0 : 0.24)), 0.25, 30);
      }
    };
  });

  const CHECK = '<svg viewBox="0 0 68 68"><path d="M18 35 L30 47 L51 22" pathLength="1" fill="none" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  FAB.lista = ev => bloco(ev, 'lista', raiz => {
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
    return t => {
      for (const o of itens) {
        const u = t - o.it.em;
        o.mask.style.display = u >= 0 ? 'block' : 'none';
        o.vazio.style.display = u >= 0 ? 'none' : 'block';
        if (BR) {
          o.mask.style.clipPath = ''; o.txt.style.transform = '';
          o.path.style.strokeDasharray = '1';
          o.path.style.strokeDashoffset = u >= 0 ? '0' : '1';
          o.chk.style.background = u >= 0 ? '#EBFF70' : '#FFF';
          if (u >= 0) pancada(o.chk, u, 0);
          else { o.chk.style.translate = ''; o.chk.style.scale = ''; o.chk.style.boxShadow = 'none'; }
        } else {
          const v = clamp(u / 0.32);
          o.mask.style.clipPath = `inset(0 ${100 * (1 - E.outCubic(v))}% 0 0)`;
          o.txt.style.transform = `translateX(${-30 * (1 - E.outCubic(v))}px)`;
          const c = clamp((u - 0.08) / 0.28);
          o.path.style.strokeDasharray = '1';
          o.path.style.strokeDashoffset = String(1 - E.inOutCubic(c));
        }
      }
    };
  });

  FAB.linha_tempo = ev => bloco(ev, 'tempo', raiz => {
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
    const barra = eixo.firstChild;
    return t => {
      let alcance = -1;
      marcos.forEach((o, k) => {
        const u = t - o.m.em;
        if (u >= 0) alcance = k;
        const p = entra(u, 0.3);
        o.ponto.style.visibility = u >= 0 ? 'visible' : 'hidden';
        o.ponto.style.transform = `scale(${BR ? 1 : 0.4 + 0.6 * p})`;
        revela(o.q, u - (BR ? 0 : 0.05));
        revela(o.o, u - (BR ? 0 : 0.15));
      });
      let frac = 0;
      if (alcance > 0) {
        const prox = BR ? 1 : E.inOutCubic(clamp((t - marcos[alcance].m.em) / 0.4));
        frac = (alcance - 1 + prox) / (n - 1);
      }
      barra.style.transform = `scaleY(${clamp(frac)})`;
    };
  });

  FAB.rosca = ev => bloco(ev, 'rosca', raiz => {
    const segs = ev.segmentos || [];
    const tot = segs.reduce((a, s) => a + s.valor, 0) || 1;
    let acc = 0;
    const cores = BR ? ['#000000', '#9966FF'] : ['#9966FF', 'rgba(153,102,255,.42)'];
    const circ = segs.map((s, k) => {
      const ini = acc; acc += 100 * s.valor / tot;
      return { s, ini, tam: 100 * s.valor / tot, cor: s.destaque ? '#EBFF70' : cores[k % 2] };
    });
    const fundoAnel = BR ? '#EDEDED' : 'rgba(153,102,255,.14)';
    raiz.insertAdjacentHTML('beforeend', `
      <svg width="560" height="560" viewBox="-280 -280 560 560">
        <circle r="200" fill="none" stroke="${fundoAnel}" stroke-width="80"/>
        ${circ.map((c, k) => `<circle class="sg" data-k="${k}" r="200" fill="none" stroke="${c.cor}" stroke-width="80" pathLength="100" transform="rotate(${-90 + c.ini * 3.6})"/>`).join('')}
        ${BR ? '<circle r="242" fill="none" stroke="#000" stroke-width="6"/><circle r="158" fill="none" stroke="#000" stroke-width="6"/>' : ''}
        <text class="centro" y="48" text-anchor="middle">${esc(ev.centro ?? '')}</text>
      </svg>`);
    const leg = el('div', 'leg', circ.map(c => `<span><i style="background:${c.cor}"></i>${marcar(c.s.rotulo)}</span>`).join(''));
    raiz.appendChild(leg);
    const sgs = [...raiz.querySelectorAll('.sg')], centro = raiz.querySelector('.centro');
    return (t, f) => {
      sgs.forEach((g, k) => {
        const c = circ[k];
        const u = t - c.s.em;
        const p = BR ? (u >= 0 ? 1 : 0) : E.inOutCubic(clamp(u / 0.6));
        g.style.strokeDasharray = `${c.tam * p} 100`;
      });
      const uc = f.u - (BR ? 0 : 0.5);
      centro.style.visibility = uc >= 0 ? 'visible' : 'hidden';
      centro.style.transform = BR ? '' : `translateY(${(1 - entra(uc, 0.3)) * 20}px)`;
      revela(leg, f.u - (BR ? 0 : 0.6));
    };
  });

  FAB.carimbo = ev => {
    const raiz = el('div', 'el carimbo' + (ev.destaque ? ' dest' : ''));
    const selo = el('div', 'selo', esc(ev.texto));
    selo.style.setProperty('--giro', (ev.giro ?? -7) + 'deg');
    raiz.appendChild(selo);
    return {
      raiz, tremor: BR ? 14 : 0,
      atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.1, ev.segura ? 0 : saida());
        if (!f) return false;
        const k = 1 - E.outCubic(clamp(f.u / 0.09));   // bate de cima: 1,5x para 1x em 3 quadros
        selo.style.scale = String(1 + 0.5 * k);
        return true;
      },
    };
  };

  FAB.sticker = ev => {
    const raiz = el('div', 'el sticker' + (ev.alinhar === 'esquerda' ? ' esq' : ''));
    const s = el('div', 's', marcar(ev.texto));
    const r = mulberry32(semente(ev.id));
    const giro = ev.giro ?? ((r() < 0.5 ? -1 : 1) * (4 + r() * 4));
    s.style.setProperty('--giro', giro.toFixed(1) + 'deg');
    raiz.appendChild(s);
    return {
      raiz,
      atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.1, ev.segura ? 0 : saida());
        if (!f) return false;
        s.style.scale = String(1 + 0.25 * (1 - E.outCubic(clamp(f.u / 0.08))));
        return true;
      },
    };
  };

  FAB.cta = ev => bloco(ev, 'cta', raiz => {
    const c = el('div', 'caixa', marcar(ev.texto));
    raiz.appendChild(c);
    return (t, f) => {
      if (BR) { c.style.visibility = 'visible'; return; }
      const p = entra(f.u, 0.38);
      c.style.clipPath = `inset(0 ${(1 - p) * 100}% 0 0)`;
      c.style.transform = `translateX(${(-24 * (1 - p)).toFixed(2)}px)`;
    };
  }, { oculta_legenda: true, tremor: 9 });

  FAB.aviso = ev => {
    const raiz = el('div', 'el aviso');
    const s = el('span', '', esc(ev.texto));
    raiz.appendChild(s);
    return {
      raiz, atualizar(t) {
        const f = fase(t, ev.inicio, ev.fim, 0.25, ev.segura ? 0 : saida());
        if (!f) return false;
        const p = BR ? 1 : E.outCubic(f.pin) * (1 - E.inCubic(f.pout));
        s.style.clipPath = `inset(0 ${100 * (1 - p)}% 0 0)`;
        return true;
      },
    };
  };

  // ------------------------------------------------------------ papel quadriculado (Blueprint)
  function montarPapel() {
    const papel = $('papel');
    papel.innerHTML = '';
    linhasPapel = [];
    if (BR) return;
    const passo = 67.5, nV = Math.round(1080 / passo), nH = Math.ceil(1920 / passo);
    let svg = `<svg width="1080" height="1920">`;
    for (let i = 0; i <= nH; i++) {
      const y = (i * passo).toFixed(1);
      svg += `<line class="${i % 4 === 0 ? 'mj' : 'mn'}" data-ini="${(0.02 + (i / nH) * 0.45).toFixed(3)}" x1="0" y1="${y}" x2="1080" y2="${y}" pathLength="1"/>`;
    }
    for (let j = 0; j <= nV; j++) {
      const x = (j * passo).toFixed(1);
      svg += `<line class="${j % 4 === 0 ? 'mj' : 'mn'}" data-ini="${(0.12 + (j / nV) * 0.45).toFixed(3)}" x1="${x}" y1="0" x2="${x}" y2="1920" pathLength="1"/>`;
    }
    papel.innerHTML = svg + '</svg>';
    linhasPapel = [...papel.querySelectorAll('line')].map(no => ({ no, ini: parseFloat(no.dataset.ini) }));
  }
  function desenharPapel(t) {
    const d = P.papel_instantaneo ? 0 : 0.6;
    for (const l of linhasPapel) {
      const p = d === 0 ? 1 : E.inOutCubic(clamp((t - l.ini) / d));
      l.no.style.strokeDasharray = '1';
      l.no.style.strokeDashoffset = String(1 - p);
    }
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

  // ------------------------------------------------------------ API
  window.carregar = async function (plano) {
    P = plano;
    BR = P.estilo === 'brutalista';
    document.body.className = BR ? 'brutalista' : 'blueprint';
    await Promise.all(["300 80px 'Barlow'", "600 80px 'Barlow'", "700 80px 'Barlow'", "500 40px 'JetBrains Mono'",
      "700 40px 'JetBrains Mono'", "400 80px 'Archivo Black'"].map(f => document.fonts.load(f)));
    await document.fonts.ready;
    const visiveis = (P.palavras || []).filter(w => String(w.texto).trim() !== '');
    grupos = (P.legenda && P.legenda.ativa === false) ? [] : montarGrupos(visiveis, P.legenda || {});
    montarPapel();
    const raizCenas = $('cenas');
    raizCenas.innerHTML = '';
    cenas = [];
    tremores = [];
    const medidas = [];
    for (const cfg of P.cenas) {
      const fundo = cfg.fundo || (BR ? 'cinza' : 'papel');
      const raiz = el('div', `cena t-${fundo}`);
      const conteudo = el('div', 'conteudo');
      raiz.append(conteudo);
      raizCenas.appendChild(raiz);
      const elems = [];
      for (const ev of cfg.elementos) {
        if (!FAB[ev.tipo]) continue;
        const c = FAB[ev.tipo](ev);
        c.ev = ev;
        conteudo.appendChild(c.raiz);
        elems.push(c);
      }
      // mede e posiciona: alto = 360, centro = centralizado em 800, baixo = base em 1190
      raiz.style.display = 'block';
      for (const c of elems) {
        mostrar(c, true);
        if (c.medir) c.medir();
        const h = c.raiz.offsetHeight;
        mostrar(c, false);
        const pos = c.ev.pos || (c.ev.tipo === 'sticker' ? 'alto' : 'centro');
        let top = c.ev.y ?? (pos === 'alto' ? 360 : pos === 'baixo' ? 1190 - h : Math.round(800 - h / 2));
        if (c.ev.tipo === 'aviso' && c.ev.y === undefined) top = 1392;
        if (c.ev.tipo === 'cta' && c.ev.y === undefined) top = 1250;
        c.raiz.style.top = top + 'px';
        medidas.push({ id: c.ev.id, tipo: c.ev.tipo, topo: top, altura: h });
        if (c.tremor > 0) {
          const r = mulberry32(semente('tremor:' + c.ev.id));
          tremores.push({ ini: c.ev.inicio, amp: c.tremor, offs: [...Array(6)].map(() => [r() * 2 - 1, r() * 2 - 1]) });
        }
      }
      raiz.style.display = 'none';
      cenas.push({ cfg, raiz, conteudo, elems });
    }
    $('guias').style.display = P.guias ? 'block' : 'none';
    window.pronto = true;
    return medidas;
  };

  function desenharCena(c, t, tEl) {
    const cfg = c.cfg;
    c.raiz.style.display = 'block';
    if (!BR) {   // respiração de câmera só no Blueprint
      const dur = Math.max(cfg.fim - cfg.inicio, 0.5);
      c.conteudo.style.transform = `scale(${1 + 0.025 * clamp((t - cfg.inicio) / dur)})`;
    }
    let oculta = false;
    for (const e of c.elems) {
      const vis = e.atualizar(tEl);
      mostrar(e, vis);
      if (vis && e.oculta_legenda) oculta = true;
    }
    return oculta;
  }

  window.seek = async function (t) {
    if (!BR) desenharPapel(t);
    let idx = 0;
    for (let i = 0; i < cenas.length; i++) if (t >= cenas[i].cfg.inicio) idx = i;
    const atual = cenas[idx];
    const ant = idx > 0 ? cenas[idx - 1] : null;
    const tr = atual.cfg.transicao || 'corte';
    const dTr = tr === 'corte' ? 0 : (atual.cfg.dur_transicao ?? (tr === 'bloco' ? 0.12 : 0.5));
    const emTr = ant && t < atual.cfg.inicio + dTr;
    const bruto = emTr ? clamp((t - atual.cfg.inicio) / dTr) : 1;
    const p = tr === 'bloco' ? bruto : E.inOutCubic(bruto);

    for (const c of cenas) {
      c.raiz.style.display = 'none';
      c.raiz.style.transform = '';
      c.raiz.style.clipPath = '';
      c.raiz.style.zIndex = '0';
    }
    const regua = $('regua');
    regua.style.display = 'none';
    let oculta = false;
    if (emTr) {
      // a cena que sai congela no último instante dela
      oculta = desenharCena(ant, t, Math.min(t, ant.cfg.fim - 0.001)) || oculta;
      ant.raiz.style.zIndex = '1';
      if (tr === 'empurra') ant.raiz.style.transform = `translateY(${-p * 100}%)`;
      if (tr === 'lateral') ant.raiz.style.transform = `translateX(${-p * 100}%)`;
      if (tr === 'cortina' && !BR) ant.raiz.style.clipPath = `inset(0 0 ${p * 100}% 0)`;
    }
    oculta = desenharCena(atual, t, t) || oculta;
    atual.raiz.style.zIndex = '2';
    if (emTr) {
      const [ox, oy] = atual.cfg.origem || [540, 900];
      if (tr === 'cortina') {
        atual.raiz.style.clipPath = `inset(${(1 - p) * 100}% 0 0 0)`;
        if (!BR) { regua.style.display = 'block'; regua.style.top = ((1 - p) * 1920 - 2).toFixed(1) + 'px'; }
      }
      if (tr === 'circulo') atual.raiz.style.clipPath = `circle(${p * 2250}px at ${ox}px ${oy}px)`;
      if (tr === 'empurra') atual.raiz.style.transform = `translateY(${(1 - p) * 100}%)`;
      if (tr === 'lateral') atual.raiz.style.transform = `translateX(${(1 - p) * 100}%)`;
      if (tr === 'bloco') atual.raiz.style.clipPath = `inset(0 0 0 ${(1 - p) * 100}%)`;
    }

    // tremor de tela (Brutalista), com semente: mesmo quadro, mesmo deslocamento
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

    for (const [a, b] of (P.legenda && P.legenda.ocultar) || []) if (t >= a && t < b) oculta = true;
    atualizarLegenda(t, oculta);
    return true;
  };
})();
