// Frame-accurate renderer for a film page that follows the contract in SKILL.md:
//   window.DUR (seconds), window.seek(t, frame), optional window.fontsReady (Promise).
// The film's folder is served over http (fonts need it), so keep fonts and assets next to film.html.
//
//   node render.mjs stills <film.html> <t1,t2,...> <outDir>        one PNG per time
//   node render.mjs full   <film.html> <outDir> [fps=120] [workers=4]  chunk0..N.mp4 for assemble.sh
//
// Env: CHROME_PATH (Chromium/Chrome binary), FFMPEG (ffmpeg with libx264). setup.sh exports both.
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(path.join(process.cwd(), 'noop.js'));
let chromium;
try { ({ chromium } = require('playwright-core')); } catch { ({ chromium } = require('playwright')); }

const [mode, filmArg, ...rest] = process.argv.slice(2);
if (!mode || !filmArg) { console.error('usage: render.mjs stills|full <film.html> ...'); process.exit(2); }
const film = path.resolve(filmArg), root = path.dirname(film), page0 = path.basename(film);
const FF = process.env.FFMPEG || 'ffmpeg';
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.json': 'application/json' };
const srv = http.createServer((q, r) => {
  const f = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'content-type': types[path.extname(f).toLowerCase()] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(r);
});
await new Promise(r => srv.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${srv.address().port}/${page0}`;
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ['--font-render-hinting=none', '--force-color-profile=srgb', '--hide-scrollbars'] });

async function openPage() {
  const probe = await browser.newPage();
  await probe.goto(url);
  const size = await probe.evaluate(() => window.SIZE || [1920, 1080]);
  await probe.close();
  const page = await browser.newPage({ viewport: { width: size[0], height: size[1] }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(url);
  await page.evaluate(() => Promise.resolve(window.fontsReady || document.fonts.ready));
  if (errors.length) { console.error('page errors:\n' + errors.join('\n')); process.exit(1); }
  const dur = await page.evaluate(() => window.DUR);
  if (!dur || (await page.evaluate(() => typeof window.seek)) !== 'function') throw new Error('film must define window.DUR and window.seek');
  return { page, dur, errors };
}

try {
  if (mode === 'stills') {
    const times = rest[0].split(',').map(Number), out = path.resolve(rest[1] || 'stills');
    fs.mkdirSync(out, { recursive: true });
    const { page, errors } = await openPage();
    for (const t of times) {
      await page.evaluate(t => window.seek(t, Math.round(t * 60)), t);
      await page.screenshot({ path: path.join(out, `t${t.toFixed(2).padStart(6, '0')}.png`) });
    }
    if (errors.length) console.error('page errors:\n' + errors.join('\n'));
    console.log(`${times.length} stills -> ${out}`);
  } else if (mode === 'full') {
    const out = path.resolve(rest[0] || '.'), FPS = Number(rest[1] || 120), W = Number(rest[2] || 4);
    fs.mkdirSync(out, { recursive: true });
    const { page: p0, dur } = await openPage(); await p0.close();
    const N = Math.round(FPS * dur), per = Math.ceil(N / W);
    const t0 = Date.now();
    await Promise.all(Array.from({ length: W }, async (_, w) => {
      const { page, errors } = await openPage();
      const a = w * per, b = Math.min(N, a + per);
      const ff = spawn(FF, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '10', '-pix_fmt', 'yuv444p', path.join(out, `chunk${w}.mp4`)], { stdio: ['pipe', 'inherit', 'inherit'] });
      for (let i = a; i < b; i++) {
        await page.evaluate(([t, f]) => window.seek(t, f), [i / FPS, Math.floor(i * 60 / FPS)]);
        const buf = await page.screenshot({ type: 'jpeg', quality: 96 });
        if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
        if ((i - a) % 200 === 0) console.log(`worker ${w}: ${i - a}/${b - a}`);
      }
      ff.stdin.end();
      await new Promise(r => ff.on('close', r));
      if (errors.length) console.error(`worker ${w} page errors:\n` + errors.join('\n'));
    }));
    fs.writeFileSync(path.join(out, 'chunks.txt'), Array.from({ length: W }, (_, w) => `file 'chunk${w}.mp4'`).join('\n') + '\n');
    fs.writeFileSync(path.join(out, 'film.json'), JSON.stringify({ dur, fps: FPS, workers: W }));
    console.log(`rendered ${N} frames at ${FPS} fps in ${((Date.now() - t0) / 1000).toFixed(0)} s -> ${out}`);
  } else throw new Error('mode must be stills or full');
} finally { await browser.close(); srv.close(); }
