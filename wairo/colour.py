"""Colour maths for the palette: sRGB hex <-> OKLCH, WCAG contrast, CIELAB ΔE (CIE76)."""
import math


def _lin(x):
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def _enc(x):
    return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055


def rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def lum(h):
    r, g, b = map(_lin, rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b='#FFFFFF'):
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def lab(h):
    r, g, b = map(_lin, rgb(h))
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    t = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    return 116 * t(Y) - 16, 500 * (t(X) - t(Y)), 200 * (t(Y) - t(Z))


def delta_e(a, b):
    return math.dist(lab(a), lab(b))


def oklch(h):
    r, g, b = map(_lin, rgb(h))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


def from_oklch(L, C, H):
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l_, m_, s_ = L + 0.3963377774 * a + 0.2158037573 * b, L - 0.1055613458 * a - 0.0638541728 * b, L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    out = [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s]
    return '#' + ''.join(f'{round(min(1, max(0, _enc(c))) * 255):02X}' for c in out)
