// Modelo de dados e de tempo do Reel. Usado por index.html (quadro) e audio.mjs (sons),
// então ticks de ano e visual nascem da mesma linha do tempo.

export const FPS = 30;
export const DUR = 26;
export const N_FRAMES = FPS * DUR;

export const T_INI = 1.5;      // começa o crescimento
export const T_DESACEL = 15.5; // começa a desacelerar
export const T_FIM = 17.5;     // congela
export const T_CTA = 22;       // entra o CTA

export const Y_MIN = 90;
export const TIP_FRAC = 0.85;  // ponta do Brasil em ~85% da altura útil
export const TIP_TETO = 0.92;  // teto duro
export const PASSOS = [2, 5, 10, 20, 50, 100, 200, 500];
export const MAX_LINHAS = 6;
export const MARCOS = [200, 300, 400];
export const MARCO_DUR = 2;    // s visível
export const MARCO_ANIM = 6 / FPS;
export const GRADE_ANIM = 10 / FPS;

// Interpolação monótona por trechos (Fritsch-Carlson), x com passo 1
function pchip(ys) {
  const n = ys.length;
  const del = [];
  for (let i = 0; i < n - 1; i++) del.push(ys[i + 1] - ys[i]);
  const d = new Array(n).fill(0);
  for (let i = 1; i < n - 1; i++) {
    if (del[i - 1] * del[i] > 0) d[i] = 2 / (1 / del[i - 1] + 1 / del[i]);
  }
  const ponta = (a, b) => {
    let s = (3 * a - b) / 2;
    if (Math.sign(s) !== Math.sign(a)) s = 0;
    else if (Math.sign(a) !== Math.sign(b) && Math.abs(s) > 3 * Math.abs(a)) s = 3 * a;
    return s;
  };
  d[0] = ponta(del[0], del[1]);
  d[n - 1] = ponta(del[n - 2], del[n - 3]);
  return (x) => {
    if (x <= 0) return ys[0];
    if (x >= n - 1) return ys[n - 1];
    const i = Math.floor(x), t = x - i;
    const t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * d[i] +
           (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * d[i + 1];
  };
}

export function construir(dados) {
  const anos = [];
  for (let a = dados.ano_inicial; a <= dados.ano_final; a++) anos.push(a);
  const P_MAX = anos.length - 1;
  const ids = Object.keys(dados.paises);
  const serie = {}, interp = {};
  for (const id of ids) {
    serie[id] = anos.map((a) => dados.paises[id].indice_base_2000[String(a)]);
    interp[id] = pchip(serie[id]);
  }
  // ordem vertical das bandeiras: fixa, pelo valor final (de baixo para cima)
  const ordem = [...ids].sort((a, b) => serie[a][P_MAX] - serie[b][P_MAX]);

  // progresso (em anos) em função do tempo: constante, depois desacelera até 1/3
  const v0 = P_MAX / ((T_DESACEL - T_INI) + (2 / 3) * 2 * (T_FIM - T_DESACEL) / 2);
  const progresso = (t) => {
    if (t <= T_INI) return 0;
    if (t >= T_FIM) return P_MAX;
    if (t <= T_DESACEL) return v0 * (t - T_INI);
    const s = t - T_DESACEL, L = T_FIM - T_DESACEL;
    return v0 * ((T_DESACEL - T_INI) + s - (s * s) / (3 * L));
  };
  const tempoDe = (p) => {
    if (p <= 0) return T_INI;
    const p1 = v0 * (T_DESACEL - T_INI);
    if (p <= p1) return T_INI + p / v0;
    const L = T_FIM - T_DESACEL, c = (p - p1) / v0;
    const s = (3 * L / 2) * (1 - Math.sqrt(1 - (4 * c) / (3 * L)));
    return T_DESACEL + s;
  };
  const valor = (id, p) => interp[id](p);

  // tabela do máximo do eixo Y por quadro (suavizado uma vez, aqui no build)
  const alvo = (t) => Y_MIN + (valor('BRA', progresso(t + 0.15)) - Y_MIN) / TIP_FRAC;
  const M = new Float64Array(N_FRAMES + 1);
  let m = alvo(0);
  for (let i = 0; i <= N_FRAMES; i++) {
    const t = i / FPS;
    m += 0.2 * (alvo(t) - m);
    const piso = Y_MIN + (valor('BRA', progresso(t)) - Y_MIN) / TIP_TETO;
    M[i] = Math.max(m, piso);
  }
  const Mt = (t) => {
    const f = Math.min(Math.max(t * FPS, 0), N_FRAMES);
    const i = Math.min(Math.floor(f), N_FRAMES - 1);
    return M[i] + (M[i + 1] - M[i]) * (f - i);
  };

  // passo da grade por quadro (nunca diminui) e eventos de troca
  const contar = (s, mx) => Math.floor(mx / s) - Math.ceil(Y_MIN / s) + 1;
  const passoQ = [];
  let atual = PASSOS[0];
  for (let i = 0; i <= N_FRAMES; i++) {
    let s = PASSOS.find((x) => contar(x, M[i]) <= MAX_LINHAS) ?? PASSOS[PASSOS.length - 1];
    if (s < atual) s = atual;
    atual = s;
    passoQ.push(s);
  }
  const familia = {}; // passo -> {ini, fim} em segundos
  passoQ.forEach((s, i) => {
    const t = i / FPS;
    if (!familia[s]) familia[s] = { ini: i === 0 ? null : t, fim: null };
    if (i > 0 && passoQ[i - 1] !== s) familia[passoQ[i - 1]].fim = t;
  });
  const rampa = (x) => Math.min(Math.max(x, 0), 1);
  const presenca = (v, t) => {
    // devolve {modo:'cheia'|'entra'|'sai', f} ou null
    let melhor = null;
    for (const [sStr, fam] of Object.entries(familia)) {
      const s = Number(sStr);
      if (Math.abs(v / s - Math.round(v / s)) > 1e-9) continue;
      // a família nova só entra depois que a antiga saiu (sem rótulos sobrepostos)
      const on = fam.ini === null ? 1 : rampa((t - fam.ini - GRADE_ANIM) / GRADE_ANIM);
      const off = fam.fim === null ? 0 : rampa((t - fam.fim) / GRADE_ANIM);
      if (on <= 0) continue;
      if (off >= 1) continue;
      let r;
      if (off > 0) r = { modo: 'sai', f: off };
      else if (on < 1) r = { modo: 'entra', f: on };
      else r = { modo: 'cheia', f: 1 };
      if (!melhor || r.modo === 'cheia' || (melhor.modo !== 'cheia' && r.modo === 'entra')) melhor = r;
    }
    return melhor;
  };

  // marcos do Brasil: primeiro ano de dado em que o índice cruza o limiar
  const marcos = [];
  for (const lim of MARCOS) {
    const k = serie.BRA.findIndex((x) => x >= lim);
    if (k < 0) continue;
    marcos.push({ limiar: lim, mult: lim / 100, k, ano: anos[k], t: tempoDe(k), texto: `BRASIL: ${lim / 100}X EM ${anos[k]}` });
  }
  // um tick por ano de dado, tom sobe com o índice do Brasil
  const ticks = anos.map((ano, k) => ({ k, ano, t: tempoDe(k), brasil: serie.BRA[k] }));

  return { anos, P_MAX, ids, ordem, serie, valor, progresso, tempoDe, Mt, M, passoQ, familia, presenca,
           marcos, ticks, v0, Y_MIN };
}
