// Render one themed Mermaid diagram to a PNG: node render-png.mjs <mermaid.min.js> <in.mmd> <out.png> <scale> [caption]
// Draws on the diagram's own card with the one-line legend underneath when there is one, so the legend travels with the image.
import { readFileSync } from 'node:fs';
import puppeteer from 'puppeteer-core';
import { chromePath } from './chrome.mjs';

const [lib, input, out, scale = '3', caption = ''] = process.argv.slice(2);
const { PAGE_BG = '#FFFFFF', CAPTION_FG = '#4E5D63', FONT = 'sans-serif' } = process.env;
const b = await puppeteer.launch({ executablePath: chromePath(), args: ['--no-sandbox'] });
const p = await b.newPage();
await p.setViewport({ width: 1600, height: 1000, deviceScaleFactor: Number(scale) });
await p.setContent(`<!doctype html><meta charset="utf-8"><body style="margin:0;background:${PAGE_BG}">
  <figure id="fig" style="display:inline-block;margin:0;padding:12px 12px ${caption ? 8 : 12}px;background:${PAGE_BG}">
    <div id="d"></div>
    <figcaption id="c" style="font:12px/1.5 ${FONT};color:${CAPTION_FG};text-align:center;margin-top:6px"></figcaption>
  </figure></body>`);
await p.addScriptTag({ content: readFileSync(lib, 'utf8') });
const err = await p.evaluate(async (src, cap) => {
  window.mermaid.initialize({ startOnLoad: false });
  try {
    const { svg } = await window.mermaid.render('fig1', src);
    document.getElementById('d').innerHTML = svg;
  } catch (e) { return String(e.message || e); }
  const s = document.querySelector('#d svg');
  if (s.style.maxWidth) { s.style.width = s.style.maxWidth; s.removeAttribute('height'); }
  const c = document.getElementById('c');
  if (cap) { c.textContent = cap; c.style.maxWidth = `${Math.max(360, s.getBoundingClientRect().width)}px`; } else c.remove();
  await document.fonts.ready;
  return null;
}, readFileSync(input, 'utf8'), caption);
if (err) { console.error(err); process.exit(1); }
await (await p.$('#fig')).screenshot({ path: out });
await b.close();
