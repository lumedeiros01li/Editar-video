// Servidor estático local e abertura da página com Playwright, compartilhados por render e verificações.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

export const AQUI = path.dirname(fileURLToPath(import.meta.url));

export function carregarPlaywright() {
  const req = createRequire(import.meta.url);
  for (const alvo of ['playwright', '/opt/node-tools/node_modules/playwright']) {
    try { return req(alvo); } catch { /* tenta o próximo */ }
  }
  throw new Error('Playwright não encontrado. Rode: npm i playwright');
}

export function servidor() {
  const tipos = { '.html': 'text/html; charset=utf-8', '.mjs': 'text/javascript', '.json': 'application/json', '.woff2': 'font/woff2', '.jpg': 'image/jpeg' };
  const srv = http.createServer((rq, rs) => {
    const arq = path.join(AQUI, decodeURIComponent(rq.url.split('?')[0]).replace(/^\/+/, '') || 'index.html');
    if (!arq.startsWith(AQUI) || !fs.existsSync(arq) || fs.statSync(arq).isDirectory()) { rs.writeHead(404); return rs.end(); }
    rs.writeHead(200, { 'content-type': tipos[path.extname(arq)] || 'application/octet-stream' });
    fs.createReadStream(arq).pipe(rs);
  });
  return new Promise((ok) => srv.listen(0, '127.0.0.1', () => ok({ srv, url: `http://127.0.0.1:${srv.address().port}/index.html` })));
}

export async function abrir(browser, url) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto(url);
  await page.waitForFunction('window.__ready === true', null, { timeout: 30000 });
  return page;
}
