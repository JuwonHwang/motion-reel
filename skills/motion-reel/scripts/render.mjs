#!/usr/bin/env node
// HTML 장면 파일을 프레임 단위로 캡처해 MP4로 인코딩한다.
// 장면 파일은 window.__reel = { W, H, DURATION, FPS, ready, renderFrame(t), cues, music } 를 노출해야 한다.
//
// 사용:
//   node render.mjs --html reel/index.html --out reel/reel.mp4 [--audio reel/audio.wav]
//                   [--blur 2] [--crf 16] [--fast] [--workers 4] [--lufs -16]
//   node render.mjs --html reel/index.html --stills 0.5,2,4.25 --outdir reel/stills
//   node render.mjs --html reel/index.html --dump-cues reel/cues.json
//
// --blur N : 한 출력 프레임당 N개의 하위 프레임을 렌더링해 평균한다(모션 블러). 렌더 시간은 N배가 된다.
// --fast   : PNG 대신 JPEG(q=95)로 캡처하고 x264 veryfast 로 인코딩한다. 미리보기 렌더에 쓴다.
// --format png|jpeg : 프레임 캡처 형식. png 는 무손실, jpeg(q95)는 약 1.4배 빠르다(측정 55초 → 39초).
// --workers N : 병렬 캡처 브라우저 수(기본 min(4, CPU 코어 - 2)).
// --preset P  : x264 프리셋(기본 medium).
// --lufs N : 오디오 평균 소리 크기 목표(기본 -16). 방송용은 -23. --tp N: True Peak 상한(기본 -1.5 dBTP).
// 인코딩: H.264 High, yuv420p, BT.709 표기, AAC 384 kbps 48kHz (YouTube 권장 업로드 설정, references/conventions.md 6절)

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

let chromium;
try {
  ({ chromium } = await import('playwright-core'));
} catch {
  const dir = path.dirname(new URL(import.meta.url).pathname);
  console.error(`playwright-core가 없다. 다음을 실행한다:\n  npm install --prefix "${dir}"`);
  process.exit(2);
}

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => {
    if (a.startsWith('--')) {
      const next = arr[i + 1];
      acc.push([a.slice(2), next && !next.startsWith('--') ? next : true]);
    }
    return acc;
  }, [])
);

if (!args.html) {
  console.error('--html 경로가 필요하다.');
  process.exit(1);
}

async function launch() {
  const opts = { headless: true, args: ['--force-color-profile=srgb', '--hide-scrollbars', '--enable-webgl', '--ignore-gpu-blocklist'] };
  const tries = [];
  if (process.env.CHROME_PATH) tries.push({ ...opts, executablePath: process.env.CHROME_PATH });
  tries.push({ ...opts, channel: 'chrome' }, opts, { ...opts, channel: 'msedge' });
  let lastErr;
  for (const t of tries) {
    try { return await chromium.launch(t); } catch (e) { lastErr = e; }
  }
  console.error('Chromium 계열 브라우저를 실행하지 못했다. CHROME_PATH 환경 변수로 실행 파일을 지정하거나 `npx playwright-core install chromium`을 실행한다.');
  throw lastErr;
}

const browser = await launch();
const htmlUrl = pathToFileURL(path.resolve(args.html)).href;
const consoleErrors = [];

// 탭 하나를 연다. 탭마다 별도 컨텍스트를 써서 렌더러 프로세스를 나눈다(병렬 렌더용).
// 작업자마다 브라우저 프로세스를 따로 띄운다. 한 브라우저 안의 탭 여러 개는 캡처가 직렬화되어 빨라지지 않았다(측정: 탭 1개 119초, 4개 98초).
async function openPage(size = { width: 1920, height: 1080 }, own = false) {
  const br = own ? await launch() : browser;
  const ctx = await br.newContext({ viewport: size, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => consoleErrors.push(String(e)));
  await page.goto(`${htmlUrl}?render=1`, { waitUntil: 'networkidle', timeout: 120000 });
  await page.waitForFunction(() => window.__reel && typeof window.__reel.renderFrame === 'function', null, { timeout: 30000 });
  await page.evaluate(async () => { await window.__reel.ready; await document.fonts.ready; });
  const cdp = await ctx.newCDPSession(page);
  return { page, cdp, br };
}

const first = await openPage();
const meta = await first.page.evaluate(() => ({
  W: window.__reel.W, H: window.__reel.H, DURATION: window.__reel.DURATION, FPS: window.__reel.FPS,
  cues: window.__reel.cues || [], music: window.__reel.music || null,
}));
await first.page.setViewportSize({ width: meta.W, height: meta.H });

if (consoleErrors.length) {
  console.error('페이지 오류:\n' + consoleErrors.join('\n'));
}

// 캡처는 CDP Page.captureScreenshot 을 직접 쓴다. optimizeForSpeed 는 PNG 압축 수준을 낮춰 빠르게 하며 무손실이다.
// 측정(informative-slides 예시, 1080p): Playwright PNG 318ms, CDP PNG(optimizeForSpeed) 67ms, JPEG q95 33ms /프레임.
async function frameAt(w, t, type = 'png') {
  await w.page.evaluate((tt) => window.__reel.renderFrame(tt), t);
  const r = await w.cdp.send('Page.captureScreenshot', {
    format: type, ...(type === 'jpeg' ? { quality: 95 } : {}), optimizeForSpeed: true,
    clip: { x: 0, y: 0, width: meta.W, height: meta.H, scale: 1 },
  });
  return Buffer.from(r.data, 'base64');
}

// --- 큐 내보내기 ---
if (args['dump-cues']) {
  const out = { duration: meta.DURATION, music: meta.music, cues: meta.cues };
  fs.writeFileSync(args['dump-cues'], JSON.stringify(out, null, 2));
  console.log(`큐 ${meta.cues.length}개를 ${args['dump-cues']}에 썼다.`);
  await browser.close();
  process.exit(0);
}

// --- 정지 프레임 ---
if (args.stills) {
  const outdir = args.outdir || path.join(path.dirname(args.html), 'stills');
  fs.mkdirSync(outdir, { recursive: true });
  const times = String(args.stills).split(',').map(Number);
  for (const t of times) {
    const buf = await frameAt(first, t);
    const f = path.join(outdir, `t${t.toFixed(2).padStart(5, '0')}.png`);
    fs.writeFileSync(f, buf);
    console.log(f);
  }
  await browser.close();
  if (consoleErrors.length) process.exit(3);
  process.exit(0);
}

// --- 영상 ---
const fps = Number(args.fps || meta.FPS || 60);
const blur = Math.max(1, Number(args.blur || 1));
const crf = String(args.crf || 16);
const out = args.out || path.join(path.dirname(args.html), 'reel.mp4');
const type = args.format || (args.fast ? 'jpeg' : 'png');
const subRate = fps * blur;
const total = Math.round(meta.DURATION * subRate);

const vf = [];
if (blur > 1) {
  // tmix는 직전 N개 프레임을 평균한다. N번째마다 하나를 고르면 셔터 각도 360도의 모션 블러가 된다.
  vf.push(`tmix=frames=${blur}`, `select='eq(mod(n\\,${blur})\\,${blur - 1})'`, `setpts=N/(${fps}*TB)`);
}
vf.push('format=yuv420p');

const ff = [
  '-y', '-hide_banner', '-loglevel', 'error',
  '-f', 'image2pipe', '-framerate', String(subRate), '-i', '-',
];
if (args.audio) ff.push('-i', args.audio);
ff.push('-vf', vf.join(','), '-r', String(fps), '-c:v', 'libx264', '-preset', args.fast ? 'veryfast' : (args.preset || 'medium'), '-crf', crf,
  '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
  '-movflags', '+faststart');
const lufs = Number(args.lufs ?? -16), tp = Number(args.tp ?? -1.5);
if (args.audio) ff.push('-map', '0:v', '-map', '1:a', '-af', `loudnorm=I=${lufs}:TP=${tp}:LRA=11,aresample=48000`,
  '-c:a', 'aac', '-b:a', '384k', '-ar', '48000', '-shortest');
ff.push(out);

const enc = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });
const encDone = new Promise((res, rej) => enc.on('close', (c) => (c === 0 ? res() : rej(new Error(`ffmpeg 종료 코드 ${c}`)))));

// 병렬 캡처: 작업자 W개가 프레임을 번갈아 맡고(i % W), 기록기는 번호 순서대로 ffmpeg 에 넘긴다.
const cores = (await import('node:os')).cpus().length;
// 측정(Apple Silicon 10코어 중 고성능 4코어, informative-slides 15초, PNG): 브라우저 1개 119초, 4개 55초, 6개 57초, 8개 59초
const nWorkers = Math.max(1, Number(args.workers || Math.min(4, Math.max(1, cores - 2))));
const workers = [first];
for (let k = 1; k < nWorkers; k++) {
  workers.push(openPage({ width: meta.W, height: meta.H }, true));
}
for (let k = 1; k < workers.length; k++) workers[k] = await workers[k];
const t0 = Date.now();
const ready = new Map();
let nextToWrite = 0, wake = null;
const writer = (async () => {
  while (nextToWrite < total) {
    if (!ready.has(nextToWrite)) { await new Promise((r) => (wake = r)); continue; }
    const buf = ready.get(nextToWrite); ready.delete(nextToWrite);
    if (!enc.stdin.write(buf)) await new Promise((r) => enc.stdin.once('drain', r));
    if (nextToWrite % subRate === 0) {
      const el = (Date.now() - t0) / 1000;
      console.log(`${nextToWrite}/${total} 프레임, ${el.toFixed(0)}초 경과, 남은 예상 ${((el / Math.max(nextToWrite, 1)) * (total - nextToWrite)).toFixed(0)}초`);
    }
    nextToWrite++;
  }
})();
await Promise.all(workers.map(async (w, k) => {
  for (let i = k; i < total; i += nWorkers) {
    // 기록이 너무 뒤처지면 메모리를 아끼려고 기다린다
    while (i - nextToWrite > nWorkers * 8) await new Promise((r) => setTimeout(r, 5));
    ready.set(i, await frameAt(w, i / subRate, type));
    if (wake) { const f = wake; wake = null; f(); }
  }
}));
if (wake) { const f = wake; wake = null; f(); }
await writer;
for (const w of workers.slice(1)) await w.br.close();
enc.stdin.end();
await encDone;
await browser.close();
console.log(`${out} (${total}개 하위 프레임, ${fps}fps, 블러 ${blur}, 작업자 ${nWorkers}개, ${((Date.now() - t0) / 1000).toFixed(0)}초)`);
if (consoleErrors.length) {
  console.error(`페이지 오류 ${consoleErrors.length}건이 있었다. 위 로그를 확인한다.`);
  process.exit(3);
}
