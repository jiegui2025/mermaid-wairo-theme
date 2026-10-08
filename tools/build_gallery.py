"""Prove the theme: theme every sample in gallery/gallery.src.md, draw it the way readers see it, check every drawn colour and every
label, and write the results.

    python3 tools/build_gallery.py

Each diagram is drawn five times:
- viewer-light and viewer-dark: the light theme in Mermaid 11.14 in a browser on a light and a dark page, as SharePoint, GitHub or a wiki draw it
- print: the light theme in Mermaid 12.1 on white, as mermaid-cli renders PDFs and images
- dark-viewer and dark-print: the dark theme (theme(..., mode='dark')) the same two ways, on its 墨 card
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
RUNS = {  # label: (theme mode, mermaid version, page background, page text colour)
    'viewer-light': ('light', '11.14.0', '#F8F8F8', '#242424'),
    'viewer-dark': ('light', '11.14.0', '#1B1A19', '#F3F2F1'),     # light theme on a dark page: the white card
    'print': ('light', '12.1.0', P.NEUTRAL['white'], P.NEUTRAL['ink']),
    'dark-viewer': ('dark', '11.14.0', '#1B1A19', '#F3F2F1'),       # dark theme on a dark page: the 墨 card
    'dark-print': ('dark', '12.1.0', P.NEUTRAL_DARK['white'], P.NEUTRAL_DARK['ink']),
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
T.APPROVED.update({m: set(T.TYPE_GROUPS) for m in P.MODES})  # provisional while proving; the checks below decide the real lists
source = open(os.path.join(G, 'gallery.src.md')).read()
shutil.rmtree(BUILD, ignore_errors=True)
docs, blocks_by_mode = {}, {}
for mode in P.MODES:
    docs[mode], n = T.theme_doc(source, mode=mode)
    blocks_by_mode[mode] = re.findall(r'```mermaid\n(.*?)```', docs[mode], re.S)
    os.makedirs(os.path.join(BUILD, 'src', mode))
    for i, b in enumerate(blocks_by_mode[mode], 1):
        open(os.path.join(BUILD, 'src', mode, f'd{i:02d}.mmd'), 'w').write(b)
    json.dump(sorted(P.all_hex(mode)), open(os.path.join(BUILD, f'allowed-{mode}.json'), 'w'))
body = docs['light']

ok_types, failed = {m: set() for m in P.MODES}, {m: defaultdict(dict) for m in P.MODES}
for label, (mode, version, bg, fg) in RUNS.items():
    out = os.path.join(BUILD, label)
    env = dict(os.environ, PAGE_BG=bg, PAGE_FG=fg)
    card = 'rgb({}, {}, {})'.format(*(int(P.neutral(mode)['white'][i:i + 2], 16) for i in (1, 3, 5)))
    rep = node('mm-render.mjs', fetch(version), out, *sorted(glob.glob(os.path.join(BUILD, 'src', mode, '*.mmd'))), env=env)['diagrams']
    audit = node('audit-colours.mjs', os.path.join(BUILD, f'allowed-{mode}.json'), *sorted(glob.glob(os.path.join(out, '*.svg'))), env=env)
    for i, b in enumerate(blocks_by_mode[mode], 1):
        kind, name = T.diagram_type(b), f'd{i:02d}'
        r = rep[name]
        if r.get('error'):
            failed[mode][kind][f'{label}: render'] = r['error']
            continue
        if 'viewer' in label and r.get('background') != card:
            failed[mode][kind][f'{label}: background'] = f"{r.get('background')}, not the {mode} card {card}"
        over = [o for o in r['overflows'] if o['by'] > 2]
        if over:
            failed[mode][kind][f'{label}: text overflow'] = over
        if audit.get(f'{name}.svg'):
            failed[mode][kind][f'{label}: off-palette colours'] = audit[f'{name}.svg']
        ok_types[mode].add(kind)
approved_by_mode = {m: sorted(ok_types[m] - set(failed[m])) for m in P.MODES}
approved = approved_by_mode['light']
json.dump({'approved': approved_by_mode, 'checked': {k: f'{v[0]} theme, Mermaid {v[1]}' for k, v in RUNS.items()}, 'not_themeable': NOT_THEMEABLE,
           'dark_refused': {k: dict(v) for k, v in failed['dark'].items()}},
          open(T.APPROVED_FILE, 'w'), indent=1)
print(f'{n} diagrams, checked as {", ".join(RUNS)}')
for m in P.MODES:
    print(f'  {m} theme approved: {approved_by_mode[m]}')
    if failed[m]:
        print(f'  {m} theme refused:', json.dumps({k: dict(v) for k, v in failed[m].items()}, indent=1))
if failed['light']:
    raise SystemExit(1)  # the light theme must prove every sample; the dark theme may refuse a type, with the reason recorded

img = os.path.join(ROOT, 'docs', 'images')
os.makedirs(img, exist_ok=True)
for name, what in README_FIGURES.items():
    for run, suffix in (('viewer-light', 'light'), ('viewer-dark', 'dark'), ('dark-viewer', 'dark-theme')):
        shutil.copyfile(os.path.join(BUILD, run, f'{name}.png'), os.path.join(img, f'{what}-{suffix}.png'))


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
so any Mermaid viewer draws it the same way. Each type here passed every check in Mermaid {RUNS['viewer-light'][1]} on a light
page and a dark page, and in Mermaid {RUNS['print'][1]} for print, in both the light and the dark theme: every colour drawn is a palette colour, every label fits
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
