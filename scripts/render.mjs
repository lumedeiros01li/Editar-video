import { chromium } from 'playwright-core';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const ROOT = process.argv[2], OUT = process.argv[3];
const frames = process.argv[4] ? process.argv[4].split(',').map(Number) : null;
const workers = Number(process.env.WORKERS || 2);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png' };
const srv = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => srv.listen(8765, r));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const total = JSON.parse(fs.readFileSync(path.join(ROOT, 'scene_data.json'))).head.length;
const list = frames || [...Array(total).keys()];
fs.mkdirSync(OUT, { recursive: true });
let next = 0, done = 0; const t0 = Date.now();
async function work() {
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('console', m => { if (m.type() === 'error') console.log('PAGE:', m.text()); });
  page.on('pageerror', e => console.log('PAGEERR:', e.message));
  await page.goto('http://localhost:8765/r3d/scene.html');
  await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
  while (next < list.length) {
    const f = list[next++];
    const url = await page.evaluate(f => window.renderFrame(f), f);
    fs.writeFileSync(path.join(OUT, String(f + 1).padStart(5, '0') + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
    if (++done % 50 === 0) console.log(done, 'frames', ((Date.now() - t0) / done).toFixed(0), 'ms/frame');
  }
}
await Promise.all([...Array(workers)].map(work));
await browser.close(); srv.close();
console.log('done', done, ((Date.now() - t0) / 1000).toFixed(1), 's');
