// Find a headless Chrome: $CHROME_PATH, else the newest chrome-headless-shell that Puppeteer installed.
import { existsSync, readdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

export function chromePath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const base = join(homedir(), '.cache', 'puppeteer', 'chrome-headless-shell');
  const found = existsSync(base)
    ? readdirSync(base).sort().flatMap((v) => readdirSync(join(base, v)).map((d) => join(base, v, d, 'chrome-headless-shell')))
    : [];
  const hit = found.filter(existsSync).pop();
  if (!hit) throw new Error('No headless Chrome: run `npx @puppeteer/browsers install chrome-headless-shell@stable`, or set CHROME_PATH');
  return hit;
}
