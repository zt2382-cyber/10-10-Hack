import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from admissions.core import connect, validate_profile
from admissions.documents import combine_pages, extract_freeform, read_pdf
from admissions.intake import stage_document, review, publish


class DocumentTests(unittest.TestCase):
    def test_freeform_to_reviewed_snapshot(self):
        db = connect(':memory:')
        try:
            path = Path(__file__).resolve().parents[1] / 'examples/application.txt'
            report = stage_document(db, path, 'freeform', 'student', True, 'synthetic')
            values = {c['field']: c['value'] for c in report['candidates']}
            self.assertEqual(values['gpa']['value'], 3.8)
            self.assertEqual(values['activity_records'][0]['role'], 'Captain')
            self.assertEqual(values['activity_records'][0]['hours_per_week'], 8)
            self.assertEqual(values['activity_records'][1]['duration']['unit'], 'month')
            self.assertEqual(len(values['courses']), 2)
            self.assertEqual(values['courses'][1]['grade'], 'B+')
            self.assertIn('Teaching a younger teammate', values['essay_draft'])
            self.assertEqual(db.execute('SELECT original_bytes FROM document_assets').fetchone()[0], path.read_bytes())
            for candidate in report['candidates']:
                self.assertIsNone(candidate['issue'])
                evidence = candidate['evidence']
                for item in evidence.get('items', [evidence]):
                    self.assertEqual(item['page'], 1)
                    self.assertEqual(item['quoted_text'], (path.read_text()+'\n')[item['start_char']:item['end_char']])
                review(db, candidate['id'], 'accepted', 'reviewer')
            result = publish(db, report['batch_id'], 'snapshot', '2024-11-01')
            self.assertEqual(result['profile']['courses'], values['courses'])
        finally:
            db.close()

    def test_missing_weighting_not_inferred_and_score_not_assumed_submitted(self):
        records = extract_freeform('My GPA is 3.8 out of 4.0. SAT score: 1450.\n')
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0][1])
        self.assertIn('weighting', records[0][3])

    def test_second_page_offsets(self):
        content, pages = combine_pages([{'page': 1, 'text': 'First page', 'method': 'pdf-text'},
                                       {'page': 2, 'text': 'Weighted GPA: 4.2 / 5.0', 'method': 'ocr'}])
        record = extract_freeform(content, pages)[0]
        self.assertEqual(record[2]['page'], 2)
        self.assertEqual(record[2]['method'], 'ocr')
        self.assertEqual(content[record[2]['start_char']:record[2]['end_char']], record[2]['quoted_text'])

    def test_pdf_page_adapter_and_ocr_fallback(self):
        class Page:
            def __init__(self, text): self.text = text
            def extract_text(self, **kwargs): return self.text
        class Reader:
            is_encrypted = False
            def __init__(self, path): self.pages = [Page('Digital text ' * 10), Page('')]
        with patch.dict(sys.modules, {'pypdf': types.SimpleNamespace(PdfReader=Reader)}):
            pages = read_pdf('fixture.pdf')
            self.assertIsNotNone(pages[1]['warning'])
            with patch('admissions.documents.shutil.which', return_value='/tool'), patch('admissions.documents.subprocess.run') as run:
                run.return_value = types.SimpleNamespace(stdout='OCR extracted page')
                pages = read_pdf('fixture.pdf', ocr=True)
                self.assertEqual(pages[0]['method'], 'pdf-text')
                self.assertEqual(pages[1]['method'], 'ocr')
                self.assertEqual(run.call_count, 2)
            with patch('admissions.documents.shutil.which', return_value=None):
                with self.assertRaises(ValueError): read_pdf('fixture.pdf', ocr=True)

    def test_rich_schema_rejects_invalid_hours_and_keeps_grade_scale(self):
        with self.assertRaises(ValueError):
            validate_profile({'activity_records': [{'name': 'robotics', 'hours_per_week': 200}]})
        validate_profile({'courses': [{'name': 'Math', 'grade': '87/100'}]})

    def test_no_extraction_preserves_document_without_publishing(self):
        db = connect(':memory:')
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'unrecognized.txt'
                path.write_text('Unrecognized layout retained for manual correction.')
                report = stage_document(db, path, 'freeform', 'student', True, 'synthetic')
            self.assertEqual(report['candidates'], [])
            self.assertEqual(len(report['documents']), 1)
            with self.assertRaises(ValueError): publish(db, report['batch_id'], 'snapshot', '2024-11-01')
        finally: db.close()
