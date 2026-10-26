// Renderiza quadros: node render.cjs <saida> [lista,de,quadros]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = __dirname, OUT = process.argv[2];
const list0 = process.argv[3] ? process.argv[3].split(',').map(Number) : null;
const workers = Number(process.env.WORKERS || 3), TOTAL = Math.round(62.3 * 30);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.woff2': 'font/woff2' };
const srv = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
});
(async () => {
  await new Promise(r => srv.listen(8766, r));
  const browser = await chromium.launch();
  const list = list0 || [...Array(TOTAL).keys()];
  fs.mkdirSync(OUT, { recursive: true });
  let next = 0, done = 0; const t0 = Date.now();
  async function work() {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
    page.on('pageerror', e => console.log('PAGEERR:', e.message));
    page.on('console', m => { if (m.type() === 'error') console.log('PAGE:', m.text()); });
    await page.goto('http://localhost:8766/index.html');
    await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
    while (next < list.length) {
      const f = list[next++];
      const url = await page.evaluate(async f => { await window.renderFrame(f); return document.getElementById('c').toDataURL('image/jpeg', 0.94); }, f);
      fs.writeFileSync(path.join(OUT, String(f).padStart(5, '0') + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
      if (++done % 100 === 0) console.log(done, '/', list.length, ((Date.now() - t0) / done).toFixed(0), 'ms/q');
    }
  }
  await Promise.all([...Array(workers)].map(work));
  await browser.close(); srv.close(); console.log('ok', done, ((Date.now() - t0) / 1000).toFixed(1) + 's');
})();
