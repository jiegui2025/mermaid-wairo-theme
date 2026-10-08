"""Markdown document with Mermaid -> PDF with every diagram drawn as vectors, styled from the palette.

    python3 tools/build_doc_pdf.py <doc.md> <out.pdf> [--compact]

--compact sets tighter type and margins, for one-page handouts.

Diagrams are rendered by mermaid-cli (Mermaid 12) and inlined as SVG. Chrome prints an <img> SVG that holds HTML labels as a
low-resolution bitmap, so inlining keeps lines and text sharp at any zoom. Needs Node (npx) and a headless Chrome (tools/chrome.py).
"""
import html
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from chrome import chrome_path  # noqa: E402
from wairo import palette as P  # noqa: E402  the one source of colour and type

MMDC = '@mermaid-js/mermaid-cli@12.0.0'
MARKED = 'marked@15.0.12'
N, C = P.NEUTRAL, P.COLOURS
SANS, MONO = P.font_stack(P.FONT_SANS), P.font_stack(P.FONT_MONO)


def build(src, out_pdf, compact=False):
    T = dict(P.TYPE['print'])
    if compact:
        T.update({'body': 8.6, 'leading': 1.48, 'h1': 16, 'h2': 11.5, 'table': 8, 'small': 7.5})
    margin = '11mm 13mm 12mm' if compact else '16mm 15mm 17mm'
    gap = 12 if compact else 22
    md = open(src).read()
    work = tempfile.mkdtemp(prefix='wairo-pdf-')
    blocks = list(re.finditer(r'```mermaid\n(.*?)```', md, re.S))
    parts, last = [], 0
    for i, m in enumerate(blocks, 1):
        mmd, svg_path = os.path.join(work, f'fig{i}.mmd'), os.path.join(work, f'fig{i}.svg')
        open(mmd, 'w').write(m.group(1))
        r = subprocess.run(['npx', '-y', MMDC, '-q', '-i', mmd, '-o', svg_path, '-b', N['white']], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f'diagram {i} failed to render:\n{r.stderr[-1500:]}')
        # mermaid-cli names every diagram 'my-svg' (its CSS and marker ids hang off that), so give each its own id first
        svg = re.sub(r'^<\?xml[^>]*>\s*', '', open(svg_path).read().replace('my-svg', f'fig{i}'))
        parts += [md[last:m.start()], f'\n<figure class="diagram" role="img" aria-label="Diagram {i}">{svg}</figure>\n']
        last = m.end()
    parts.append(md[last:])
    tmp_md, body_html = os.path.join(work, 'doc.md'), os.path.join(work, 'body.html')
    open(tmp_md, 'w').write(''.join(parts).replace('<details>', '<details open>'))
    subprocess.run(['npx', '-y', MARKED, '--gfm', '-i', tmp_md, '-o', body_html], check=True)
    m = re.search(r'^# (.+)$', md, re.M)
    title = m.group(1) if m else os.path.basename(src)
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>
@page {{ size: A4; margin: {margin};
  @bottom-right {{ content: counter(page) " / " counter(pages); font: {T['small']}pt {SANS}; color: {N['muted']}; }}
  @bottom-left {{ content: "{html.escape(title)}"; font: {T['small']}pt {SANS}; color: {N['muted']}; }} }}
body {{ font-family: {SANS}; font-size: {T['body']}pt; line-height: {T['leading']}; color: {N['ink']}; font-variant-numeric: tabular-nums; }}
h1 {{ font-size: {T['h1']}pt; font-weight: 600; line-height: 1.3; margin: 0 0 10pt; padding-bottom: 6pt; border-bottom: 2px solid {C['ai'].ink}; }}
h2 {{ font-size: {T['h2']}pt; font-weight: 600; color: {C['ai'].ink}; margin: {gap}pt 0 6pt; padding-bottom: 3pt; border-bottom: 1px solid {N['line']}; break-after: avoid; }}
h3 {{ font-size: {T['h3']}pt; font-weight: 600; color: {C['kon'].ink}; margin: 15pt 0 4pt; break-after: avoid; }}
h4 {{ font-size: {T['h4']}pt; font-weight: 600; margin: 12pt 0 4pt; break-after: avoid; }}
p, li {{ margin: 0 0 5pt; }}
strong {{ font-weight: 600; }}
table {{ border-collapse: collapse; width: 100%; margin: 6pt 0 12pt; font-size: {T['table']}pt; line-height: 1.45; }}
th, td {{ border: 1px solid {N['line']}; padding: 3.5pt 6pt; vertical-align: top; text-align: left; }}
th {{ background: {N['paper']}; font-weight: 600; border-bottom: 1.5px solid {N['border']}; }}
tr {{ break-inside: avoid; }}
code {{ font-family: {MONO}; font-size: {T['code']}pt; background: {N['paper']}; border: 1px solid {N['rule']}; padding: 0 2.5pt; border-radius: 2pt; }}
pre {{ background: {N['paper']}; border: 1px solid {N['line']}; border-left: 3px solid {C['ai'].ink}; padding: 7pt 9pt; white-space: pre-wrap; word-break: break-word; break-inside: avoid; }}
pre code {{ background: none; border: 0; padding: 0; }}
figure.diagram {{ margin: 10pt 0 4pt; text-align: center; break-inside: avoid; }}
figure.diagram svg {{ max-width: 100%; max-height: 240mm; height: auto; }}
p.legend {{ font-size: {T['small']}pt; color: {N['muted']}; text-align: center; margin: 0 0 14pt; }}
hr {{ border: 0; border-top: 1px solid {N['line']}; margin: 16pt 0; }}
a {{ color: {C['ai'].ink}; text-decoration: underline; text-decoration-color: {N['line']}; text-underline-offset: 2px; }}
blockquote {{ margin: 6pt 0; padding: 3pt 10pt; border-left: 3px solid {C['hanada'].ink}; background: {C['hanada'].tint}; color: {N['ink']}; }}
</style></head><body>
{open(body_html).read()}
</body></html>'''
    page = re.sub(r'<p><em>(Legend: .*?)</em></p>', r'<p class="legend">\1</p>', page)  # captions written by theme_doc()
    page_html = os.path.join(work, 'page.html')
    open(page_html, 'w').write(page)
    subprocess.run([chrome_path(), '--headless', '--disable-gpu', '--no-sandbox', '--no-pdf-header-footer',
                    f'--print-to-pdf={os.path.abspath(out_pdf)}', 'file://' + page_html], check=True, capture_output=True)
    pdf = open(out_pdf, 'rb').read()
    pages = len(re.findall(rb'/Type\s*/Page[^s]', pdf))
    print(f'{out_pdf}: {len(blocks)} diagrams, {pages} pages, {len(pdf) // 1024} KB')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2:
        raise SystemExit(__doc__)
    build(args[0], args[1], compact='--compact' in sys.argv)
