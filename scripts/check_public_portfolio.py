#!/usr/bin/env python3
"""Check public claim boundaries, integration drift, private endpoints and links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import json
import re
import sys
from export_wix import render

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs = []; self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.add(a['id'])
        if tag in ('a', 'link', 'img', 'script'):
            value = a.get('href', a.get('src'))
            if value: self.refs.append(value)

def main():
    errors = []
    p = json.loads((ROOT / 'governance/profile.json').read_text())
    if p['authority'] != 'HUMAN_PRIMARY': errors.append('Human authority changed')
    if 'runtime' in p: errors.append('Private runtime included in public claims')
    if any(p['sync'].get(k) == 'AUTOMATIC' for k in ('website','github','resume')):
        errors.append('Unverified automatic synchronization claim')
    for claim in p['claims']:
        if not (ROOT / claim['source'].split('#')[0]).is_file():
            errors.append('Missing claim source: ' + claim['id'])
    if not (ROOT / p['artifacts']['resume_path']).is_file(): errors.append('Resume target missing')
    htmls = ['index.html','career-verification.html','credentials.html','verify.html','verification/live/index.html','integrations/wix-career-embed.html']
    for name in htmls:
        path=ROOT/name; text=path.read_text(); parser=Links();parser.feed(text)
        if '<html lang="en"' not in text or 'name="viewport"' not in text: errors.append(name+': document metadata missing')
        for ref in parser.refs:
            u=urlsplit(ref)
            if u.scheme or u.netloc: continue
            target=path.parent/unquote(u.path) if u.path else path
            if not target.is_file(): errors.append(name+': missing target '+ref); continue
            if u.fragment and target.suffix=='.html':
                dest=Links();dest.feed(target.read_text())
                if u.fragment not in dest.ids: errors.append(name+': missing fragment '+ref)
        if re.search(r"fetch\s*\(|XMLHttpRequest|WebSocket|VERIFIED SNAPSHOT",text):
            errors.append(name+': private runtime transport or fallback data')
    # Scan the whole versioned text surface; report filenames only, never values.
    patterns=[r'https?://[^\s\"\'<>]*\.ts\.net',r'person\.damien\b',r'camera\.(?:back_door|kitchen)',r'\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}',r'\b(?:192\.168|10\.\d{1,3})\.\d{1,3}\.\d{1,3}\b']
    for path in ROOT.rglob('*'):
        if '.git' in path.parts or '.github' in path.parts or '__pycache__' in path.parts or not path.is_file(): continue
        if path.suffix not in ('.html','.md','.json','.yaml','.yml','.js','.py'):continue
        # The checker contains detection expressions, not private values.
        if path.name==Path(__file__).name:continue
        if any(re.search(x,path.read_text(),re.I) for x in patterns): errors.append(str(path.relative_to(ROOT))+': private marker')
    if (ROOT/'integrations/wix-career-embed.html').read_text()!=render(): errors.append('Wix export drift')
    if errors:
        print('\n'.join(errors)); return 1
    print('PUBLIC_PORTFOLIO=PASS: claims, privacy patterns, local links, static boundaries, Wix parity')
    return 0

if __name__=='__main__':sys.exit(main())
