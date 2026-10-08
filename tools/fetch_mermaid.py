"""Download the pinned Mermaid bundles into vendor/mermaid/ and verify their SHA-256. python3 tools/fetch_mermaid.py"""
import hashlib
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PINS = json.load(open(os.path.join(ROOT, 'tools', 'mermaid-versions.json')))
DEST = os.path.join(ROOT, 'vendor', 'mermaid')


def path(version):
    return os.path.join(DEST, f'mermaid-{version}.min.js')


def fetch(version):
    want = PINS['versions'][version]
    p = path(version)
    if os.path.exists(p) and hashlib.sha256(open(p, 'rb').read()).hexdigest() == want:
        return p
    os.makedirs(DEST, exist_ok=True)
    data = urllib.request.urlopen(PINS['url'].format(version=version), timeout=120).read()
    got = hashlib.sha256(data).hexdigest()
    if got != want:
        raise SystemExit(f'mermaid {version}: SHA-256 {got} does not match the pinned {want}')
    open(p, 'wb').write(data)
    return p


if __name__ == '__main__':
    for v in PINS['versions']:
        print(v, fetch(v))
