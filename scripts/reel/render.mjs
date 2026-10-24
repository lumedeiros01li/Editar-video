import { createRequire } from 'node:module';
const require = createRequire('/opt/node22/lib/node_modules/');
const { chromium } = require('playwright');
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const ROOT = process.argv[2], OUT = process.argv[3];
const only = process.argv[4] ? process.argv[4].split(',').map(Number) : null;
const workers = Number(process.env.WORKERS || 3);
const types = { '.html': 'text/html', '.json': 'application/json', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2' };
const srv = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => srv.listen(8766, r));
const browser = await chromium.launch();
fs.mkdirSync(OUT, { recursive: true });
let list = only, next = 0, done = 0; const t0 = Date.now();
async function work(wi) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.log('PAGEERR:', e.message));
  page.on('console', m => { if (m.type() === 'error') console.log('PAGE:', m.text()); });
  await page.goto('http://localhost:8766/scene.html');
  await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
  if (!list) list = [...Array(await page.evaluate(() => window.NFRAMES)).keys()];
  // contiguous chunks per worker keep the frame cache warm
  const n = list.length, a = Math.floor(n * wi / workers), b = Math.floor(n * (wi + 1) / workers);
  for (let i = a; i < b; i++) {
    const f = list[i];
    const url = await page.evaluate(f => window.renderFrame(f), f);
    fs.writeFileSync(path.join(OUT, String(f + 1).padStart(5, '0') + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
    if (++done % 100 === 0) console.log(done, 'frames', ((Date.now() - t0) / done).toFixed(0), 'ms/frame');
  }
}
// first worker resolves the list
const pages=[...Array(workers).keys()];
if(!list){const p=await browser.newPage();await p.goto("http://localhost:8766/scene.html");await p.waitForFunction(()=>window.READY===true,null,{timeout:120000});list=[...Array(await p.evaluate(()=>window.NFRAMES)).keys()];await p.close();}
await Promise.all(pages.map(work));
await browser.close(); srv.close(); console.log("done",done,((Date.now()-t0)/1000).toFixed(1),"s");
