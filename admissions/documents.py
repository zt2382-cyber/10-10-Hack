"""Local PDF/OCR adapters and conservative evidence-backed text extraction."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from admissions.core import require


def read_pdf(path, ocr=False):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError('Install PDF support with: pip install -e ".[documents]"') from exc
    path = Path(path).resolve()
    reader = PdfReader(path)
    require(not reader.is_encrypted, 'Decrypt the PDF before importing')
    pages = []
    for number, page in enumerate(reader.pages, 1):
        text = page.extract_text(extraction_mode='layout') or ''
        method = 'pdf-text'
        if ocr and len(text.strip()) < 40:
            require(shutil.which('pdftoppm') and shutil.which('tesseract'), 'OCR requires pdftoppm and tesseract installed on PATH')
            with tempfile.TemporaryDirectory() as directory:
                prefix = str(Path(directory) / 'page')
                subprocess.run(['pdftoppm', '-f', str(number), '-l', str(number), '-singlefile', '-r', '200', '-png', str(path), prefix], check=True, capture_output=True, timeout=60)
                result = subprocess.run(['tesseract', prefix+'.png', 'stdout', '-l', 'eng'], check=True, capture_output=True, text=True, timeout=60)
                text, method = result.stdout, 'ocr'
        pages.append({'page': number, 'text': text, 'method': method,
                      'warning': 'Sparse page: inspect for missing scanned content' if len(text.strip()) < 40 else None})
    require(bool(pages), 'PDF has no pages')
    return pages


def combine_pages(pages):
    content, ranges = '', []
    for page in pages:
        start = len(content)
        content += page['text']
        ranges.append({**page, 'start_char': start, 'end_char': len(content)})
        content += '\n'
    return content, ranges


def evidence(content, start, end, pages):
    result = {'start_char': start, 'end_char': end, 'quoted_text': content[start:end]}
    for page in pages:
        if page['start_char'] <= start < page['end_char']:
            result.update(page=page['page'], page_start_char=start-page['start_char'], method=page['method'])
            break
    return result


def extract_freeform(content, pages=None):
    """Extract only explicit assertions; unknown details remain null."""
    pages = pages or []
    records, activities, courses, activity_evidence, course_evidence = [], [], [], [], []
    essay_heading = re.search(r'(?im)^\s*(?:personal statement|essay)\s*:\s*\n', content)
    essay_span = None
    if essay_heading:
        next_heading = re.search(r'(?im)^\s*(?:activities|honors|education|courses|test scores)\s*:\s*$', content[essay_heading.end():])
        essay_span = (essay_heading.end(), essay_heading.end()+next_heading.start() if next_heading else len(content))
    # Narrative assertions in an essay are not canonical profile updates.
    def in_essay(position):
        return essay_span is not None and essay_span[0] <= position < essay_span[1]

    # A complete GPA declaration is necessary; never infer a scale or weighting.
    pattern = r'(?:(?P<pre>unweighted|weighted)\s+)?GPA\s*(?:is|of|:|=)?\s*(?P<value>\d+(?:\.\d+)?)\s*(?:/|out of)\s*(?P<scale>\d+(?:\.\d+)?)(?:\s*(?P<post>unweighted|weighted))?'
    for match in re.finditer(pattern, content, re.I):
        if in_essay(match.start()):
            continue
        weighting = match['pre'] or match['post']
        ev = evidence(content, *match.span(), pages)
        if weighting is None:
            records.append(('gpa', None, ev, 'GPA weighting is missing; stage an explicit correction'))
        else:
            records.append(('gpa', {'value': float(match['value']), 'scale': float(match['scale']), 'weighted': weighting.lower() == 'weighted'}, ev, None))
    # A raw score does not prove that it was submitted.
    for match in re.finditer(r'\b(?:submitted\s+SAT|SAT\s+submitted)\s*(?:score|is|of|:|=)?\s*(\d{3,4})\b', content, re.I):
        prefix = content[max(content.rfind('\n', 0, match.start())+1, match.start()-60):match.start()]
        if in_essay(match.start()) or re.search(r'\b(?:not|never|haven.t|hasn.t|didn.t|no)\b', prefix, re.I):
            continue
        records.append(('sat_submitted', int(match[1]), evidence(content, *match.span(), pages), None))
    for match in re.finditer(r'\b(?:intended major|academic interests?)\s*:\s*([^\n]+)', content, re.I):
        if in_essay(match.start()):
            continue
        records.append(('interests', [x.strip().casefold() for x in match[1].split(';') if x.strip()], evidence(content, *match.span(), pages), None))
    offset = 0
    for line in content.splitlines(keepends=True):
        if in_essay(offset):
            offset += len(line)
            continue
        text = line.strip()
        ev = evidence(content, offset, offset+len(line.rstrip('\r\n')), pages)
        # Recognize labeled application/resume entries, retaining unparsed descriptions.
        match = re.match(r'(?:activity|extracurricular)\s*:\s*([^;]+)(.*)', text, re.I)
        narrative = re.search(r'\b(?:I am|I was|I served as)\s+(?:the\s+)?(captain|president|founder|volunteer|member)\s+(?:of|at|in)\s+([^.;\n]+)', text, re.I)
        if match or narrative:
            name = match[1].strip() if match else narrative[2].strip()
            role = re.search(r'\brole\s*:\s*([^;]+)', text, re.I)
            hours = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:/|per\s+)\s*week', text, re.I)
            duration = re.search(r'(\d+(?:\.\d+)?)\s*(years?|months?)\b', text, re.I)
            achievement = re.search(r'\bachievement\s*:\s*([^;]+)', text, re.I)
            activities.append({'name': name, 'role': role[1].strip() if role else narrative[1].lower() if narrative else None,
                'hours_per_week': float(hours[1]) if hours else None,
                'duration': {'value': float(duration[1]), 'unit': duration[2].lower().rstrip('s')} if duration else None,
                'achievements': [achievement[1].strip()] if achievement else [], 'description': text})
            activity_evidence.append(ev)
        # Recognize explicit rows; do not reinterpret grade scales.
        match = re.match(r'course\s*:\s*([^;]+);\s*grade\s*:\s*([^;]+)(.*)', text, re.I)
        if match:
            tail = match[3]
            term = re.search(r'\bterm\s*:\s*([^;]+)', tail, re.I)
            credits = re.search(r'\bcredits\s*:\s*(\d+(?:\.\d+)?)', tail, re.I)
            name = match[1].strip()
            level = 'AP' if name.upper().startswith('AP ') else 'IB' if name.upper().startswith('IB ') else None
            courses.append({'name': name, 'grade': match[2].strip(), 'term': term[1].strip() if term else None,
                            'credits': float(credits[1]) if credits else None, 'level': level})
            course_evidence.append(ev)
        else:
            # Common transcript rows: term | course | grade | credits (header excluded).
            cells = [x.strip() for x in re.split(r'\s*\|\s*|\t+|\s{2,}', text)]
            if len(cells) == 4 and re.fullmatch(r'(?:19|20)\d{2}(?:[- /].+)?', cells[0]) and re.fullmatch(r'[ABCDF][+-]?|\d{1,3}(?:\.\d+)?', cells[2]) and re.fullmatch(r'\d+(?:\.\d+)?', cells[3]):
                courses.append({'term': cells[0], 'name': cells[1], 'grade': cells[2], 'credits': float(cells[3]),
                                'level': 'AP' if cells[1].upper().startswith('AP ') else 'IB' if cells[1].upper().startswith('IB ') else None})
                course_evidence.append(ev)
        offset += len(line)
    if activities:
        records.append(('activity_records', activities, {'items': activity_evidence}, None))
        records.append(('activities', list(dict.fromkeys(a['name'].casefold() for a in activities)), {'items': activity_evidence}, None))
    if courses:
        records.append(('courses', courses, {'items': course_evidence}, None))
    # Explicit essay headings delimit a contiguous essay section.
    match = re.search(r'(?im)^\s*(?:personal statement|essay)\s*:\s*\n', content)
    if match:
        end_match = re.search(r'(?im)^\s*(?:activities|honors|education|courses|test scores)\s*:\s*$', content[match.end():])
        end = match.end()+end_match.start() if end_match else len(content)
        if content[match.end():end].strip():
            records.append(('essay_draft', content[match.end():end], evidence(content, match.end(), end, pages), None))
    return records
