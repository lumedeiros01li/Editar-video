/* Ícones de traço, grade 48x48, desenhados para esta skill (sem marcas de terceiros).
 * Cada traço usa pathLength="1": o motor desenha o ícone animando o tracejado de 1 a 0.
 * Traços com classe "d" ficam na cor de destaque. */
window.ICONES = {
  moeda: '<circle cx="24" cy="24" r="18"/><path class="d" d="M24 13v22"/><path class="d" d="M29.5 18c-1.4-1.6-3.3-2.4-5.5-2.4-3.1 0-5.2 1.6-5.2 4.1 0 2.6 2.6 3.4 5.2 4.1 2.7.8 5.3 1.6 5.3 4.3 0 2.5-2.2 4.3-5.4 4.3-2.3 0-4.3-.8-5.8-2.4"/>',
  casa: '<path d="M7 23 24 9l17 14"/><path d="M12 19v21h24V19"/><path class="d" d="M20 40V29h8v11"/>',
  carro: '<path d="M6 33v-7l5-9h26l5 9v7z"/><path d="M6 26h36"/><circle class="d" cx="14" cy="36" r="4"/><circle class="d" cx="34" cy="36" r="4"/>',
  calendario: '<rect x="8" y="11" width="32" height="29" rx="3"/><path d="M8 19h32"/><path d="M16 7v8"/><path d="M32 7v8"/><path class="d" d="M16 27h4M24 27h4M16 33h4"/>',
  relogio: '<circle cx="24" cy="24" r="17"/><path class="d" d="M24 14v10l7 5"/>',
  cofre: '<rect x="7" y="9" width="34" height="30" rx="3"/><circle class="d" cx="24" cy="24" r="7"/><path class="d" d="M24 17v4"/><path d="M12 39v3M36 39v3"/>',
  grafico_sobe: '<path d="M6 40h36"/><path class="d" d="M10 32l9-9 7 6 12-14"/><path class="d" d="M31 15h7v7"/>',
  grafico_desce: '<path d="M6 40h36"/><path class="d" d="M10 14l9 9 7-6 12 14"/><path class="d" d="M31 31h7v-7"/>',
  carteira: '<rect x="6" y="13" width="36" height="25" rx="4"/><path class="d" d="M34 22h8v8h-8a4 4 0 0 1 0-8z"/><path d="M10 13l20-6 3 6"/>',
  escudo: '<path d="M24 6l15 6v11c0 9-6.5 16-15 19-8.5-3-15-10-15-19V12z"/><path class="d" d="M17 24l5 5 9-10"/>',
  alvo: '<circle cx="24" cy="24" r="17"/><circle cx="24" cy="24" r="10"/><circle class="d" cx="24" cy="24" r="3"/>',
  pessoa: '<circle cx="24" cy="15" r="7"/><path class="d" d="M10 41c1-8 7-12 14-12s13 4 14 12"/>',
  familia: '<circle cx="17" cy="15" r="5"/><circle cx="33" cy="18" r="4"/><path d="M7 40c1-7 5-10 10-10s9 3 10 10"/><path class="d" d="M27 40c.5-5 3-8 6-8s6 3 7 8"/>',
  cartao: '<rect x="5" y="12" width="38" height="25" rx="4"/><path d="M5 20h38"/><path class="d" d="M11 30h9"/>',
  porcentagem: '<path class="d" d="M12 36L36 12"/><circle cx="15" cy="15" r="4"/><circle cx="33" cy="33" r="4"/>',
  alerta: '<path d="M24 7L43 40H5z"/><path class="d" d="M24 19v10"/><path class="d" d="M24 34v1"/>',
  lampada: '<path d="M18 31c-4-3-6-7-6-11a12 12 0 0 1 24 0c0 4-2 8-6 11v4H18z"/><path class="d" d="M19 40h10"/>',
  ampulheta: '<path d="M13 7h22M13 41h22"/><path class="d" d="M15 7c0 9 9 11 9 17s-9 8-9 17"/><path class="d" d="M33 7c0 9-9 11-9 17s9 8 9 17"/>',
  check: '<circle cx="24" cy="24" r="18"/><path class="d" d="M15 25l6 6 12-13"/>',
  xis: '<circle cx="24" cy="24" r="18"/><path class="d" d="M17 17l14 14M31 17L17 31"/>',
  maleta: '<rect x="6" y="15" width="36" height="24" rx="3"/><path d="M18 15v-4h12v4"/><path class="d" d="M6 26h36"/>',
  imposto: '<path d="M12 6h18l8 8v28H12z"/><path d="M30 6v8h8"/><path class="d" d="M18 30L30 20"/><circle class="d" cx="19" cy="21" r="2"/><circle class="d" cx="29" cy="29" r="2"/>',
  saude: '<path d="M24 40S8 31 8 19a8 8 0 0 1 16-3 8 8 0 0 1 16 3c0 12-16 21-16 21z"/><path class="d" d="M14 24h6l3-5 4 9 3-4h4"/>',
  dolar: '<rect x="5" y="13" width="38" height="22" rx="3"/><circle class="d" cx="24" cy="24" r="6"/><path d="M11 18v12M37 18v12"/>',
};
