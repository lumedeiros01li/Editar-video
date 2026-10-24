// Modelo de dados e de tempo do Reel "R$ 100 em 2000". Usado por index.html (quadro) e audio.mjs (sons).

export const FPS = 30;
export const DUR = 16.4;
export const N_FRAMES = Math.round(FPS * DUR);

// roteiro (s)
export const T_CORRIDA = 1;      // começa a corrida
export const LENTO_2008 = [4, 5];   // câmera lenta em 2008
export const LENTO_2018 = [7.5, 8.5];
export const T_CONGELA = 10.5;   // linhas congeladas, "QUAL FICOU EM 1º?"
export const T_REVELA = 11.5;    // começam as revelações
export const PASSO_REVELA = 0.6;
export const T_RANKING = 14.5;   // ranking parado
export const T_VOLTA = 16.0;     // rebobina para o primeiro quadro (loop)
export const T_VOLTA_FIM = 16.3;
export const FLASH_DUR = 1.2;

export const Y_MIN = 60;          // abaixo do menor valor da série (S&P 74 em 2009)
export const TIP_FRAC = 0.85;
export const TIP_TETO = 0.92;
export const MAX_LINHAS = 6;
export const GRADE_ANIM = 8 / FPS;
export const ATIVOS = ['POU', 'CDI', 'OURO', 'IBOV', 'SPX'];
export const LINHAS = ['IPCA', ...ATIVOS]; // a inflação entra em cinza
// ordem dos rótulos enquanto todos valem 100 (de baixo para cima): neutra, para não entregar o ranking
export const ORDEM_NEUTRA = ['IPCA', 'SPX', 'POU', 'OURO', 'IBOV', 'CDI'];
export const FRAC_INICIO = 0.45; // antes da corrida, o 100 fica no meio do gráfico

// interpolação monótona por trechos (Fritsch-Carlson) com x arbitrário
export function pchip(xs, ys) {
  const n = xs.length, h = [], del = [];
  for (let i = 0; i < n - 1; i++) { h.push(xs[i + 1] - xs[i]); del.push((ys[i + 1] - ys[i]) / h[i]); }
  const d = new Array(n).fill(0);
  for (let i = 1; i < n - 1; i++) {
    if (del[i - 1] * del[i] > 0) {
      const w1 = 2 * h[i] + h[i - 1], w2 = h[i] + 2 * h[i - 1];
      d[i] = (w1 + w2) / (w1 / del[i - 1] + w2 / del[i]);
    }
  }
  const ponta = (h0, h1, d0, d1) => {
    let s = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1);
    if (Math.sign(s) !== Math.sign(d0)) s = 0;
    else if (Math.sign(d0) !== Math.sign(d1) && Math.abs(s) > 3 * Math.abs(d0)) s = 3 * d0;
    return s;
  };
  if (n > 2) {
    d[0] = ponta(h[0], h[1], del[0], del[1]);
    d[n - 1] = ponta(h[n - 2], h[n - 3], del[n - 2], del[n - 3]);
  } else { d[0] = d[1] = del[0]; }
  return (x) => {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0;
    while (x > xs[i + 1]) i++;
    const hh = h[i], t = (x - xs[i]) / hh, t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * hh * d[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * hh * d[i + 1];
  };
}

export function construir(dados, opcoes = {}) {
  const ALTURA = opcoes.altura ?? 946;
  const eixo = opcoes.eixo === 'linear' ? 'linear' : 'log';
  const pos = dados.posicao;
  const P_MAX = pos[pos.length - 1];
  const anoBase = dados.base.ano;
  const ids = Object.keys(dados.series);
  const serie = {}, interp = {};
  for (const id of ids) { serie[id] = dados.series[id].valores; interp[id] = pchip(pos, serie[id]); }
  const valor = (id, p) => interp[id](p);
  const final = (id) => serie[id][serie[id].length - 1];
  const idx = (ano) => dados.anos.indexOf(String(ano)); // índice do ano no vetor

  // progresso (anos desde a base) em função do tempo: nós do roteiro, ligados por spline monótona
  // 1-4 s: 2000 a 2007 | 4-5 s: 2008 em câmera lenta | 5-7,5 s: até 2017 | 7,5-8,5 s: 2018 lento | 8,5-10,5 s: até set/2026
  const nos = [[0, 0], [T_CORRIDA, 0], [LENTO_2008[0], idx(2007)], [LENTO_2008[1], idx(2008)], [LENTO_2018[0], idx(2017)],
    [LENTO_2018[1], idx(2018)], [T_CONGELA, P_MAX], [T_VOLTA, P_MAX]];
  const curva = pchip(nos.map((n) => n[0]), nos.map((n) => n[1]));
  const ease = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x));
  const progresso = (t) => {
    if (t >= T_VOLTA) return P_MAX * (1 - ease((t - T_VOLTA) / (T_VOLTA_FIM - T_VOLTA)));
    return curva(Math.max(0, t));
  };
  // primeiro instante em que o progresso atinge p (só na corrida)
  const tempoDe = (p) => {
    let a = T_CORRIDA, b = T_CONGELA;
    if (p <= 0) return T_CORRIDA;
    for (let k = 0; k < 60; k++) { const m = (a + b) / 2; if (curva(m) < p) a = m; else b = m; }
    return b;
  };
  const anoNaTela = (p) => anoBase + Math.min(dados.anos.length - 1, Math.max(0, Math.ceil(p - 1e-9)));

  // eixo log ou linear: fração da altura útil e máximo que põe um valor numa fração
  const frac = eixo === 'log' ? (v, mx) => Math.log(v / Y_MIN) / Math.log(mx / Y_MIN) : (v, mx) => (v - Y_MIN) / (mx - Y_MIN);
  const maxPara = eixo === 'log' ? (v, f) => Y_MIN * Math.pow(v / Y_MIN, 1 / f) : (v, f) => Y_MIN + (v - Y_MIN) / f;
  const lider = (p) => Math.max(...LINHAS.map((id) => valor(id, p)));
  // máximo acumulado do líder: o eixo só cresce na corrida (a queda de 2008 não encolhe a escala)
  const liderAcum = (p) => { let m = 0; for (let q = 0; q < p; q += 0.05) m = Math.max(m, lider(q)); return Math.max(m, lider(p)); };

  // tabela do máximo do eixo por quadro, suavizada em log (build), rebobinagem interpolada até o quadro 0
  const M = new Float64Array(N_FRAMES + 1);
  const gIni = Math.log(maxPara(lider(0), FRAC_INICIO));
  let g = gIni;
  for (let i = 0; i <= N_FRAMES; i++) {
    const t = i / FPS;
    if (t < T_VOLTA) {
      // o eixo parte da escala inicial (100 no meio) e só cresce quando o líder pede
      const alvo = Math.max(gIni, Math.log(maxPara(liderAcum(progresso(Math.min(t + 0.15, T_VOLTA - 1e-6))), TIP_FRAC)));
      g += 0.22 * (alvo - g);
      const piso = Math.log(maxPara(liderAcum(progresso(t)), TIP_TETO));
      M[i] = Math.exp(Math.max(g, piso));
    }
  }
  const iVolta = Math.ceil(T_VOLTA * FPS);
  const gV = Math.log(M[iVolta - 1]), g0 = Math.log(M[0]);
  for (let i = iVolta; i <= N_FRAMES; i++) {
    const e = ease((i / FPS - T_VOLTA) / (T_VOLTA_FIM - T_VOLTA));
    M[i] = Math.exp(gV + (g0 - gV) * e);
  }
  const Mt = (t) => M[Math.min(Math.max(Math.round(t * FPS), 0), N_FRAMES)];

  // famílias de grade: múltiplos simples no começo, depois 1-2-5 por década (melhor no log)
  const mult = (s) => ({ nome: `x${s}`, tem: (v) => Math.abs(v / s - Math.round(v / s)) < 1e-9,
    valores: (mx) => { const r = []; for (let v = Math.ceil(Y_MIN / s) * s; v <= mx + 1e-9; v += s) r.push(v); return r; } });
  const d125 = [100, 200, 500, 1000, 2000, 5000, 10000, 20000];
  const familias = eixo === 'log'
    ? [mult(5), mult(10), mult(20), mult(50), mult(100), { nome: '1-2-5', tem: (v) => d125.includes(v), valores: (mx) => d125.filter((v) => v <= mx + 1e-9) }]
    : [mult(5), mult(10), mult(20), mult(50), mult(100), mult(200), mult(500), mult(1000), mult(2000)];
  const viavel = (f, mx) => {
    const vs = f.valores(mx);
    if (vs.length > MAX_LINHAS) return false;
    const todos = [...new Set([...vs, 100])].sort((a, b) => a - b);
    for (let i = 1; i < todos.length; i++) if (ALTURA * (frac(todos[i], mx) - frac(todos[i - 1], mx)) < 54) return false;
    return true;
  };
  const famQ = [];
  let atual = 0;
  for (let i = 0; i <= N_FRAMES; i++) {
    const t = i / FPS;
    const livre = familias.findIndex((f) => viavel(f, M[i]));
    const escolha = livre < 0 ? familias.length - 1 : livre;
    atual = t >= T_VOLTA ? escolha : Math.max(atual, escolha); // na corrida a grade só engrossa
    famQ.push(atual);
  }
  const inicioRun = [];
  famQ.forEach((f, i) => inicioRun.push(i > 0 && famQ[i - 1] === f ? inicioRun[i - 1] : i));
  // presença de uma linha de grade: a família antiga sai, depois a nova entra
  const presenca = (v, t) => {
    const i = Math.min(Math.max(Math.round(t * FPS), 0), N_FRAMES);
    const cur = familias[famQ[i]], ini = inicioRun[i];
    const ant = ini > 0 ? familias[famQ[ini - 1]] : null;
    const d = (i - ini) / FPS;
    const naCur = cur.tem(v), naAnt = ant ? ant.tem(v) : false;
    if (!ant || t >= T_VOLTA) return naCur ? { modo: 'cheia', f: 1 } : null;
    if (naCur && naAnt) return { modo: 'cheia', f: 1 };
    if (naAnt && d < GRADE_ANIM) return { modo: 'sai', f: d / GRADE_ANIM };
    if (naCur && d >= GRADE_ANIM) return d >= 2 * GRADE_ANIM ? { modo: 'cheia', f: 1 } : { modo: 'entra', f: (d - GRADE_ANIM) / GRADE_ANIM };
    return null;
  };
  const candidatos = (t) => {
    const i = Math.min(Math.max(Math.round(t * FPS), 0), N_FRAMES);
    const mx = M[i], ini = inicioRun[i];
    const vs = new Set(familias[famQ[i]].valores(mx));
    if (ini > 0) familias[famQ[ini - 1]].valores(mx).forEach((v) => vs.add(v));
    return [...vs].sort((a, b) => a - b);
  };

  // flashes do roteiro, com os números calculados dos dados
  const pct = (r) => `${r > 0 ? '+' : ''}${Math.round(r * 100)}%`;
  const ret = (id, ano) => dados.series[id].retornos[idx(ano) - 1];
  // ano a partir do qual o S&P fica sempre acima da poupança (em 2002 ele passou e depois voltou a ficar abaixo)
  let kSpx = -1;
  for (let k = serie.SPX.length - 1; k > 0 && serie.SPX[k] > serie.POU[k]; k--) kSpx = k;
  const anoSpx = Number(dados.anos[kSpx]);
  const flashes = [
    { ano: 2008, t: tempoDe(idx(2007)), texto: `2008: IBOVESPA ${pct(ret('IBOV', 2008))}` },
    { ano: anoSpx, t: tempoDe(idx(anoSpx) - 1), texto: `${anoSpx}: S&P PASSA A POUPANÇA` },
    { ano: 2024, t: tempoDe(idx(2023)), texto: `2024: DÓLAR ${pct(ret('USD', 2024))}` },
  ];
  // revelações do último ao primeiro; a inflação entra junto com o último ativo
  const ordemFinal = [...ATIVOS].sort((a, b) => final(a) - final(b));
  const revela = { IPCA: T_REVELA };
  ordemFinal.forEach((id, k) => { revela[id] = T_REVELA + k * PASSO_REVELA; });
  const vencedor = ordemFinal[ordemFinal.length - 1];
  // poupança acima da inflação, ao ano
  const acima = Math.pow(final('POU') / final('IPCA'), 1 / dados.anos_periodo) - 1;
  // ticks: um por troca do ano na tela
  const ticks = [];
  for (let k = 0; k < dados.anos.length - 1; k++) ticks.push({ k, ano: anoBase + k + 1, t: tempoDe(k + 1e-9) });

  return { ids, serie, valor, final, progresso, tempoDe, anoNaTela, frac, Mt, M, famQ, familias, presenca, candidatos,
    flashes, revela, ordemFinal, vencedor, acima, ticks, P_MAX, anoBase, lider, eixo };
}
