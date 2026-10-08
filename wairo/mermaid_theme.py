"""Wairo Mermaid theme: one theme for every diagram type, every colour from palette.py, a legend on every figure.

    theme(src, classmap=None, edges=None) -> source with the theme, standard classDefs, edge styles and the legend; content unchanged
    caption(src)                          -> the text legend for types that cannot draw one inside the diagram, or None
    check(src)                            -> raises unless the themed source follows the rules
    theme_doc(md, plans=None)             -> a Markdown document with every Mermaid block themed and captioned

The legend lives in the diagram source, so any Mermaid viewer (SharePoint, GitHub, Azure DevOps, VS Code) draws it:
- flowchart: a small key box (11px, one swatch per entry) in the bottom corner, hung from the last of the deepest nodes.
- pie: the chart's own legend.
- everything else (gantt, sequence, quadrant, xychart, mindmap, state, class, ER, git): a one-line caption under the diagram.
Automatic entries can be renamed, and entries added, with `%% legend: <style> = <words>`, where style is a class, an edge
kind, series-N, gantt-STATE, or text (a plain entry with no swatch).
"""
import json
import os
import re
from collections import defaultdict

from . import palette as P

FONT = P.font_stack(P.FONT_SANS, quoted=False)  # unquoted: Mermaid's init parser breaks on any quote
TY = P.TYPE['diagram']
MODE = None  # the mode the colour tables below are built for; every public function sets it


class _Steps:
    """One palette colour's ink, soft and tint in a given mode."""
    def __init__(self, colour, mode):
        self.ink, self.soft, self.tint = (colour.step(s, mode) for s in ('ink', 'soft', 'tint'))


def classdef(c):
    s = f"fill:{c['fill']},stroke:{c['stroke']},stroke-width:1.2px,color:{c['color']}"
    return s + (f",stroke-dasharray:{c['dash']}" if c['dash'] else '')

def linkstyle(e):
    s = f"stroke:{e['stroke']},stroke-width:{e['width']}px,color:{e['color']}"
    return s + (f",stroke-dasharray:{e['dash']}" if e['dash'] else '')

def _series(prefix, values, n, start=0):
    return {f'{prefix}{i + start}': values[i % len(values)] for i in range(n)}


def _build(mode):
    """Build every colour table for 'light' or 'dark'. Everything else in this module reads them at call time."""
    global MODE, BORDER, C, CARD_CSS, CLASSES, EDGE, EDGES, GANTT, INK, LEGEND_BOX, LEGEND_POINT, LINE, MUTED, N, PAPER, RULE, SERIES_INK, SERIES_SOFT, VARS, WHITE
    MODE = mode
    N, C = P.neutral(mode), {k: _Steps(c, mode) for k, c in P.COLOURS.items()}
    INK, MUTED, EDGE, BORDER, LINE, RULE, PAPER, WHITE = (N[k] for k in ('ink', 'muted', 'edge', 'border', 'line', 'rule', 'paper', 'white'))

    SERIES_INK = [C[s].ink for s in P.SERIES]
    SERIES_SOFT = [C[s].soft for s in P.SERIES]


    def _role(name, dash=None):
        return {'fill': P.role(name, 'tint', mode), 'stroke': P.role(name, 'ink', mode), 'dash': dash, 'color': INK}


    # One class set, identical in every diagram. Structure stays neutral; colour is for meaning.
    CLASSES = {
        'plain': {'fill': WHITE, 'stroke': BORDER, 'dash': None, 'color': INK},      # default thing ('node' and 'default' are Mermaid's own names)
        'ours': _role('ours'),                                                       # our own system, the subject
        'gen': {'fill': PAPER, 'stroke': BORDER, 'dash': None, 'color': INK},        # generated output, artefacts
        'ext': {'fill': WHITE, 'stroke': BORDER, 'dash': '4 3', 'color': MUTED},     # external, third party, or not real yet
        'ok': _role('ok'), 'warn': _role('warn'), 'block': _role('block'), 'info': _role('info'), 'risk': _role('risk'),
        'new': {'fill': WHITE, 'stroke': P.role('ours', 'ink', mode), 'dash': '4 3', 'color': INK},  # proposed, not built yet
    }
    EDGES = {  # linkStyle values for edges that carry meaning; 'flow' is the default arrow
        'flow': {'stroke': EDGE, 'width': 1.25, 'dash': None, 'color': INK, 'arrow': '-->'},
        'hard': {'stroke': P.role('block', 'ink', mode), 'width': 2.5, 'dash': None, 'color': P.role('block', 'ink', mode), 'arrow': '==>'},
        'planned': {'stroke': P.role('warn', 'ink', mode), 'width': 2, 'dash': '6 4', 'color': P.role('warn', 'ink', mode), 'arrow': '-.->'},
        'related': {'stroke': P.role('info', 'ink', mode), 'width': 1.5, 'dash': '3 3', 'color': P.role('info', 'ink', mode), 'arrow': '-.->'},
        'optional': {'stroke': C['ginnezumi'].ink, 'width': 1.25, 'dash': '2 4', 'color': MUTED, 'arrow': '-.->'},
    }
    GANTT = {  # task state -> look; the same meanings as the classes
        'task': {'fill': C['ai'].tint, 'stroke': C['ai'].ink, 'label': 'Planned', 'tags': '', 'words': 'pale indigo' if mode == 'light' else 'dark indigo'},
        'active': {'fill': C['ai'].soft, 'stroke': C['ai'].ink, 'label': 'In progress', 'tags': 'active, ', 'words': 'indigo'},
        'done': {'fill': C['tetsunezumi'].soft, 'stroke': C['tetsunezumi'].ink, 'label': 'Done', 'tags': 'done, ', 'words': 'grey'},
        'crit': {'fill': C['enji'].tint, 'stroke': C['enji'].ink, 'label': 'Critical path', 'tags': 'crit, ', 'words': 'crimson-edged'},
        'milestone': {'fill': C['ai'].tint, 'stroke': C['ai'].ink, 'label': 'Milestone', 'tags': 'milestone, ', 'words': 'indigo-edged'},  # Mermaid draws it in the task colours
    }
    # Every diagram is its own card (white in light mode, 墨 sumi in dark mode), so it reads the same on any page. SharePoint draws Mermaid with a transparent
    # background, so in dark mode our ink would sit on a dark page. The card also sets the text colour, so anything Mermaid draws in
    # currentColor (labels that inherit, Gantt grid lines) uses our ink, not the page's. Mermaid 11 (SharePoint) honours this. Mermaid 12
    # scopes themeCSS under the diagram and drops it, so render with Mermaid 12 on a white page (tools/ do).
    CARD_CSS = f'&{{background-color:{WHITE};border-radius:6px;color:{INK}}}'
    LEGEND_BOX = {'fill': WHITE, 'stroke': LINE, 'dash': '3 3'}  # the Legend group: white with a dashed hairline, unlike content groups
    LEGEND_POINT = {'fill': WHITE, 'stroke': WHITE}              # invisible ends of the sample lines


    VARS = {  # Mermaid theme variables by group; a diagram's init block carries 'common' plus its type's groups
        'common': {
            'fontFamily': FONT, 'fontSize': f"{TY['body']}px", 'background': WHITE, 'darkMode': mode == 'dark',
            'useGradient': False, 'dropShadow': 'none', 'radius': 2, 'strokeWidth': 1,  # engineering look: flat, crisp, near-square
            'primaryColor': WHITE, 'primaryBorderColor': BORDER, 'primaryTextColor': INK,
            'secondaryColor': PAPER, 'secondaryBorderColor': LINE, 'secondaryTextColor': INK,
            'tertiaryColor': WHITE, 'tertiaryBorderColor': LINE, 'tertiaryTextColor': INK,
            'mainBkg': WHITE, 'textColor': INK, 'titleColor': INK, 'lineColor': EDGE, 'errorBkgColor': C['enji'].tint, 'errorTextColor': C['enji'].ink,
        },
        'flow': {
            'nodeBorder': BORDER, 'nodeTextColor': INK, 'clusterBkg': PAPER, 'clusterBorder': LINE, 'edgeLabelBackground': WHITE,
            'defaultLinkColor': EDGE, 'arrowheadColor': EDGE, 'labelBackground': WHITE,
        },
        'note': {'noteBkgColor': C['kuchiba'].tint, 'noteBorderColor': C['kuchiba'].ink, 'noteTextColor': INK},
        'sequence': {
            'actorBkg': C['ai'].tint, 'actorBorder': C['ai'].ink, 'actorTextColor': INK, 'actorLineColor': BORDER,
            'signalColor': EDGE, 'signalTextColor': INK, 'labelBoxBkgColor': PAPER, 'labelBoxBorderColor': BORDER, 'labelTextColor': INK,
            'loopTextColor': INK, 'activationBkgColor': PAPER, 'activationBorderColor': BORDER, 'sequenceNumberColor': WHITE,
        },
        'gantt': {
            'sectionBkgColor': PAPER, 'altSectionBkgColor': WHITE, 'sectionBkgColor2': PAPER, 'gridColor': LINE, 'excludeBkgColor': RULE,
            'taskBkgColor': GANTT['task']['fill'], 'taskBorderColor': GANTT['task']['stroke'],
            'activeTaskBkgColor': GANTT['active']['fill'], 'activeTaskBorderColor': GANTT['active']['stroke'],
            'doneTaskBkgColor': GANTT['done']['fill'], 'doneTaskBorderColor': GANTT['done']['stroke'],
            'critBkgColor': GANTT['crit']['fill'], 'critBorderColor': GANTT['crit']['stroke'],
            'taskTextColor': INK, 'taskTextLightColor': INK, 'taskTextDarkColor': INK, 'taskTextOutsideColor': INK,
            'taskTextClickableColor': C['ai'].ink, 'todayLineColor': C['shu'].ink, 'vertLineColor': C['shu'].ink,
        },
        'state': {
            'stateBkg': WHITE, 'stateLabelColor': INK, 'altBackground': PAPER, 'compositeBackground': PAPER, 'compositeBorder': LINE,
            'compositeTitleBackground': PAPER, 'transitionColor': EDGE, 'transitionLabelColor': INK, 'specialStateColor': EDGE,
            'innerEndBackground': WHITE, 'labelBackgroundColor': WHITE,
        },
        'class': {'classText': INK},
        'er': {'attributeBackgroundColorOdd': WHITE, 'attributeBackgroundColorEven': PAPER, 'rowOdd': WHITE, 'rowEven': PAPER},
        'requirement': {
            'requirementBackground': WHITE, 'requirementBorderColor': BORDER, 'requirementTextColor': INK,
            'relationColor': EDGE, 'relationLabelBackground': WHITE, 'relationLabelColor': INK,
        },
        'arch': {'archEdgeColor': EDGE, 'archEdgeArrowColor': EDGE, 'archGroupBorderColor': LINE},
        'c4': {'personBkg': C['ai'].tint, 'personBorder': C['ai'].ink},
        'git': {
            **_series('git', SERIES_INK, 8), **_series('gitInv', [WHITE], 8), **_series('gitBranchLabel', [WHITE], 8),
            'commitLabelColor': INK, 'commitLabelBackground': PAPER, 'tagLabelColor': INK, 'tagLabelBackground': C['kuchiba'].tint,
            'tagLabelBorder': C['kuchiba'].ink,
        },
        'pie': {
            **_series('pie', SERIES_SOFT, 12, start=1), 'pieStrokeColor': WHITE, 'pieStrokeWidth': '2px', 'pieOuterStrokeColor': BORDER,
            'pieOuterStrokeWidth': '1px', 'pieOpacity': '1', 'pieSectionTextColor': INK, 'pieTitleTextColor': INK, 'pieLegendTextColor': INK,
            'pieTitleTextSize': f"{TY['title']}px", 'pieSectionTextSize': f"{TY['body']}px", 'pieLegendTextSize': f"{TY['body']}px",
        },
        'quadrant': {  # a quiet 藍白 checkerboard, points in 藍
            'quadrant1Fill': PAPER, 'quadrant2Fill': WHITE, 'quadrant3Fill': PAPER, 'quadrant4Fill': WHITE,
            'quadrant1TextFill': INK, 'quadrant2TextFill': INK, 'quadrant3TextFill': INK, 'quadrant4TextFill': INK,
            'quadrantPointFill': C['ai'].ink, 'quadrantPointTextFill': INK, 'quadrantXAxisTextFill': MUTED, 'quadrantYAxisTextFill': MUTED,
            'quadrantInternalBorderStrokeFill': LINE, 'quadrantExternalBorderStrokeFill': BORDER, 'quadrantTitleFill': INK,
        },
        'xy': {'xyChart': {
            'backgroundColor': WHITE, 'titleColor': INK, 'dataLabelColor': INK, 'legendTextColor': INK,
            'xAxisTitleColor': INK, 'xAxisLabelColor': MUTED, 'xAxisTickColor': BORDER, 'xAxisLineColor': BORDER,
            'yAxisTitleColor': INK, 'yAxisLabelColor': MUTED, 'yAxisTickColor': BORDER, 'yAxisLineColor': BORDER,
            'plotColorPalette': ','.join(SERIES_INK)}},
        'sections': {  # timeline, mindmap, kanban, treemap, journey, radar: soft areas with ink labels
            **_series('cScale', SERIES_SOFT, 12), **_series('cScaleLabel', [INK], 12), **_series('cScaleInv', [INK], 12),
            **_series('cScalePeer', SERIES_INK, 12), **_series('fillType', SERIES_SOFT, 8),
        },
        'radar': {'radar': {'axisColor': BORDER, 'graticuleColor': LINE, 'graticuleOpacity': 1, 'curveOpacity': 0.35, 'curveStrokeWidth': 2}},
        'venn': {**_series('venn', SERIES_SOFT, 8, start=1), 'vennSetTextColor': INK, 'vennTitleTextColor': INK},
        'root': {'git0': C['ai'].ink, 'gitBranchLabel0': WHITE},  # mindmap root: 藍 with white words
    }


def _use(mode):
    if mode not in P.MODES:
        raise ValueError(f'mode must be one of {P.MODES}')
    if mode != MODE:
        _build(mode)


def _mode_of(src):
    """The mode a themed diagram was themed for, read from its init block (light when there is none)."""
    m = re.search(r'%%\{init:\s*(\{.*?\})\s*\}%%', src, re.S)
    return 'dark' if m and json.loads(m.group(1)).get('themeVariables', {}).get('darkMode') else 'light'


TYPE_GROUPS = {
    'flowchart': ['flow'], 'graph': ['flow'], 'sequenceDiagram': ['sequence', 'note'], 'gantt': ['gantt'],
    'stateDiagram-v2': ['flow', 'state', 'note'], 'stateDiagram': ['flow', 'state', 'note'], 'classDiagram': ['flow', 'class', 'note'],
    'erDiagram': ['flow', 'er'], 'journey': ['flow', 'sections'], 'pie': ['pie'], 'quadrantChart': ['quadrant'],
    'xychart-beta': ['xy'], 'xychart': ['xy'], 'timeline': ['sections'], 'mindmap': ['flow', 'sections', 'root'], 'kanban': ['flow', 'sections'],
    'treemap-beta': ['sections'], 'treemap': ['sections'], 'gitGraph': ['git'], 'requirementDiagram': ['flow', 'requirement'],
    'block-beta': ['flow'], 'block': ['flow'], 'packet-beta': ['flow', 'sections'], 'packet': ['flow', 'sections'],
    'architecture-beta': ['flow', 'arch'], 'radar-beta': ['sections', 'radar'], 'venn-beta': ['venn'],
    'C4Context': ['flow', 'c4'], 'C4Container': ['flow', 'c4'], 'C4Component': ['flow', 'c4'],
}
LAYOUT = {  # engineering look: straight connectors, even spacing; one type scale (palette.TYPE)
    'flowchart': {'curve': 'linear', 'nodeSpacing': 36, 'rankSpacing': 48, 'padding': 12, 'diagramPadding': 16, 'htmlLabels': True},
    'sequence': {'mirrorActors': False, 'actorMargin': 40, 'boxMargin': 8, 'noteMargin': 8,
                 'actorFontFamily': FONT, 'messageFontFamily': FONT, 'noteFontFamily': FONT,
                 'actorFontSize': TY['body'], 'messageFontSize': TY['body'], 'noteFontSize': TY['small']},
    'gantt': {'barHeight': 20, 'barGap': 6, 'topPadding': 44, 'fontSize': TY['small'], 'sectionFontSize': TY['small'], 'numberSectionStyles': 2,
              'tickInterval': '1week', 'weekday': 'monday'},  # weekly ticks: d3's default adds a tick at each month start that collides
    'quadrantChart': {'titleFontSize': TY['title'], 'quadrantLabelFontSize': TY['body'], 'pointLabelFontSize': TY['small'],
                      'xAxisLabelFontSize': TY['small'], 'yAxisLabelFontSize': TY['small']},
    'xyChart': {'showLegend': False, 'titleFontSize': TY['title'], 'xAxis': {'labelFontSize': TY['small'], 'titleFontSize': TY['body']},
                'yAxis': {'labelFontSize': TY['small'], 'titleFontSize': TY['body']}},
    'pie': {'textPosition': 0.72},
}
LAYOUT_TYPE = {'flowchart': ('flowchart', 'graph'), 'sequence': ('sequenceDiagram',), 'gantt': ('gantt',),
               'quadrantChart': ('quadrantChart',), 'xyChart': ('xychart-beta', 'xychart'), 'pie': ('pie',)}
LAYOUT_KEYS = {'flowchart', 'sequence', 'gantt', 'pie', 'quadrantChart', 'xyChart', 'timeline', 'mindmap', 'gitGraph', 'journey',
               'state', 'class', 'er', 'requirement', 'block', 'packet', 'kanban', 'architecture', 'radar', 'treemap', 'sankey', 'c4', 'venn', 'wrap'}
BUILT_IN_LEGEND = {'pie', 'radar-beta', 'journey'}  # xychart's own legend only exists from Mermaid 11.17, so it gets a caption
_build('light')
APPROVED = {}  # mode -> types whose drawn colours the gallery has proven; set by load_approved(). Empty means not loaded yet.


def theme_variables(kind):
    out = dict(VARS['common'])
    for g in TYPE_GROUPS.get(kind, list(VARS)):
        out.update(VARS[g])
    return out


def diagram_type(src):
    body = re.sub(r'%%\{.*?\}%%', '', src, flags=re.S)
    body = re.sub(r'^---\n.*?\n---\n', '', body.lstrip(), flags=re.S)
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith('%%'):
            return s.split()[0].rstrip(':')
    raise ValueError('empty diagram')


def init_block(kind, extra=None, mode=None):
    _use(mode or MODE)
    cfg = {'theme': 'base', 'look': 'classic', 'themeVariables': theme_variables(kind), 'fontFamily': FONT, 'themeCSS': CARD_CSS}
    # Mermaid 12 reads the font from the top level, and its default 'neo' look adds drop shadows
    for k, v in LAYOUT.items():
        if kind in LAYOUT_TYPE[k]:
            cfg[k] = json.loads(json.dumps(v))
    for k, v in (extra or {}).items():  # keep a diagram's own layout settings (e.g. gantt barHeight, wrappingWidth)
        if isinstance(v, dict):
            cfg.setdefault(k, {}).update(v)
        else:
            cfg[k] = v
    return '%%{init: ' + json.dumps(cfg, separators=(',', ':'), ensure_ascii=False) + '}%%'


def _strip_generated(src):
    """Remove an earlier init block and generated legend, so theme() can run again on its own output."""
    extra = {}
    m = re.search(r'%%\{init:\s*(\{.*?\})\s*\}%%\n?', src, re.S)
    if m:
        old = json.loads(m.group(1))
        extra = {k: v for k, v in old.items() if k in LAYOUT_KEYS and v != LAYOUT.get(k)}  # themeCSS is never kept: theme() writes the card
        src = src[:m.start()] + src[m.end():]
    src = re.sub(r'\n?[ \t]*%% legend-start.*?%% legend-end[^\n]*', '', src, flags=re.S)
    return src, extra


# ---------------------------------------------------------------- flowchart parsing (enough to count edges and find the deepest node)
_LINK = re.compile(r'\s*(?:<?(?:-{2,}|={2,})[>xo]?|<?-\.+-?>?|~~~+)\s*')
_TEXT_LINK = re.compile(r'(?<![-=.<])(--|==|-\.)\s+[^\n]*?\s+(-->|==>|\.->|---|===|\.-)')
_SKIP = re.compile(r'\s*(%%|subgraph\b|end\b|direction\b|classDef\b|class\b|style\b|linkStyle\b|click\b|flowchart\b|graph\b|$)')


def _mask(s):
    s = re.sub(r'"[^"]*"', '""', s)
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r'\[[^\[\]]*\]|\([^()]*\)|\{[^{}]*\}', lambda m: m.group(0)[0] + m.group(0)[-1], s)
    s = re.sub(r'\|[^|]*\|', '', s)
    return _TEXT_LINK.sub('-->', s)


def _ids(segment):
    return [m.group(1) for part in segment.split('&') for m in [re.match(r'\s*([A-Za-z0-9_][\w]*)', part)] if m]


def parse_flowchart(src):
    """(edges [(a, b, invisible)], node order, unit of each node, direction). A unit is a top-level node or top-level subgraph."""
    edges, order, unit, stack = [], [], {}, []
    direction = 'TD'
    for raw in src.splitlines():
        line = raw.strip()
        m = re.match(r'(flowchart|graph)\s+(\w+)', line)
        if m:
            direction = m.group(2)
            continue
        m = re.match(r'subgraph\s+([A-Za-z0-9_]\w*)', line)
        if m:
            sid = m.group(1)
            unit.setdefault(sid, stack[0] if stack else sid)
            stack.append(sid)
            order.append(sid)
            continue
        if re.match(r'end\s*$', line) and stack:
            stack.pop()
            continue
        if _SKIP.match(line):
            continue
        for stmt in _mask(line).split(';'):
            parts = _LINK.split(stmt)
            links = _LINK.findall(stmt)
            groups = [_ids(p) for p in parts]
            for ids in groups:
                for i in ids:
                    if i not in unit:
                        unit[i] = stack[0] if stack else i
                        order.append(i)
            for (left, right), link in zip(zip(groups, groups[1:]), links):
                for a in left:
                    for b in right:
                        edges.append((a, b, '~~~' in link))
    return edges, order, unit, direction


def _deepest_unit(edges, order, unit):
    succ = defaultdict(set)
    for a, b, _ in edges:
        ua, ub = unit.get(a, a), unit.get(b, b)
        if ua != ub:
            succ[ua].add(ub)
    units = list(dict.fromkeys(unit.get(n, n) for n in order))
    depth, visiting = {}, set()

    def d(u):  # longest path from any root to u
        if u in depth:
            return depth[u]
        if u in visiting:
            return 0
        visiting.add(u)
        preds = [p for p in units if u in succ[p]]
        depth[u] = 1 + max((d(p) for p in preds), default=0)
        visiting.discard(u)
        return depth[u]

    best = max(units, key=lambda u: (d(u), units.index(u)))
    return best


# ---------------------------------------------------------------- legend entries
def classes_used(src):
    found = set(re.findall(r':::(\w+)', src))
    for m in re.findall(r'^\s*class\s+\S+\s+(\w+)', src, re.M):
        found.add(m)
    found -= {'lgpoint', 'lgbox'}
    return [c for c in CLASSES if c in found] + sorted(found - set(CLASSES))


def edges_used(src):
    kinds = set()
    for m in re.finditer(r'^\s*linkStyle\s+([\d,\s]+?)\s+(\S+)\s*$', src, re.M):
        for k, e in EDGES.items():
            if m.group(2).rstrip(';') == linkstyle(e):
                kinds.add(k)
    return [k for k in EDGES if k in kinds]


def declared(src):
    return dict((k.strip(), v.strip()) for k, v in re.findall(r'^\s*%%\s*legend:\s*([\w-]+)\s*=\s*(.+?)\s*$', src, re.M))


def _swatch(style):
    """('box'|'line'|'area'|'diamond'|'text', look) for a legend style name."""
    if style == 'text':
        return 'text', {}
    if style in CLASSES:
        return 'box', CLASSES[style]
    if style in EDGES:
        return 'line', EDGES[style]
    m = re.fullmatch(r'series-(\d+)', style)
    if m:
        i = int(m.group(1)) % len(SERIES_SOFT)
        return 'area', {'fill': SERIES_SOFT[i], 'stroke': SERIES_INK[i], 'dash': None, 'colour': P.SERIES[i]}
    m = re.fullmatch(r'gantt-(\w+)', style)
    if m and m.group(1) in GANTT:
        g = GANTT[m.group(1)]
        return ('diamond' if m.group(1) == 'milestone' else 'box'), {'fill': g['fill'], 'stroke': g['stroke'], 'dash': None, 'words': g['words']}
    raise ValueError(f'legend style {style!r} is not a class, an edge kind, series-N, gantt-STATE or text')


def _gantt_states(src):
    states = set()
    for line in src.splitlines():
        if re.match(r'\s*(%%|title|dateFormat|axisFormat|section|excludes|includes|todayMarker|tickInterval|weekday|inclusiveEndDates|gantt)\b', line):
            continue
        m = re.match(r'[^:]+:\s*(.+)$', line)
        if not m:
            continue
        tags = {t.strip() for t in m.group(1).split(',')}
        hit = tags & {'milestone', 'crit', 'done', 'active'}
        states |= hit or {'task'}
    return [s for s in GANTT if s in states]


def _sections(src, kind):
    if kind == 'timeline':
        return re.findall(r'^\s*section\s+(.+?)\s*$', src, re.M)
    if kind == 'mindmap':
        body = re.sub(r'%%\{.*?\}%%', '', src, flags=re.S)
        lines = [l for l in body.splitlines() if l.strip() and not l.strip().startswith('%%')]
        lines = lines[1:]  # drop the 'mindmap' line; lines[0] is now the root
        if len(lines) < 2:
            return []
        depth1 = min(len(l) - len(l.lstrip()) for l in lines[1:])
        return [re.sub(r'^[\w-]*[\[\(\{]+|[\]\)\}]+$', '', l.strip()) for l in lines[1:] if len(l) - len(l.lstrip()) == depth1]
    return []


def _sequence_entries(src):
    body = re.sub(r'%%.*', '', src)
    out = []
    if re.search(r'\w\s*-[)x]?>>?[+-]?\s*\w|\w\s*->>', body):
        out.append(('text', 'solid arrow = call or request'))
    if re.search(r'\w\s*-->>?[+-]?\s*\w', body):
        out.append(('text', 'dashed arrow = reply'))
    if re.search(r'^\s*(loop|alt|opt|par|critical|break)\b', body, re.M):
        out.append(('text', 'labelled frame = loop or alternative'))
    if re.search(r'^\s*Note\b', body, re.M):
        out.append(('text', 'ochre note = remark'))
    return out


def legend(src):
    """[(style, swatch, look, words)] in display order: automatic entries (words overridable), then declared extras."""
    kind = diagram_type(src)
    decl = declared(src)
    auto, words = [], {**P.ROLE_LABEL, **{f'gantt-{k}': v['label'] for k, v in GANTT.items()}}
    if kind in ('flowchart', 'graph'):
        cls = [c for c in classes_used(src) if c in CLASSES]
        if not cls or _has_unclassed_nodes(src):
            cls = ['plain'] + [c for c in cls if c != 'plain']
        eds = edges_used(src)
        auto += cls + ['flow'] * (not eds or _has_plain_edges(src)) + [e for e in eds if e != 'flow']
    elif kind in ('stateDiagram-v2', 'stateDiagram', 'classDiagram', 'block-beta', 'block'):
        auto += [c for c in classes_used(src) if c in CLASSES]
    elif kind in ('xychart-beta', 'xychart'):
        for i, (shape, name) in enumerate(re.findall(r'^\s*(bar|line)\s+"([^"]+)"', src, re.M)):
            auto.append(f'series-{i}')
            words[f'series-{i}'] = f'{name} ({shape}s)'
    elif kind == 'gantt':
        auto += [f'gantt-{s}' for s in _gantt_states(src)]
    elif kind in ('timeline', 'mindmap'):
        first = 1 if kind == 'mindmap' else 0  # a mindmap's first branch takes the second colour; the root has its own
        for i, name in enumerate(_sections(src, kind), first):
            auto.append(f'series-{i}')
            words.setdefault(f'series-{i}', name)
            decl.setdefault(f'series-{i}', name)
    out, seen = [], set()
    for style in auto + [s for s in decl if s not in auto and s != 'text']:
        if style in seen:
            continue
        seen.add(style)
        sw, look = _swatch(style)
        out.append((style, sw, look, decl.get(style) or words.get(style) or style))
    if kind == 'sequenceDiagram':
        out += [('text', 'text', {}, w) for _, w in _sequence_entries(src)]
    out += [('text', 'text', {}, w) for w in re.findall(r'^\s*%%\s*legend:\s*text\s*=\s*(.+?)\s*$', src, re.M)]
    return out


def _has_unclassed_nodes(src):
    edges, order, unit, _ = parse_flowchart(_without_legend(src))
    subgraphs = set(re.findall(r'^\s*subgraph\s+(\w+)', src, re.M))
    classed = set(re.findall(r'([A-Za-z0-9_]\w*)(?:\[[^\]]*\]|\([^)]*\)|\{[^}]*\}|\[\[.*?\]\]|\(\(.*?\)\))?:::\w+', src))
    for m in re.findall(r'^\s*class\s+(\S+)\s+\w+', src, re.M):
        classed |= set(m.split(','))
    return any(n not in classed and n not in subgraphs for n in order)


def _has_plain_edges(src):
    edges, *_ = parse_flowchart(_without_legend(src))
    visible = [e for e in edges if not e[2]]
    styled = {int(i) for m in re.findall(r'^\s*linkStyle\s+([\d,]+)', _without_legend(src), re.M) for i in m.split(',')}
    return len(visible) > len(styled)


def _without_legend(src):
    return re.sub(r'%% legend-start.*?%% legend-end[^\n]*', '', src, flags=re.S)


# ---------------------------------------------------------------- legend inside the diagram
def _rgb(hexv):
    """rgb() form for HTML inside labels: Mermaid reads '#XXXXXX;' in a label as an entity code and breaks it."""
    return 'rgb({},{},{})'.format(*(int(hexv[i:i + 2], 16) for i in (1, 3, 5)))


def _swatch_html(sw, look):
    if sw == 'box':
        border = 'dashed' if look.get('dash') else 'solid'
        return (f"<span style='display:inline-block;width:12px;height:8px;margin-right:5px;vertical-align:middle;"
                f"background:{_rgb(look['fill'])};border:1px {border} {_rgb(look['stroke'])}'></span>")
    if sw == 'line':
        border = 'dashed' if look.get('dash') else 'solid'
        width = 2 if look['width'] >= 2 else 1
        return (f"<span style='display:inline-block;width:18px;margin-right:5px;vertical-align:middle;"
                f"border-top:{width}px {border} {_rgb(look['stroke'])}'></span>")
    return ''


def _flowchart_legend(src, entries):
    """A small key box in the diagram's bottom corner: one node, 11px text, a swatch per entry.
    It hangs under the last of the deepest nodes (bottom right in TD, right edge in LR) by one invisible link. It has no
    groups and no edges of its own, so it lays out the same in Mermaid 11 (SharePoint) and 12, and edge numbering is untouched."""
    edges, order, unit, _ = parse_flowchart(src)
    if not order or not entries:
        return '', 0
    anchor = _deepest_unit(edges, order, unit)
    rows = ''.join(f"<br/>{_swatch_html(sw, look)}{_q(w)}" for _, sw, look, w in entries)
    label = (f"<div style='text-align:left;font-size:{TY['legend']}px;line-height:1.55'>"
             f"<b style='font-weight:600'>Legend</b>{rows}</div>")
    lines = ['  %% legend-start (generated by wairo; edit the %% legend: lines, not this block)',
             f'  lg_legend["{label}"]:::lgbox',
             f'  {anchor} ~~~ lg_legend',
             f"  classDef lgbox fill:{LEGEND_BOX['fill']},stroke:{LEGEND_BOX['stroke']},stroke-width:1px,stroke-dasharray:{LEGEND_BOX['dash']},color:{MUTED}",
             '  %% legend-end']
    return '\n'.join(lines), 1


def _q(s):
    return s.replace('"', '#quot;')


def caption(src):
    """The text legend for a type that cannot draw one inside the diagram; None when the diagram carries its own."""
    _use(_mode_of(src))
    kind = diagram_type(src)
    if kind in ('flowchart', 'graph') or kind in BUILT_IN_LEGEND:
        return None
    parts = []
    for style, sw, look, w in legend(src):
        if sw == 'text':
            parts.append(w)
        elif sw == 'area':
            noun = 'series' if kind in ('xychart-beta', 'xychart') else 'band'
            parts.append(f'{P.ENGLISH[look["colour"]]} {noun} = {w}')
        elif sw in ('box', 'diamond'):
            noun = {'box': 'bar' if kind == 'gantt' else 'box', 'diamond': 'diamond'}[sw]
            parts.append(f'{look.get("words") or _colour_word(look["stroke"])} {noun} = {w}')
        elif sw == 'line':
            parts.append(f'{_colour_word(look["stroke"])} {"dashed " if look["dash"] else ""}line = {w}')
    return 'Legend: ' + '; '.join(parts) + '.' if parts else None


def _colour_word(hexv):
    for k, c in C.items():
        if hexv.upper() in (c.ink.upper(), c.soft.upper(), c.tint.upper()):
            return P.ENGLISH[k]
    return 'grey'


def theme(src, classmap=None, edges=None, mode='light'):
    _use(mode)
    """The diagram with the standard theme, classes, edge styles and legend; content unchanged.
    classmap: old class name -> standard class. edges: {edge index: kind} for edges that carry meaning (indices as in the source)."""
    src, extra = _strip_generated(src)
    kind = diagram_type(src)
    lines = [l for l in src.strip('\n').splitlines() if not re.match(r'\s*(classDef|linkStyle|style)\s', l)]
    body = '\n'.join(lines)
    for old, new in (classmap or {}).items():
        body = re.sub(rf':::{old}\b', f':::{new}', body)
        body = re.sub(rf'^(\s*class\s+\S+\s+){old}(\s*;?\s*)$', rf'\g<1>{new}\g<2>', body, flags=re.M)
    header, _, rest = body.partition('\n')
    styles = [f'  linkStyle {i} {linkstyle(EDGES[k])}' for i, k in sorted((edges or {}).items())]
    defs = lambda text: [f'  classDef {c} {classdef(CLASSES[c])}' for c in classes_used(text) if c in CLASSES]
    out = '\n'.join([header, *defs(body), rest, *styles]).rstrip()
    block = ''
    if kind in ('flowchart', 'graph'):
        block, _ = _flowchart_legend(out, legend(out))
    out = '\n'.join([header, *defs(body + block), rest, *styles, block]).rstrip()  # classDefs for every class, the legend's too
    return init_block(kind, extra) + '\n' + out + '\n'


# ---------------------------------------------------------------- the gate
COLOUR_LITERAL = re.compile(r'#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(')


APPROVED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'approved.json')  # written by tools/build_gallery.py


def load_approved(path=APPROVED_FILE):
    APPROVED.clear()
    approved = json.load(open(path))['approved']
    approved = approved if isinstance(approved, dict) else {'light': approved}  # older files list light types only
    APPROVED.update({mode: set(kinds) for mode, kinds in approved.items()})


if os.path.exists(APPROVED_FILE):
    load_approved()


def check(src):
    """Raise ValueError listing every rule the themed source breaks."""
    _use(_mode_of(src))
    bad = []
    kind = diagram_type(src)
    mode = _mode_of(src)
    if not APPROVED:
        bad.append('approved types not loaded (load_approved)')
    elif kind not in APPROVED.get(mode, set()):
        bad.append(f'diagram type {kind!r} is not approved for the {mode} theme; add it to the gallery and prove its colours first')
    m = re.search(r'%%\{init:\s*(\{.*?\})\s*\}%%', src, re.S)
    if not m:
        bad.append('no theme init block (run theme())')
    else:
        cfg = json.loads(m.group(1))
        if cfg.get('theme') != 'base' or cfg.get('look') != 'classic' or cfg.get('themeVariables') != theme_variables(kind):
            bad.append('init block changes the theme variables')
        if cfg.get('themeCSS') != CARD_CSS:
            bad.append('themeCSS must be the standard card (white background, ink text) and nothing else')
    rest = src[m.end():] if m else src
    generated = re.findall(r'[ \t]*%% legend-start.*?%% legend-end', rest, re.S)
    if kind in ('flowchart', 'graph'):
        body = _without_legend(rest).rstrip()
        want, _ = _flowchart_legend(body, legend(body))
        if not generated or generated[0].strip() != want.strip():
            bad.append('legend block missing or edited by hand (run theme())')
    rest = _without_legend(rest)
    allowed = {f'classDef {k} {classdef(v)}' for k, v in CLASSES.items()}
    for i, line in enumerate(rest.splitlines(), 1):
        s = line.strip()
        if re.match(r'(style|classDef|linkStyle)\s', s):
            ok = s in allowed or (s.startswith('linkStyle') and any(s.endswith(' ' + linkstyle(e)) for e in EDGES.values()))
            if not ok:
                bad.append(f'line {i}: own styling is not allowed: {s[:90]}')
        elif COLOUR_LITERAL.search(re.sub(r'%%.*', '', s)):
            bad.append(f'line {i}: colour literal: {s[:90]}')
    unknown = [c for c in classes_used(src) if c not in CLASSES]
    if unknown:
        bad.append(f'classes outside the standard set: {unknown}')
    for style in declared(src):
        try:
            _swatch(style)
        except ValueError as e:
            bad.append(str(e))
    if kind == 'gantt':
        bad += _gantt_edge_milestones(src)
    entries = legend(src)
    if kind in BUILT_IN_LEGEND or kind in ('flowchart', 'graph'):
        pass
    elif not entries:
        bad.append('no legend: declare entries with %% legend: <style> = <words> (they become the caption)')
    if bad:
        raise ValueError('diagram check failed:\n  ' + '\n  '.join(bad))
    return True


def _gantt_edge_milestones(src):
    """A milestone on the chart's last day: Mermaid flips its label to the left, across its own diamond."""
    import datetime
    ends, miles = [], []
    for name, tags in re.findall(r'^\s*([^:%\n]+?)\s*:\s*(.+)$', src, re.M):
        if re.match(r'(title|dateFormat|axisFormat|section|excludes|includes|todayMarker|tickInterval|weekday)\b', name):
            continue
        parts = [t.strip() for t in tags.split(',')]
        dates = [datetime.date.fromisoformat(t) for t in parts if re.fullmatch(r'\d{4}-\d{2}-\d{2}', t)]
        date = dates[0] if dates else None
        dur = next((int(t[:-1]) for t in parts if re.fullmatch(r'\d+d', t)), 0)
        if date:
            ends.append(dates[1] if len(dates) > 1 else date + datetime.timedelta(days=dur))  # an end date, or start + duration
            if 'milestone' in parts:
                miles.append((name, date))
    last = max(ends, default=None)
    return [f'gantt milestone {n!r} is on the last day, so Mermaid draws its label across the diamond; end the chart later'
            for n, d in miles if last and d >= last]


def theme_doc(md, plans=None, mode='light'):
    """Theme every Mermaid block in a Markdown document and put a caption under the ones that need it.
    plans: {block number (1-based): {'classmap': ..., 'edges': ...}}."""
    out, last, n = [], 0, 0
    for m in re.finditer(r'```mermaid\n(.*?)```\n?(?:\*Legend:[^\n]*\*\n)?', md, re.S):
        n += 1
        plan = (plans or {}).get(n, {})
        src = theme(m.group(1), plan.get('classmap'), plan.get('edges'), mode)
        check(src)
        cap = caption(src)
        out += [md[last:m.start()], '```mermaid\n', src, '```\n', f'*{cap}*\n' if cap else '']
        last = m.end()
    out.append(md[last:])
    return ''.join(out), n
