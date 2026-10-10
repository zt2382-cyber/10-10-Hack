import argparse
import json
from pathlib import Path
from admissions.core import connect, ingest, search


def main():
    parser = argparse.ArgumentParser(description='Applicant evidence retrieval prototype')
    parser.add_argument('--db', default='applicants.db')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    load = sub.add_parser('import')
    load.add_argument('file', type=Path)
    index = sub.add_parser('index-essays')
    index.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2')
    index.add_argument('--revision')
    index.add_argument('--include-synthetic', action='store_true')
    essay_find = sub.add_parser('essay-search')
    essay_find.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2')
    essay_find.add_argument('--revision')
    essay_find.add_argument('--min-academic-coverage', type=float, default=0.5)
    essay_find.add_argument('--min-academic-score', type=float, default=0.5)
    unified = sub.add_parser('retrieve')
    unified.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2')
    unified.add_argument('--revision')
    unified.add_argument('--without-essays', action='store_true')
    unified.add_argument('--min-academic-coverage', type=float, default=0.25)
    unified.add_argument('--min-academic-score', type=float, default=0.4)
    unified.add_argument('--no-diagnostics', action='store_true')
    unified.add_argument('--neighbours', type=int, default=7)
    unified.add_argument('--needed-per-group', type=int, default=15)
    unified.add_argument('--weights', type=Path, help='JSON object of positive component weights')
    unified.add_argument('--snapshot-id', help='Use an existing profile snapshot instead of a file')
    find = sub.add_parser('search')
    for find in (find, essay_find, unified):
        if find is unified:
            find.add_argument('file', type=Path, nargs='?', help='JSON query profile; alternatively use --snapshot-id')
        else:
            find.add_argument('file', type=Path, help='JSON query profile')
        find.add_argument('--college', required=True)
        find.add_argument('--cycle', type=int, required=True)
        find.add_argument('--round', required=True, choices=['ED', 'EA', 'RD', 'rolling'])
        find.add_argument('--program', required=True)
        find.add_argument('--residency', required=True)
        find.add_argument('--limit', type=int, default=10)
        find.add_argument('--include-synthetic', action='store_true')
        find.add_argument('--exclude-student-id')
    stage_parser = sub.add_parser('stage')
    stage_parser.add_argument('file', type=Path)
    stage_parser.add_argument('--kind', required=True, choices=['intake-text', 'intake-csv', 'essay', 'freeform', 'pdf'])
    stage_parser.add_argument('--ocr', action='store_true', help='OCR PDF pages with sparse extracted text')
    stage_parser.add_argument('--student-id', required=True)
    stage_parser.add_argument('--batch-id')
    stage_parser.add_argument('--synthetic', action='store_true')
    stage_parser.add_argument('--consent', required=True, choices=['granted', 'synthetic'])
    inspect_parser = sub.add_parser('inspect-intake')
    inspect_parser.add_argument('batch_id')
    review_parser = sub.add_parser('review-field')
    review_parser.add_argument('candidate_id')
    review_parser.add_argument('--status', required=True, choices=['accepted', 'rejected'])
    review_parser.add_argument('--reviewer', required=True)
    publish_parser = sub.add_parser('publish-intake')
    publish_parser.add_argument('batch_id')
    publish_parser.add_argument('--snapshot-id', required=True)
    publish_parser.add_argument('--captured-at', required=True)
    args = parser.parse_args()
    db = connect(args.db)
    try:
        if args.command in ('stage', 'inspect-intake', 'review-field', 'publish-intake'):
            from admissions.intake import stage, stage_document, inspect_batch, review, publish
            if args.command == 'stage':
                if args.kind in ('pdf', 'freeform'):
                    result = stage_document(db, args.file, args.kind, args.student_id, args.synthetic, args.consent, args.batch_id, args.ocr)
                else:
                    result = stage(db, args.file.read_text(), args.file.name, args.kind, args.student_id,
                                   args.synthetic, args.consent, args.batch_id)
            elif args.command == 'inspect-intake':
                result = inspect_batch(db, args.batch_id)
            elif args.command == 'review-field':
                review(db, args.candidate_id, args.status, args.reviewer)
                result = {'candidate_id': args.candidate_id, 'status': args.status}
            else:
                result = publish(db, args.batch_id, args.snapshot_id, args.captured_at)
            print(json.dumps(result, indent=2))
        elif args.command == 'import':
            ingest(db, json.loads(args.file.read_text()))
            print('Import complete.')
        elif args.command == 'index-essays':
            from admissions.essays import LocalEmbedder, index_essays
            print(json.dumps(index_essays(db, LocalEmbedder(args.model, args.revision), args.include_synthetic), indent=2))
        elif args.command == 'essay-search':
            from admissions.essays import LocalEmbedder, essay_search
            result = essay_search(db, json.loads(args.file.read_text()), LocalEmbedder(args.model, args.revision),
                                  args.college, args.cycle, args.round, args.program, args.residency,
                                  args.limit, args.include_synthetic, args.exclude_student_id,
                                  args.min_academic_coverage, args.min_academic_score)
            print(json.dumps(result, indent=2))
        elif args.command == 'retrieve':
            from admissions.retrieval import retrieve
            from admissions.essays import LocalEmbedder, essay_text
            from admissions.core import require
            require(bool(args.file) != bool(args.snapshot_id), 'Provide either a query JSON file or --snapshot-id')
            exclude = args.exclude_student_id
            if args.snapshot_id:
                row = db.execute('SELECT profile_json, student_id FROM snapshots WHERE id=?', (args.snapshot_id,)).fetchone()
                require(row is not None, 'Unknown query snapshot')
                query = json.loads(row['profile_json'])
                exclude = exclude or row['student_id']
            else:
                query = json.loads(args.file.read_text())
            embedder = LocalEmbedder(args.model, args.revision) if essay_text(query) and not args.without_essays else None
            result = retrieve(db, query, args.college, args.cycle, args.round, args.program, args.residency,
                              embedder=embedder, limit=args.limit, include_synthetic=args.include_synthetic,
                              exclude_student_id=exclude, without_essays=args.without_essays,
                              min_academic_coverage=args.min_academic_coverage,
                              min_academic_similarity=args.min_academic_score,
                              weights=json.loads(args.weights.read_text()) if args.weights else None,
                              diagnostics=not args.no_diagnostics, neighbours=args.neighbours, needed=args.needed_per_group)
            print(json.dumps(result, indent=2))
        elif args.command == 'search':
            result = search(db, json.loads(args.file.read_text()), args.college, args.cycle,
                            args.round, args.program, args.residency, args.limit,
                            args.include_synthetic, args.exclude_student_id)
            print(json.dumps(result, indent=2))
        else:
            print('Database initialized.')
    finally:
        db.close()


if __name__ == '__main__':
    main()
