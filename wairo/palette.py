"""Wairo palette: the one place a colour or a typeface is defined.

Diagrams (mermaid_theme.py), document section titles and PDF documents (tools/build_doc_pdf.py) all
import from here; none of them may write a hex value of its own. `python3 -m wairo.palette` runs check() and prints the swatches.

Tone: 和色, traditional Japanese colours, calmed for documentation. Each colour keeps its traditional hue; its chroma is
capped (OKLCH C <= 0.14, most <= 0.10) and its lightness set so it reads as text on white.
Engineering tint: the structure reads like a Japanese engineering drawing. Paper is 藍白 (aijiro, the palest indigo dye),
borders are 藍鼠 (ainezumi, indigo grey), connectors are iron grey, text is a cool 墨 ink, and greys lean faintly cool.
Every colour has three steps:
- ink:  lines, borders, section titles and labels. At least 4.5:1 on white (縹 and 銀鼠 at least 3.3:1, large titles only).
- soft: chart areas (pie slices, bars, timeline and mindmap sections) with ink text on top, at least 7:1.
- tint: node and panel fills with ink text, at least 12:1.

Colour carries meaning only. A meaning (ROLE, SECTION, SERIES) names a colour; nothing names a hex.

Type follows the Japanese Digital Agency design system (デジタル庁デザインシステム): Noto Sans JP for Japanese and Latin
alike, so mixed text (和欧混植) shares one design, and Noto Sans Mono for code. PDFs and rendered images carry the font
inside them. SharePoint draws diagrams in each reader's browser, so the fallback uses only fonts every machine already has, nothing
downloaded: Windows 10 and 11 ship Segoe UI, Yu Gothic UI and Consolas in the base install (Meiryo and BIZ UD are an
optional Japanese feature, so they are not relied on); macOS ships Hiragino Sans and Menlo.
"""
import itertools
from dataclasses import dataclass

from .colour import contrast, delta_e, oklch


@dataclass(frozen=True)
class Colour:
    kanji: str
    romaji: str
    traditional: str  # the colour's traditional reference value, kept for provenance; never used directly
    ink: str
    soft: str
    tint: str


COLOURS = {
    'ai': Colour('藍', 'ai', '#165E83', ink='#1B5C7E', soft='#BBD5E7', tint='#E8F5FD'),                       # indigo
    'kon': Colour('紺', 'kon', '#223A70', ink='#233C68', soft='#C3D2EA', tint='#ECF3FF'),                     # deep navy
    'hanada': Colour('縹', 'hanada', '#2792C3', ink='#357E9C', soft='#B9D6E4', tint='#E7F5FC'),               # light indigo
    'seiheki': Colour('青碧', 'seiheki', '#478384', ink='#07635D', soft='#B6D9D5', tint='#E6F7F5'),           # blue-green
    'tokiwa': Colour('常磐', 'tokiwa', '#007B43', ink='#3F7B4A', soft='#C1D8C4', tint='#EBF6EC'),             # evergreen
    'kuchiba': Colour('朽葉', 'kuchiba', '#917347', ink='#826235', soft='#E0CEB7', tint='#FAF1E6'),           # fallen-leaf ochre
    'enji': Colour('臙脂', 'enji', '#B94047', ink='#94373D', soft='#E9C8C7', tint='#FFEEED'),                 # cochineal red
    'shu': Colour('朱', 'shu', '#EB6101', ink='#B85725', soft='#E7CABD', tint='#FEEFE9'),                     # vermilion
    'edomurasaki': Colour('江戸紫', 'edomurasaki', '#745399', ink='#755A9A', soft='#D5CCE6', tint='#F4F0FD'), # Edo purple
    'umemurasaki': Colour('梅紫', 'umemurasaki', '#A8497A', ink='#A55D81', soft='#E5C8D5', tint='#FDEEF4'),   # plum
    'tetsunezumi': Colour('鉄鼠', 'tetsunezumi', '#43474E', ink='#47494B', soft='#CED1D3', tint='#F0F3F5'),  # iron grey
    'ginnezumi': Colour('銀鼠', 'ginnezumi', '#91989F', ink='#7E8182', soft='#CED1D3', tint='#F0F3F5'),      # silver grey
}

ENGLISH = {  # plain-English colour words for text legends
    'ai': 'indigo', 'kon': 'navy', 'hanada': 'light indigo', 'seiheki': 'blue-green', 'tokiwa': 'green', 'kuchiba': 'ochre',
    'enji': 'crimson', 'shu': 'vermilion', 'edomurasaki': 'purple', 'umemurasaki': 'plum', 'tetsunezumi': 'iron grey', 'ginnezumi': 'silver grey',
}

NEUTRAL = {  # engineering tint: cool 墨 ink and iron-grey linework on 藍白 paper
    'ink': '#20282B',     # body text, node labels (15.0:1 on white)
    'muted': '#505D63',   # secondary text, axis labels, external things (6.8:1)
    'edge': '#3C4A50',    # connectors and arrows, iron grey (9.2:1)
    'border': '#6B7E86',  # 藍鼠 ainezumi: default node borders (4.2:1 on white, 4.0:1 on paper)
    'line': '#D0D9DD',    # hairlines: cluster borders, grid, table rules (decorative, never the only cue)
    'rule': '#E4EBEE',    # faint rules: alternate rows, quiet separators
    'paper': '#F2F8FA',   # 藍白 aijiro: groups, table headers, page panels
    'white': '#FFFFFF',   # nodes and page
}
BORDER = NEUTRAL['border']

# Meanings. A diagram class or edge, a document section, a chart series names one of the colours above.
ROLE = {  # diagram classes and edge kinds -> colour
    'ours': 'ai',            # our own system, the subject of the diagram
    'ok': 'tokiwa',          # done, ready, passing
    'warn': 'kuchiba',       # planned, caution, waiting
    'block': 'enji',         # hard dependency, gap, failing
    'info': 'seiheki',       # related, context
    'risk': 'edomurasaki',   # risk, decision, coordination
}
ROLE_LABEL = {  # default legend wording; a diagram may override it with `%% legend: <name>=<words>`
    'plain': 'Component', 'ours': 'Our system', 'gen': 'Generated output', 'ext': 'External or not built',
    'ok': 'Done or ready', 'warn': 'Planned or waiting', 'block': 'Blocked or gap', 'info': 'Related context',
    'risk': 'Risk or decision', 'new': 'Proposed',
    'hard': 'Hard dependency', 'planned': 'Planned link', 'related': 'Related', 'optional': 'Optional', 'flow': 'Flow',
}
EDGE_ROLE = {'hard': 'block', 'planned': 'warn', 'related': 'info'}  # 'optional' and 'flow' stay neutral

SECTION = {  # document section titles (issue or wiki templates) -> colour. Siblings share a hue family; every other pair is far apart.
    'Needs attention': 'shu', 'Risks and decisions': 'shu',
    'Summary': 'ai', 'Why': 'kon', 'Scope and approach': 'hanada',
    'Evidence': 'seiheki', 'Design': 'umemurasaki', 'Findings': 'edomurasaki',
    'Out of scope': 'kuchiba', 'Done when': 'tokiwa', 'Depends on': 'enji',
    'Files': 'tetsunezumi', 'Links': 'ginnezumi',
}
SIBLINGS = [{'ai', 'kon', 'hanada'}, {'tetsunezumi', 'ginnezumi'}]
SECTION_COLOUR = {k: COLOURS[v].ink for k, v in SECTION.items()}

SERIES = ['ai', 'kuchiba', 'tokiwa', 'enji', 'edomurasaki', 'seiheki', 'umemurasaki', 'tetsunezumi']  # chart order; neighbours far apart

# Atlassian (Jira, Confluence) draws panels in its own fixed colours; these are the meanings each carries, so a ticket
# and a diagram say the same thing (red panel = enji 'block', yellow = kuchiba 'warn', and so on).
JIRA_PANEL = {'error': 'block', 'warning': 'warn', 'note': 'risk', 'success': 'ok', 'info': 'info'}

FONT_SANS = ['Noto Sans JP',           # designed look (installed, or embedded in PDFs and images)
             'Segoe UI', 'Yu Gothic UI',  # Windows base install: Latin, then Japanese characters
             'Hiragino Sans',             # macOS base install: Latin and Japanese
             'system-ui', 'sans-serif']
FONT_MONO = ['Noto Sans Mono', 'Consolas', 'Menlo', 'monospace']  # Consolas: Windows base; Menlo: macOS base
TYPE = {
    'diagram': {'body': 13, 'small': 12, 'legend': 11, 'title': 16, 'regular': 400, 'strong': 600},   # px
    'print': {'body': 9.4, 'leading': 1.62, 'h1': 19, 'h2': 13.5, 'h3': 11, 'h4': 10, 'small': 8, 'table': 8.5, 'code': 8.2},  # pt
}


def font_stack(names, quoted=True):
    """CSS font-family list. Mermaid's init block needs quoted=False (any quote breaks it; CSS accepts unquoted names)."""
    generic = {'system-ui', 'sans-serif', 'monospace', 'serif'}
    return ', '.join(n if (n in generic or not quoted) else f'"{n}"' for n in names)


# Limits check() enforces
MIN_INK, MIN_TITLE, MIN_SOFT_TEXT, MIN_TINT_TEXT, MIN_BORDER = 4.5, 3.3, 7.0, 12.0, 3.0
MIN_APART, MIN_SIBLING, MAX_CHROMA = 25, 12, 0.145


def ink(name):
    return COLOURS[name].ink


def soft(name):
    return COLOURS[name].soft


def tint(name):
    return COLOURS[name].tint


def role(name, step='ink'):
    return getattr(COLOURS[ROLE[name]], step)


def all_hex():
    """Every colour a published artefact may contain."""
    out = set(NEUTRAL.values()) | {BORDER}
    for c in COLOURS.values():
        out |= {c.ink, c.soft, c.tint}
    return {h.upper() for h in out}


def check():
    """Prove the rules; raise with every failure listed."""
    bad = []
    for k, c in COLOURS.items():
        large_only = k in ('ginnezumi', 'hanada')
        need = MIN_TITLE if large_only else MIN_INK
        if contrast(c.ink) < need:
            bad.append(f'{k} ink {c.ink} {contrast(c.ink):.1f}:1 on white < {need}')
        if contrast(NEUTRAL['ink'], c.soft) < MIN_SOFT_TEXT:
            bad.append(f'{k} soft {c.soft}: ink text {contrast(NEUTRAL["ink"], c.soft):.1f}:1 < {MIN_SOFT_TEXT}')
        if contrast(NEUTRAL['ink'], c.tint) < MIN_TINT_TEXT:
            bad.append(f'{k} tint {c.tint}: ink text {contrast(NEUTRAL["ink"], c.tint):.1f}:1 < {MIN_TINT_TEXT}')
        if oklch(c.ink)[1] > MAX_CHROMA:
            bad.append(f'{k} ink {c.ink} chroma {oklch(c.ink)[1]:.3f} > {MAX_CHROMA} (not calm)')
    for a, b in itertools.combinations(COLOURS, 2):
        d = delta_e(COLOURS[a].ink, COLOURS[b].ink)
        sib = any({a, b} <= s for s in SIBLINGS)
        if d < (MIN_SIBLING if sib else MIN_APART):
            bad.append(f'{a}/{b} ΔE {d:.0f} < {MIN_SIBLING if sib else MIN_APART}')
    for name in ('ink', 'muted', 'edge'):
        for bg in ('white', 'paper'):
            if contrast(NEUTRAL[name], NEUTRAL[bg]) < MIN_INK:
                bad.append(f'{name} on {bg} {contrast(NEUTRAL[name], NEUTRAL[bg]):.1f}:1')
    if contrast(BORDER) < MIN_BORDER or contrast(BORDER, NEUTRAL['paper']) < MIN_BORDER:
        bad.append(f'border {BORDER} under 3:1')
    for table, names in (('ROLE', ROLE.values()), ('SECTION', SECTION.values()), ('SERIES', SERIES), ('EDGE_ROLE', [ROLE[x] for x in EDGE_ROLE.values()])):
        bad += [f'{table} names unknown colour {n}' for n in names if n not in COLOURS]
    for a, b in zip(SERIES, SERIES[1:]):
        if delta_e(soft(a), soft(b)) < 10:
            bad.append(f'SERIES neighbours {a}/{b} too close as areas')
    if bad:
        raise SystemExit('palette check failed:\n  ' + '\n  '.join(bad))
    return True


if __name__ == '__main__':
    check()
    print('palette check passed')
    for k, c in COLOURS.items():
        print(f'{c.kanji:4}{c.romaji:12} ink {c.ink} ({contrast(c.ink):4.1f}:1)  soft {c.soft}  tint {c.tint}  '
              f'uses: {", ".join([r for r, v in ROLE.items() if v == k] + [s for s, v in SECTION.items() if v == k])}')
