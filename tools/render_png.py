"""Render themed Mermaid diagrams to PNG for places that can't draw Mermaid or SVG (Jira, slides, chat).

    python3 tools/render_png.py <in.mmd> <out.png> [--scale 3]

Uses Mermaid 12.1 (the print renderer) on the diagram's own card. For types whose legend is a one-line caption, the caption
is drawn under the diagram, so the PNG carries its legend. The default 3x scale stays sharp on high-density screens and when zoomed.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from fetch_mermaid import fetch  # noqa: E402
from wairo import mermaid_theme as T  # noqa: E402
from wairo import palette as P  # noqa: E402


def render(src_path, out_path, scale=3):
    src = open(src_path).read()
    T.check(src)
    mode = T._mode_of(src)
    N = P.neutral(mode)
    env = dict(os.environ, PAGE_BG=N['white'], CAPTION_FG=N['muted'], FONT=P.font_stack(P.FONT_SANS, quoted=False))  # unquoted: it goes inside an HTML attribute
    cap = T.caption(src) or ''
    subprocess.run(['node', os.path.join(ROOT, 'tools', 'render-png.mjs'), fetch('12.1.0'), src_path, out_path, str(scale), cap],
                   check=True, env=env)
    return out_path


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    scale = float(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 3
    if len(args) < 2:
        raise SystemExit(__doc__)
    print(render(args[0], args[1], scale))
