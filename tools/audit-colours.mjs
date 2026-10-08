// node audit-colours.mjs allowed.json a.svg b.svg ... -> JSON {file: [{colour, prop, el, n}]} for every drawn colour not in the allowed list
import { readFileSync } from 'node:fs';
import puppeteer from 'puppeteer-core';
import { chromePath } from './chrome.mjs';
const [allowedFile, ...files] = process.argv.slice(2);
const allowed = new Set(JSON.parse(readFileSync(allowedFile, 'utf8')).map((h) => h.toUpperCase()));
const b = await puppeteer.launch({ executablePath: chromePath(), args: ['--no-sandbox'] });
const p = await b.newPage();
const out = {};
for (const f of files) {
  await p.setContent(`<!doctype html><body style="margin:0;background:${process.env.PAGE_BG || '#fff'};color:${process.env.PAGE_FG || '#000'}">${readFileSync(f, 'utf8')}</body>`);  // the page the diagram really sits on
  out[f.split('/').pop()] = await p.evaluate((allowedList) => {
    const allowed = new Set(allowedList);
    const hex = (c) => {
      const m = c.match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/);
      if (!m) return null;
      if (m[4] !== undefined && +m[4] === 0) return null;
      return '#' + [m[1], m[2], m[3]].map((x) => (+x).toString(16).padStart(2, '0')).join('').toUpperCase() + (m[4] !== undefined && +m[4] < 1 ? `@${m[4]}` : '');
    };
    const bad = {};
    const svg = document.querySelector('svg');
    const used = new Set(); // markers some drawn element points at
    for (const el of svg.querySelectorAll('*')) {
      const cs = getComputedStyle(el);
      for (const v of [cs.markerEnd, cs.markerStart, cs.markerMid, el.getAttribute('marker-end'), el.getAttribute('marker-start')]) {
        const m = (v || '').match(/#([^)"']+)/);
        if (m) used.add(m[1]);
      }
    }
    for (const el of svg.querySelectorAll('*')) {
      if (['defs', 'style', 'title', 'desc', 'marker', 'clipPath', 'mask'].includes(el.tagName)) continue;
      if (el.closest('defs') && !el.closest('marker')) continue;
      if (el.closest('marker') && !used.has(el.closest('marker').id)) continue;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) continue;
      const isText = ['text', 'tspan', 'span', 'div', 'p', 'foreignObject', 'textPath'].includes(el.tagName);
      const hasOwnText = isText && [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
      const shape = ['rect', 'path', 'circle', 'ellipse', 'polygon', 'line', 'polyline'].includes(el.tagName);
      if (!(r.width || r.height) && !el.closest('marker')) continue;
      const props = [];
      if (cs.filter && cs.filter !== 'none') { const k = `filter ${cs.filter.slice(0, 40)} <${el.tagName}>`; bad[k] = (bad[k] || 0) + 1; }
      if (shape) {
        if (cs.fill !== 'none' && +cs.fillOpacity > 0) props.push(['fill', cs.fill]);
        if (cs.stroke !== 'none' && +cs.strokeOpacity > 0 && parseFloat(cs.strokeWidth) > 0) props.push(['stroke', cs.stroke]);
      }
      if (hasOwnText) props.push([el.tagName === 'text' || el.tagName === 'tspan' ? 'fill' : 'color', el.tagName === 'text' || el.tagName === 'tspan' ? cs.fill : cs.color]);
      if (['div', 'span', 'p'].includes(el.tagName) && cs.backgroundColor && !/rgba\(0, 0, 0, 0\)/.test(cs.backgroundColor)) props.push(['background', cs.backgroundColor]);
      for (const [prop, c] of props) {
        const h = hex(c.startsWith('url') ? '' : c);
        if (!h) continue;
        const base = h.split('@')[0];
        if (allowed.has(base)) continue;
        const key = `${h} ${prop} <${el.tagName} class="${(el.getAttribute('class') || '').slice(0, 40)}">`;
        bad[key] = (bad[key] || 0) + 1;
      }
    }
    return bad;
  }, [...allowed]);
}
await b.close();
console.log(JSON.stringify(out, null, 1));
