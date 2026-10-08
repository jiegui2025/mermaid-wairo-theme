"""Prove the theme: theme every sample in gallery/gallery.src.md, draw it the way readers see it, check every drawn colour and every
label, and write the results.

    python3 tools/build_gallery.py

Each diagram is drawn three times:
- viewer-light and viewer-dark: Mermaid 11.14 in a browser on a light and a dark page, as SharePoint, GitHub or a wiki draw it
- print: Mermaid 12.1 on white, as mermaid-cli renders PDFs and images
A diagram type is approved only if, in all three, every colour drawn is a palette colour, every label fits inside its box, it
renders without error, and (in viewers) it sits on its own white card.

Writes wairo/approved.json (the types check() accepts), gallery/preview.md (the themed gallery) and docs/images/*.png.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from fetch_mermaid import fetch  # noqa: E402
from wairo import mermaid_theme as T  # noqa: E402
from wairo import palette as P  # noqa: E402

G = os.path.join(ROOT, 'gallery')
BUILD = os.path.join(ROOT, 'build', 'gallery')
TOOLS = os.path.join(ROOT, 'tools')
RUNS = {  # label: (mermaid version, page background, page text colour)
    'viewer-light': ('11.14.0', '#F8F8F8', '#242424'),
    'viewer-dark': ('11.14.0', '#1B1A19', '#F3F2F1'),
    'print': ('12.1.0', P.NEUTRAL['white'], P.NEUTRAL['ink']),
}
NOT_THEMEABLE = {
    'journey': "faces, task borders and section borders are hard-coded greys (#666, #999, #333) in Mermaid's CSS",
    'timeline': "event boxes are drawn 20% brighter than their section colour by Mermaid's CSS, which shifts every hue; use a gantt with milestones",
}
README_FIGURES = {'d01': 'flowchart', 'd04': 'gantt', 'd05': 'pie', 'd08': 'mindmap'}


def node(script, *args, env):
    r = subprocess.run(['node', os.path.join(TOOLS, script), *args], capture_output=True, text=True, env=env)
    if r.returncode:
        raise SystemExit(f'{script} failed:\n{r.stderr[-2000:]}')
    return json.loads(r.stdout)


P.check()
T.APPROVED.update(T.TYPE_GROUPS)  # provisional while proving; the checks below decide the real list
body, n = T.theme_doc(open(os.path.join(G, 'gallery.src.md')).read())
blocks = re.findall(r'```mermaid\n(.*?)```', body, re.S)
src_dir = os.path.join(BUILD, 'src')
shutil.rmtree(BUILD, ignore_errors=True)
os.makedirs(src_dir)
for i, b in enumerate(blocks, 1):
    open(os.path.join(src_dir, f'd{i:02d}.mmd'), 'w').write(b)
allowed = os.path.join(BUILD, 'allowed.json')
json.dump(sorted(P.all_hex()), open(allowed, 'w'))

ok_types, failed = {}, defaultdict(dict)
for label, (version, bg, fg) in RUNS.items():
    out = os.path.join(BUILD, label)
    env = dict(os.environ, PAGE_BG=bg, PAGE_FG=fg)
    rep = node('mm-render.mjs', fetch(version), out, *sorted(glob.glob(os.path.join(src_dir, '*.mmd'))), env=env)['diagrams']
    audit = node('audit-colours.mjs', allowed, *sorted(glob.glob(os.path.join(out, '*.svg'))), env=env)
    for i, b in enumerate(blocks, 1):
        kind, name = T.diagram_type(b), f'd{i:02d}'
        r = rep[name]
        if r.get('error'):
            failed[kind][f'{label}: render'] = r['error']
            continue
        if label.startswith('viewer') and r.get('background') != 'rgb(255, 255, 255)':
            failed[kind][f'{label}: background'] = f"{r.get('background')}, not the white card"
        over = [o for o in r['overflows'] if o['by'] > 2]
        if over:
            failed[kind][f'{label}: text overflow'] = over
        if audit.get(f'{name}.svg'):
            failed[kind][f'{label}: off-palette colours'] = audit[f'{name}.svg']
        ok_types.setdefault(kind, name)
approved = sorted(set(ok_types) - set(failed))
json.dump({'approved': approved, 'mermaid': {k: v[0] for k, v in RUNS.items()}, 'not_themeable': NOT_THEMEABLE},
          open(T.APPROVED_FILE, 'w'), indent=1)
print(f'{n} diagrams, checked as {", ".join(RUNS)}: approved {approved}')
print('failed:', json.dumps(dict(failed), indent=1) if failed else 'none')
if failed:
    raise SystemExit(1)

img = os.path.join(ROOT, 'docs', 'images')
os.makedirs(img, exist_ok=True)
for name, what in README_FIGURES.items():
    for mode in ('light', 'dark'):
        shutil.copyfile(os.path.join(BUILD, f'viewer-{mode}', f'{name}.png'), os.path.join(img, f'{what}-{mode}.png'))


# ---------------------------------------------------------------- the gallery page
def uses(k):
    return ', '.join([f'class `{r}`' for r, v in P.ROLE.items() if v == k] + [f'"{s}"' for s, v in P.SECTION.items() if v == k]) or 'chart series'


TY = P.TYPE
colours = '\n'.join(f'| {c.kanji} {c.romaji} | {P.ENGLISH[k]} | `{c.ink}` | `{c.soft}` | `{c.tint}` | {uses(k)} |' for k, c in P.COLOURS.items())
neutral = '\n'.join(f'| {k} | `{v}` |' for k, v in P.NEUTRAL.items())
refused = '\n'.join(f'- **{k}**: {why}.' for k, why in NOT_THEMEABLE.items())
others = sorted(set(T.TYPE_GROUPS) - set(approved) - set(NOT_THEMEABLE) - {'graph', 'stateDiagram', 'xychart', 'treemap', 'block', 'packet'})
diagrams = re.sub(r'^# .*\n\n.*\n', '', body, count=1).strip()
page = f"""# Wairo theme gallery

Generated by `tools/build_gallery.py` from `gallery/gallery.src.md`. Every diagram below carries the theme in its own source,
so any Mermaid viewer draws it the same way. Each type here passed every check in Mermaid {RUNS['viewer-light'][0]} on a light
page and a dark page, and in Mermaid {RUNS['print'][0]} for print: every colour drawn is a palette colour, every label fits
inside its box, and the diagram sits on its own white card.

## Palette

| Colour | In words | Ink (lines, titles) | Soft (chart areas) | Tint (box fills) | Used for |
|---|---|---|---|---|---|
{colours}

| Neutral | Value |
|---|---|
{neutral}

Type: Noto Sans JP and Noto Sans Mono, falling back to fonts every machine already has (Segoe UI, Yu Gothic UI and Consolas
on Windows; Hiragino Sans and Menlo on macOS). Diagrams use {TY['diagram']['body']}px body text, {TY['diagram']['legend']}px
legends and {TY['diagram']['title']}px titles.

## Diagram types

{diagrams}

## Types the check refuses

These types can't follow the palette, because Mermaid hard-codes colours that no theme setting reaches:

{refused}

Not yet proven, so refused until a sample is added here and passes: {', '.join(f'`{t}`' for t in others)}.
"""
open(os.path.join(G, 'preview.md'), 'w').write(page)
print('wrote gallery/preview.md, wairo/approved.json and docs/images/')
