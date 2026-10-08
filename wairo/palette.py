"""Wairo palette: the one place a colour or a typeface is defined.

Diagrams (mermaid_theme.py), document section titles and PDF documents (tools/build_doc_pdf.py) all
import from here; none of them may write a hex value of its own. `python3 -m wairo.palette` runs check() and prints the swatches.

Tone: 和色, traditional Japanese colours, calmed for documentation. Each colour keeps its traditional hue; its chroma is
capped (OKLCH C <= 0.14, most <= 0.10) and its lightness set so it reads as text on white.
Engineering tint: the structure reads like a Japanese engineering drawing. Paper is 藍白 (aijiro, the palest indigo dye),
borders are 藍鼠 (ainezumi, indigo grey), connectors are iron grey, text is a cool 墨 ink, and greys lean faintly cool.
Every colour has three steps, in a light set and a dark set:
- ink:  lines, borders, section titles and labels. At least 4.5:1 on the card (縹 and 銀鼠 at least 3.3:1, large titles only).
        The dark inks are hue-lifted: same traditional hue, lighter, so they read on a dark card.
- soft: chart areas (pie slices, bars, timeline and mindmap sections) with ink text on top, at least 7:1.
- tint: node and panel fills with ink text, at least 12:1 (light) or 11:1 (dark).

The greys are generated, not picked: every neutral is the ink mixed into the paper at a fixed share (OKLCH lightness and hue),
plus a small chroma bump that peaks in the mid-greys and keeps the 藍鼠 indigo cast (TINT). Swapping the two anchors for
the dark ones gives the dark greys from the same rule.

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
    dark_ink: str = ''
    dark_soft: str = ''
    dark_tint: str = ''

    def step(self, step='ink', mode='light'):
        return getattr(self, step if mode == 'light' else f'dark_{step}')


COLOURS = {
    'ai': Colour('藍', 'ai', '#165E83', ink='#1B5C7E', soft='#BBD5E7', tint='#E8F5FD',
                  dark_ink='#66B4E2', dark_soft='#294C61', dark_tint='#192E3B'),                       # indigo
    'kon': Colour('紺', 'kon', '#223A70', ink='#233C68', soft='#C3D2EA', tint='#ECF3FF',
                  dark_ink='#A6C5FA', dark_soft='#374865', dark_tint='#212C3D'),                     # deep navy
    'hanada': Colour('縹', 'hanada', '#2792C3', ink='#357E9C', soft='#B9D6E4', tint='#E7F5FC',
                  dark_ink='#4797B8', dark_soft='#254D5F', dark_tint='#172F39'),               # light indigo
    'seiheki': Colour('青碧', 'seiheki', '#478384', ink='#07635D', soft='#B6D9D5', tint='#E6F7F5',
                  dark_ink='#4EBFB5', dark_soft='#1F514D', dark_tint='#14312E'),           # blue-green
    'tokiwa': Colour('常磐', 'tokiwa', '#007B43', ink='#3F7B4A', soft='#C1D8C4', tint='#EBF6EC',
                  dark_ink='#5CA869', dark_soft='#335037', dark_tint='#1F3021'),             # evergreen
    'kuchiba': Colour('朽葉', 'kuchiba', '#917347', ink='#826235', soft='#E0CEB7', tint='#FAF1E6',
                  dark_ink='#B39163', dark_soft='#594325', dark_tint='#362917'),           # fallen-leaf ochre
    'enji': Colour('臙脂', 'enji', '#B94047', ink='#94373D', soft='#E9C8C7', tint='#FFEEED',
                  dark_ink='#EB8184', dark_soft='#623C3C', dark_tint='#3B2424'),                 # cochineal red
    'shu': Colour('朱', 'shu', '#EB6101', ink='#B85725', soft='#E7CABD', tint='#FEEFE9',
                  dark_ink='#CB7044', dark_soft='#603E2F', dark_tint='#3A261D'),                     # vermilion
    'edomurasaki': Colour('江戸紫', 'edomurasaki', '#745399', ink='#755A9A', soft='#D5CCE6', tint='#F4F0FD',
                  dark_ink='#A287CA', dark_soft='#4D4160', dark_tint='#2F273A'), # Edo purple
    'umemurasaki': Colour('梅紫', 'umemurasaki', '#A8497A', ink='#A55D81', soft='#E5C8D5', tint='#FDEEF4',
                  dark_ink='#BE7096', dark_soft='#5E3B4C', dark_tint='#39242E'),   # plum
    'tetsunezumi': Colour('鉄鼠', 'tetsunezumi', '#43474E', ink='#47494B', soft='#CED1D3', tint='#F0F3F5',
                  dark_ink='#B5B7BA', dark_soft='#46484A', dark_tint='#2A2B2D'),  # iron grey
    'ginnezumi': Colour('銀鼠', 'ginnezumi', '#91989F', ink='#7E8182', soft='#CED1D3', tint='#F0F3F5',
                  dark_ink='#848788', dark_soft='#464849', dark_tint='#2A2C2C'),      # silver grey
}

ENGLISH = {  # plain-English colour words for text legends
    'ai': 'indigo', 'kon': 'navy', 'hanada': 'light indigo', 'seiheki': 'blue-green', 'tokiwa': 'green', 'kuchiba': 'ochre',
    'enji': 'crimson', 'shu': 'vermilion', 'edomurasaki': 'purple', 'umemurasaki': 'plum', 'tetsunezumi': 'iron grey', 'ginnezumi': 'silver grey',
}

ANCHORS = {  # the only picked neutrals: the card, the paper and the ink; every other grey is generated from paper and ink
    'light': {'white': '#FFFFFF', 'paper': '#F2F8FA', 'ink': '#20282B'},   # white card, 藍白 aijiro paper, cool 墨 ink
    'dark': {'white': '#161A1C', 'paper': '#1D2325', 'ink': '#E2E9EC'},    # 墨 sumi card, a step lighter paper, pale ink
}
SHARES = {  # how much ink goes into the paper for each generated grey
    'rule': 0.06,     # faint rules: alternate rows, quiet separators
    'line': 0.14,     # hairlines: cluster borders, grid, table rules (decorative, never the only cue)
    'border': 0.56,   # 藍鼠 ainezumi: default node borders (at least 3:1)
    'muted': 0.72,    # secondary text, axis labels, external things
    'edge': 0.82,     # connectors and arrows, iron grey
}
TINT = 0.013  # extra OKLCH chroma at the middle of the paper-to-ink range, so mid-greys keep the indigo cast


def _grey(share, paper, ink_):
    import math
    from .colour import from_oklch
    (Lp, Cp, Hp), (Li, Ci, Hi) = oklch(paper), oklch(ink_)
    dh = ((Hi - Hp + 180) % 360) - 180
    return from_oklch(Lp + (Li - Lp) * share, Cp + (Ci - Cp) * share + TINT * math.sin(math.pi * share), (Hp + dh * share) % 360)


def neutrals(mode='light'):
    a = ANCHORS[mode]
    return {'ink': a['ink'], **{k: _grey(s, a['paper'], a['ink']) for k, s in SHARES.items()}, 'paper': a['paper'], 'white': a['white']}


NEUTRAL = neutrals('light')
NEUTRAL_DARK = neutrals('dark')
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


MIN_TINT_TEXT_DARK = 11.0
MODES = ('light', 'dark')


def ink(name, mode='light'):
    return COLOURS[name].step('ink', mode)


def soft(name, mode='light'):
    return COLOURS[name].step('soft', mode)


def tint(name, mode='light'):
    return COLOURS[name].step('tint', mode)


def role(name, step='ink', mode='light'):
    return COLOURS[ROLE[name]].step(step, mode)


def neutral(mode='light'):
    return NEUTRAL if mode == 'light' else NEUTRAL_DARK


def all_hex(mode='light'):
    """Every colour a published artefact in this mode may contain."""
    out = set(neutral(mode).values())
    for c in COLOURS.values():
        out |= {c.step(s, mode) for s in ('ink', 'soft', 'tint')}
    return {h.upper() for h in out}


def check():
    """Prove the rules in both modes; raise with every failure listed."""
    bad = []
    for mode in MODES:
        N = neutral(mode)
        card, paper, text = N['white'], N['paper'], N['ink']
        min_tint = MIN_TINT_TEXT if mode == 'light' else MIN_TINT_TEXT_DARK
        for k, c in COLOURS.items():
            i, s, t = (c.step(x, mode) for x in ('ink', 'soft', 'tint'))
            need = MIN_TITLE if k in ('ginnezumi', 'hanada') else MIN_INK
            if contrast(i, card) < need:
                bad.append(f'{mode} {k} ink {i} {contrast(i, card):.1f}:1 on the card < {need}')
            if contrast(text, s) < MIN_SOFT_TEXT:
                bad.append(f'{mode} {k} soft {s}: text {contrast(text, s):.1f}:1 < {MIN_SOFT_TEXT}')
            if contrast(text, t) < min_tint:
                bad.append(f'{mode} {k} tint {t}: text {contrast(text, t):.1f}:1 < {min_tint}')
            if oklch(i)[1] > MAX_CHROMA:
                bad.append(f'{mode} {k} ink {i} chroma {oklch(i)[1]:.3f} > {MAX_CHROMA} (not calm)')
        for a, b in itertools.combinations(COLOURS, 2):
            d = delta_e(ink(a, mode), ink(b, mode))
            sib = any({a, b} <= s for s in SIBLINGS)
            if d < (MIN_SIBLING if sib else MIN_APART):
                bad.append(f'{mode} {a}/{b} ΔE {d:.0f} < {MIN_SIBLING if sib else MIN_APART}')
        for name in ('ink', 'muted', 'edge'):
            for bg in ('white', 'paper'):
                if contrast(N[name], N[bg]) < MIN_INK:
                    bad.append(f'{mode} {name} on {bg} {contrast(N[name], N[bg]):.1f}:1')
        if contrast(N['border'], card) < MIN_BORDER or contrast(N['border'], paper) < MIN_BORDER:
            bad.append(f"{mode} border {N['border']} under 3:1")
        for a, b in zip(SERIES, SERIES[1:]):
            if delta_e(soft(a, mode), soft(b, mode)) < 10:
                bad.append(f'{mode} SERIES neighbours {a}/{b} too close as areas')
    for table, names in (('ROLE', ROLE.values()), ('SECTION', SECTION.values()), ('SERIES', SERIES), ('EDGE_ROLE', [ROLE[x] for x in EDGE_ROLE.values()])):
        bad += [f'{table} names unknown colour {n}' for n in names if n not in COLOURS]
    if bad:
        raise SystemExit('palette check failed:\n  ' + '\n  '.join(bad))
    return True


if __name__ == '__main__':
    check()
    print('palette check passed')
    for k, c in COLOURS.items():
        print(f'{c.kanji:4}{c.romaji:12} light {c.ink} {c.soft} {c.tint}  dark {c.dark_ink} {c.dark_soft} {c.dark_tint}  '
              f'uses: {", ".join([r for r, v in ROLE.items() if v == k] + [s for s, v in SECTION.items() if v == k])}')
    for mode in MODES:
        print(mode, 'greys:', neutral(mode))
