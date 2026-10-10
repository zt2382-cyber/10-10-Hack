"""Import attributed, explicitly licensed OpenEssays references for noncommercial use.

python3 tools/import_openessays.py --limit 12
Unknown-license entries remain metadata-only in the catalogue. No student text is sent.
"""
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://www.openessays.org'
LICENSES = {'CC_BY_NC_SA_4_0': 'https://creativecommons.org/licenses/by-nc-sa/4.0/'}

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.scripts = []; self.script = False; self.depth = 0; self.text = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script': self.script = True
        if self.depth: self.depth += 1
        elif tag == 'div' and 'prose' in attrs.get('class', '').split(): self.depth = 1
    def handle_endtag(self, tag):
        if tag == 'script': self.script = False
        if self.depth:
            if tag in ('p', 'div'): self.text.append('\n')
            self.depth -= 1
    def handle_data(self, data):
        if self.script: self.scripts.append(data)
        if self.depth: self.text.append(data)


def catalogue(html):
    page = Page(); page.feed(html)
    for script in page.scripts:
        match = re.search(r'self\.__next_f\.push\((.*)\)', script, re.S)
        if not match: continue
        try: value = json.loads(match.group(1))[1]
        except (ValueError, IndexError): continue
        if not isinstance(value, str): continue
        for match in re.finditer(r'\[', value):
            try: rows, _ = json.JSONDecoder().raw_decode(value[match.start():])
            except ValueError: continue
            if isinstance(rows, list) and rows and isinstance(rows[0], dict) and 'originalUrl' in rows[0]:
                return rows
    raise ValueError('OpenEssays page format changed; no catalogue found')


def fetch(url):
    with urlopen(url, timeout=25) as response: return response.read().decode('utf-8')


def run(limit):
    rows = catalogue(fetch(BASE + '/'))
    target = ROOT / 'data/essays'; target.mkdir(exist_ok=True)
    metadata = [{k: r.get(k) for k in ('id', 'urlSlug', 'school', 'program', 'type', 'programType', 'license', 'source', 'originalUrl')} for r in rows]
    (target / 'openessays_catalogue.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+'\n')
    references = []
    for row in rows:
        if row.get('license') not in LICENSES: continue
        slug = row['urlSlug']
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', slug): continue
        url = BASE + '/essays/' + slug
        page = Page(); page.feed(fetch(url))
        text = ''.join(page.text).strip()
        if not text: raise ValueError('No essay body found: ' + slug)
        references.append({'id': 'OE-'+row['id'], 'title': row['type']+' — '+row['school'],
            'school': row['school'], 'program': row['program'], 'essay_type': row['type'],
            'degree_level': 'undergraduate' if row['programType'] == 'BACHELORS' else 'graduate',
            'text': text, 'source_url': url, 'original_url': row['originalUrl'],
            'attribution': row['source'], 'license': row['license'], 'license_url': LICENSES[row['license']],
            'synthetic': False, 'permitted_use': 'noncommercial', 'retrieved_at': datetime.now(timezone.utc).isoformat()})
        if len(references) >= limit: break
    (target / 'openessays_bank.json').write_text(json.dumps(references, indent=2, ensure_ascii=False)+'\n')
    print('Imported', len(references), 'licensed essays;', len(metadata), 'catalogue references retained.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--limit', type=int, default=12)
    args = parser.parse_args()
    if args.limit < 1: parser.error('limit must be positive')
    run(args.limit)
