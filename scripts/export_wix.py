#!/usr/bin/env python3
"""Generate an integration fragment from the existing career portal."""
from pathlib import Path
import re
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://damiengolden3674.github.io/the-control-layer-public/'

def render():
    source = (ROOT / 'career-verification.html').read_text()
    source = re.sub(r'href="([^"]+)"', lambda m: 'href="' + urljoin(BASE, m[1]) + '"', source)
    return source.replace('<head>', '<head>\n<base target="_top">', 1)

if __name__ == '__main__':
    target = ROOT / 'integrations/wix-career-embed.html'
    target.parent.mkdir(exist_ok=True)
    target.write_text(render())
    print('Wix integration export generated; no Wix publication performed.')
