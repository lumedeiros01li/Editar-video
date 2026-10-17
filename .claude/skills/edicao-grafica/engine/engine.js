/* Motor de composição da skill edicao-grafica.
 *
 * Contrato: window.seek(t) desenha o quadro do instante t (segundos).
 * Tudo é função pura de t. Nada de transição CSS, setTimeout,
 * requestAnimationFrame ou estado carregado de um quadro para o outro.
 * Cada seek reescreve todas as propriedades animadas de todas as camadas.
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
  // mola amortecida analítica (u em segundos). Passa um pouco de 1 e assenta.
  function mola(u, z = 0.6, w = 16) {
    if (u <= 0) return 0;
    const wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * u) * (Math.cos(wd * u) + (z * w / wd) * Math.sin(wd * u));
  }
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

  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  // **destaque** vira roxo, [[PALAVRA]] vira chip
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
  function fase(t, ini, fim, din, dout) {
    if (t < ini || t >= fim) return null;
    return { u: t - ini, pin: clamp((t - ini) / din), pout: clamp((t - (fim - dout)) / dout) };
  }

  // número em pt-BR: "R$ 1.250,50" -> {pre:"R$ ", val:1250.5, dec:2, grupo:true, suf:""}
  function lerNumero(txt) {
    const m = String(txt).match(/-?\d[\d.]*(?:,\d+)?/);
    if (!m) return null;
    const bruto = m[0];
    const [int, frac] = bruto.split(',');
    return {
      pre: txt.slice(0, m.index), suf: txt.slice(m.index + bruto.length),
      val: parseFloat(int.replace(/\./g, '') + (frac ? '.' + frac : '')),
      dec: frac ? frac.length : 0, grupo: int.includes('.'),
    };
  }
  function fmtNumero(n, v) {
    return n.pre + v.toLocaleString('pt-BR', {
      minimumFractionDigits: n.dec, maximumFractionDigits: n.dec, useGrouping: n.grupo,
    }) + n.suf;
  }

  // ------------------------------------------------------------ estado fixo
  let P = null;          // plano resolvido (somente leitura)
  let grupos = [];       // grupos de legenda (derivados do plano, fixos)
  let comps = [];        // componentes: {ev, raiz, atualizar(t)}
  const $ = id => document.getElementById(id);

  // ------------------------------------------------------------ componentes
  const FAB = {};

  FAB.titulo = ev => {
    const raiz = el('div', 'camada titulo');
    const t = el('div', 't', marcar(ev.texto));
    raiz.appendChild(t);
    raiz.style.top = (ev.y ?? 380) + 'px';
    return {
      raiz, atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.34, 0.22);
        if (!f) return false;
        const dir = 100 * (1 - E.outExpo(f.pin));
        const sai = 100 * E.inCubic(f.pout);
        raiz.style.clipPath = `inset(0 ${dir}% 0 ${sai}% round 24px)`;
        t.style.transform = `translateX(${-28 * (1 - E.outCubic(clamp((f.u - 0.06) / 0.34)))}px)`;
        return true;
      },
    };
  };

  FAB.palavra = ev => {
    const raiz = el('div', 'camada palavra');
    const linha = el('div', 'linha');
    const letras = [...String(ev.texto)].map(c => {
      const s = el('span', 'l', c === ' ' ? '&nbsp;' : esc(c));
      linha.appendChild(s);
      return s;
    });
    const barra = el('div', 'barra');
    raiz.append(linha, barra);
    raiz.style.top = (ev.y ?? 780) + 'px';
    return {
      raiz, atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.3, 0.22);
        if (!f) return false;
        letras.forEach((s, i) => {
          const d = clamp((f.u - i * 0.028) / 0.3);
          const saida = E.inCubic(clamp(f.pout * 1.3 - i * 0.04));
          s.style.transform = `translateY(${110 * (1 - E.outCubic(d)) - 110 * saida}%)`;
        });
        const b = E.outExpo(clamp((f.u - 0.12) / 0.4)) * (1 - E.inCubic(f.pout));
        barra.style.transform = `scaleX(${b})`;
        return true;
      },
    };
  };

  // base comum dos cartões brancos: sobe com mola e se revela de baixo para cima
  function cartao(ev, montar) {
    const raiz = el('div', 'camada cartao ' + ev.tipo);
    if (ev.topo) raiz.appendChild(el('div', 'topo', marcar(ev.topo)));
    if (ev.titulo) raiz.appendChild(el('div', 'h', marcar(ev.titulo)));
    const animarConteudo = montar(raiz);
    return {
      raiz, cartao: true,
      atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.34, 0.2);
        if (!f) return false;
        const s = mola(f.u, 0.62, 15);
        const sai = E.inCubic(f.pout);
        const rev = 100 * (1 - E.outExpo(clamp(f.u / 0.34)));
        raiz.style.clipPath = `inset(${rev}% 0 0 0 round 32px)`;
        raiz.style.transform = `translateY(${(1 - s) * 70 + sai * 40}px) scale(${0.94 + 0.06 * s - 0.04 * sai})`;
        raiz.style.opacity = String(1 - sai);
        animarConteudo(tm, f);
        return true;
      },
    };
  }

  FAB.numero = ev => cartao(ev, raiz => {
    const v = el('div', 'valor', esc(ev.valor));
    raiz.appendChild(v);
    if (ev.rotulo) raiz.appendChild(el('div', 'rotulo', marcar(ev.rotulo)));
    if (ev.fonte) raiz.appendChild(el('div', 'fonte', esc(ev.fonte)));
    const n = ev.contar === false ? null : lerNumero(ev.valor);
    const de = ev.de ?? 0;
    const dur = ev.contagem ?? 0.9;
    return (tm, f) => {
      if (!n) return;
      const p = E.outExpo(clamp((f.u - 0.1) / dur));
      v.textContent = p >= 1 ? ev.valor : fmtNumero(n, lerp(de, n.val, p));
    };
  });

  const CHECK = '<svg viewBox="0 0 52 52"><path d="M14 27 L23 36 L39 17" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  FAB.lista = ev => cartao(ev, raiz => {
    const itens = (ev.itens || []).map(it => {
      const linha = el('div', 'item');
      const chk = el('div', 'chk', CHECK);
      const mask = el('div', 'mask');
      const txt = el('div', 'txt', marcar(it.texto));
      const vazio = el('div', 'vazio');
      mask.appendChild(txt);
      linha.append(chk, mask, vazio);
      raiz.appendChild(linha);
      return { it, linha, chk, path: chk.querySelector('path'), mask, txt, vazio };
    });
    return tm => {
      for (const o of itens) {
        const v = clamp((tm - o.it.em) / 0.3);
        // antes da vez, o item aparece como esqueleto: caixa vazia e traço cinza
        o.mask.style.display = tm >= o.it.em ? 'block' : 'none';
        o.vazio.style.display = tm >= o.it.em ? 'none' : 'block';
        o.mask.style.clipPath = `inset(0 ${100 * (1 - E.outExpo(v))}% 0 0)`;
        o.txt.style.transform = `translateX(${-40 * (1 - E.outCubic(v))}px)`;
        const c = clamp((tm - o.it.em - 0.05) / 0.25);
        o.path.style.strokeDasharray = '40';
        o.path.style.strokeDashoffset = String(40 * (1 - E.outCubic(c)));
        o.chk.style.background = c > 0 ? 'var(--roxo)' : 'var(--roxo-claro)';
        o.chk.style.transform = `scale(${1 + 0.12 * Math.sin(Math.PI * c)})`;
      }
    };
  });

  FAB.comparacao = ev => cartao(ev, raiz => {
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
        const p = E.outExpo(clamp((tm - o.l.em) / 0.75));
        o.barra.style.transform = `scaleX(${p})`;
        if (o.n) o.num.textContent = p >= 1 ? o.l.texto : (tm < o.l.em ? '' : fmtNumero(o.n, o.n.val * p));
      }
    };
  });

  FAB.grafico = ev => cartao(ev, raiz => {
    const W = 716, H = 420, padT = 40, padB = 60;
    const vals = ev.valores || [0, 1];
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const xs = vals.map((_, i) => (i / (vals.length - 1)) * (W - 30));
    const ys = vals.map(v => padT + (1 - (v - lo) / (hi - lo || 1)) * (H - padT - padB));
    const d = xs.map((x, i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(' ');
    const area = `${d} L${xs[xs.length - 1]} ${H - padB} L0 ${H - padB} Z`;
    const rot = ev.rotulos || [];
    const xF = xs[xs.length - 1], yF = ys[ys.length - 1];
    const box = el('div', 'grafico', `
      <svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
        <path class="area" d="${area}" fill="#F1EBFF"/>
        <line x1="0" y1="${H - padB}" x2="${W}" y2="${H - padB}" stroke="#D0D0D0" stroke-width="3"/>
        <path class="ln" d="${d}" fill="none" stroke="#9966FF" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
        <circle class="pt" cx="${xF}" cy="${yF}" r="16" fill="#9966FF"/>
        <text class="final" x="${xF - 34}" y="${yF + 20}" text-anchor="end">${esc(ev.final ?? '')}</text>
        <text class="eixo" x="0" y="${H - 10}">${esc(rot[0] ?? '')}</text>
        <text class="eixo" x="${W}" y="${H - 10}" text-anchor="end">${esc(rot[rot.length - 1] ?? '')}</text>
      </svg>`);
    raiz.appendChild(box);
    const ln = box.querySelector('.ln'), ar = box.querySelector('.area');
    const pt = box.querySelector('.pt'), fin = box.querySelector('.final');
    let L = null;
    const desenho = ev.desenho ?? 1.4;
    return (tm, f) => {
      if (L === null) L = ln.getTotalLength();
      const p = E.inOutCubic(clamp((f.u - 0.3) / desenho));
      ln.style.strokeDasharray = String(L);
      ln.style.strokeDashoffset = String(L * (1 - p));
      ar.style.clipPath = `inset(0 ${100 * (1 - p)}% 0 0)`;
      const fimDesenho = 0.3 + desenho;
      const s = mola(f.u - fimDesenho, 0.5, 18);
      pt.style.transformOrigin = `${xF}px ${yF}px`;
      pt.style.transform = `scale(${f.u > fimDesenho ? s : 0})`;
      fin.style.opacity = f.u > fimDesenho ? String(clamp((f.u - fimDesenho) / 0.15)) : '0';
    };
  });

  FAB.emoji = ev => {
    const raiz = el('div', 'camada emoji', esc(ev.emoji));
    raiz.style.left = (ev.x ?? 860) + 'px';
    raiz.style.top = (ev.y ?? 1120) + 'px';
    return {
      raiz, atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.3, 0.16);
        if (!f) return false;
        const s = mola(f.u, 0.42, 20) * (1 - E.inCubic(f.pout));
        raiz.style.transform = `scale(${s}) rotate(${(1 - mola(f.u, 0.5, 14)) * -18}deg)`;
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
        const f = fase(tm, ev.inicio, ev.fim, 0.25, 0.2);
        if (!f) return false;
        const p = E.outCubic(f.pin) * (1 - E.inCubic(f.pout));
        s.style.transform = `translateY(${(1 - p) * 16}px)`;
        s.style.clipPath = `inset(0 ${100 * (1 - p)}% 0 0 round 10px)`;
        return true;
      },
    };
  };

  FAB.cta = ev => {
    const raiz = el('div', 'camada cta');
    const c = el('div', 'caixa', marcar(ev.texto));
    raiz.appendChild(c);
    return {
      raiz, oculta_legenda: true, atualizar(tm) {
        const f = fase(tm, ev.inicio, ev.fim, 0.34, 0.2);
        if (!f) return false;
        const s = mola(f.u, 0.5, 15);
        const sai = E.inCubic(f.pout);
        c.style.transform = `translateY(${(1 - s) * 50 + sai * 30}px) scale(${0.86 + 0.14 * s})`;
        c.style.clipPath = `inset(${100 * (1 - E.outExpo(clamp(f.u / 0.3)))}% 0 0 0 round 24px)`;
        c.style.opacity = String(1 - sai);
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
      const k = clamp((t - w.ini) / 0.09);
      return `<span class="p ativo" style="transform:scale(${1 + 0.06 * Math.sin(Math.PI * k)})">${esc(w.texto)}</span>`;
    }).join('');
    const v = E.outCubic(clamp((t - g.ini + 0.04) / 0.14));
    box.style.transform = `translateY(${16 * (1 - v)}px) scale(${0.94 + 0.06 * v})`;
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
      if (ev.modo === 'seco') s = ev.escala;
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
    await Promise.all([
      document.fonts.load("700 80px 'Barlow'"), document.fonts.load("600 80px 'Barlow'"),
      document.fonts.load("500 40px 'Inter'"), document.fonts.load("700 40px 'Inter'"),
      document.fonts.load("800 40px 'Inter'"),
    ]);
    await document.fonts.ready;
    // palavras com texto vazio continuam existindo para os índices, mas não entram na legenda
    // (ex.: "mil e sessenta" vira uma palavra "R$ 1.060" + duas vazias)
    const visiveis = (P.palavras || []).filter(w => String(w.texto).trim() !== '');
    grupos = (P.legenda && P.legenda.ativa === false) ? [] : montarGrupos(visiveis, P.legenda || {});
    const cam = $('camadas');
    cam.innerHTML = '';
    comps = [];
    for (const ev of P.eventos) {
      if (!FAB[ev.tipo]) continue;
      const c = FAB[ev.tipo](ev);
      c.ev = ev;
      cam.appendChild(c.raiz);
      comps.push(c);
    }
    // posiciona cartões: centro em y=900, base nunca abaixo de 1190, topo nunca acima de 330
    for (const c of comps) {
      if (!c.cartao) continue;
      c.raiz.style.display = 'block';
      const h = c.raiz.offsetHeight;
      c.raiz.style.display = 'none';
      const top = c.ev.y ?? Math.round(Math.max(330, Math.min(900 - h / 2, 1190 - h)));
      c.raiz.style.top = top + 'px';
      c.altura = h;
      c.topo = top;
    }
    $('guias').style.display = P.guias ? 'block' : 'none';
    window.pronto = true;
    return comps.filter(c => c.cartao).map(c => ({ id: c.ev.id, tipo: c.ev.tipo, topo: c.topo, altura: c.altura }));
  };

  window.seek = async function (t) {
    // fundo
    const img = $('frame');
    const src = quadroDoFundo(t);
    if (img.getAttribute('src') !== src) img.setAttribute('src', src);
    const { s, foco } = escalaFundo(t);
    const bg = $('bg');
    bg.style.transformOrigin = `${foco[0]}px ${foco[1]}px`;
    bg.style.transform = `scale(${s})`;

    // camadas
    let veu = 0, ocultar = false;
    for (const c of comps) {
      const vis = c.atualizar(t);
      c.raiz.style.display = vis ? 'block' : 'none';
      if (!vis) continue;
      if (c.oculta_legenda) ocultar = true;
      const alvo = c.ev.veu ?? (c.cartao ? 0.35 : (c.ev.tipo === 'palavra' ? 0.45 : 0));
      if (alvo > 0) {
        const f = fase(t, c.ev.inicio, c.ev.fim, 0.3, 0.2);
        veu = Math.max(veu, alvo * E.outCubic(f.pin) * (1 - E.inCubic(f.pout)));
      }
    }
    $('veu').style.opacity = String(veu);
    for (const [a, b] of (P.legenda && P.legenda.ocultar) || []) if (t >= a && t < b) ocultar = true;
    atualizarLegenda(t, ocultar);

    if (img.getAttribute('src')) { try { await img.decode(); } catch (e) { /* quadro ausente */ } }
    return true;
  };
})();
