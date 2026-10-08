// Render Mermaid diagrams with a given mermaid.min.js the way a browser viewer (SharePoint, GitHub, a wiki) does, screenshot each, and report text that
// overflows its box. node mm-render.mjs <mermaid.min.js> <out-dir> <a.mmd> [b.mmd ...]  -> <out-dir>/<name>.png + JSON report on stdout
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { basename } from 'node:path';
import puppeteer from 'puppeteer-core';
import { chromePath } from './chrome.mjs';

const [lib, outDir, ...files] = process.argv.slice(2);
mkdirSync(outDir, { recursive: true });
const b = await puppeteer.launch({ executablePath: chromePath(), args: ['--no-sandbox'] });
const p = await b.newPage();
await p.setViewport({ width: 1400, height: 900, deviceScaleFactor: 2 });
const PAGE_BG = process.env.PAGE_BG || '#F8F8F8', PAGE_FG = process.env.PAGE_FG || '#242424';  // PAGE_BG=#1B1A19 PAGE_FG=#F3F2F1 is a dark page
await p.setContent(`<!doctype html><meta charset="utf-8"><body style="margin:0;background:${PAGE_BG};color:${PAGE_FG}"><div id="out" style="display:inline-block;padding:16px;background:${PAGE_BG}"></div></body>`);
await p.addScriptTag({ content: readFileSync(lib, 'utf8') });
const version = await p.evaluate(() => { window.mermaid.initialize({ startOnLoad: false }); return window.mermaid.version?.() ?? '?'; }).catch(() => '?');
const report = { version, diagrams: {} };
for (const f of files) {
  const name = basename(f).replace(/\.mmd$/, '');
  const res = await p.evaluate(async (src, id) => {
    const out = document.getElementById('out');
    out.innerHTML = '';
    try {
      const { svg } = await window.mermaid.render(id, src);
      out.innerHTML = svg;
      const s = out.querySelector('svg');
      if (s.style.maxWidth) { s.style.width = s.style.maxWidth; s.removeAttribute('height'); }
    } catch (e) { return { error: String(e.message || e).slice(0, 300) }; }
    await document.fonts.ready;
    const svg = out.querySelector('svg');
    const overflows = [];
    const texts = [...svg.querySelectorAll('foreignObject span, foreignObject div, text')].filter((t) =>
      [...t.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()) || (t.tagName === 'text' && t.textContent.trim()));
    for (const t of texts) {
      const tr = t.getBoundingClientRect();
      if (!tr.width) continue;
      const cx = tr.x + tr.width / 2, cy = tr.y + tr.height / 2;
      let shape = null;
      for (let g = t.parentElement, i = 0; g && i < 5 && !shape; g = g.parentElement, i++) {
        for (const s of g.children) {
          if (!['rect', 'polygon', 'circle', 'ellipse', 'path'].includes(s.tagName)) continue;
          const cls = s.getAttribute('class') || '';
          if (s.tagName === 'path' && !/label-container|basic|outer-path/.test(cls)) continue;
          const r = s.getBoundingClientRect();
          if (r.width < 8 || r.height < 8) continue;
          if (cx >= r.x && cx <= r.x + r.width && cy >= r.y && cy <= r.y + r.height) { shape = r; break; }
        }
      }
      if (!shape) continue;
      const over = Math.max(shape.x - tr.x, tr.x + tr.width - (shape.x + shape.width), shape.y - tr.y, tr.y + tr.height - (shape.y + shape.height));
      if (over > 1) overflows.push({ text: t.textContent.trim().slice(0, 40), by: Math.round(over) });
    }
    const r = svg.getBoundingClientRect();
    return { width: Math.round(r.width), height: Math.round(r.height), overflows, background: getComputedStyle(svg).backgroundColor };
  }, readFileSync(f, 'utf8'), `d${Math.random().toString(36).slice(2, 8)}`);
  if (!res.error) {
    const el = await p.$('#out');
    await el.screenshot({ path: `${outDir}/${name}.png` });
    writeFileSync(`${outDir}/${name}.svg`, await p.$eval('#out svg', (s) => s.outerHTML));
  }
  report.diagrams[name] = res;
}
await b.close();
console.log(JSON.stringify(report, null, 1));
