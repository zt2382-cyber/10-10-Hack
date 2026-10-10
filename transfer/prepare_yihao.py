"""Prepare a reviewable transfer bundle without modifying the destination repository."""
import shutil
import subprocess
import tempfile
from pathlib import Path

workspace = Path(__file__).resolve().parents[1]
source = Path('/Users/xuyihao/Desktop/10-10-hack')
transfer = workspace / 'transfer'
with tempfile.TemporaryDirectory(prefix='yihao-transfer-') as directory:
    repo = Path(directory) / 'repo'
    shutil.copytree(source, repo, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    def git(*args):
        result = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', *args], cwd=repo, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        return result.stdout.strip()
    git('switch', 'yihao')
    git('merge', '--ff-only', 'yuri')
    target = repo / 'applicant_engine'
    target.mkdir()
    for name in ('admissions', 'tests', 'scripts', 'examples', 'docs'):
        shutil.copytree(workspace / name, target / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('README.md', 'VALIDATION.md', 'pyproject.toml', '.gitignore'):
        shutil.copy2(workspace / name, target / name)
    readme = target / 'README.md'
    readme.write_text('> Run these commands from `applicant_engine/`. This package is self-contained; the Counselor Copilot server and UI are not wired to it yet. Optional dependencies belong to this package only.\n\n' + readme.read_text())
    (target / 'INTEGRATION.md').write_text('''# Applicant retrieval package

The unified SQLite applicant pipeline is self-contained here. Existing Counselor Copilot server, UI, label rules, and standard-library core retain their existing implementation.

Run from applicant_engine/:

```sh
python3 -m unittest discover -s tests -v
python3 -m scripts.validate_pilot
python3 -m admissions.cli --help
```

See README.md for document staging, review, publication, semantic indexing, and unified retrieval. Optional dependencies require Python 3.11+. Real PDF/OCR and embedding inference remain unverified in the source environment.

No hackathon public-post data is imported into SQLite. A future UI adapter must map StudentInput/Result, canonical college/program IDs, admissions cycles, consent, and source provenance explicitly. Missing metadata must not be fabricated. The added package does not replace engine.pipeline or engine.similarity.
''')
    modules = ['tests.'+path.stem for path in sorted((repo/'tests').glob('test_*.py')) if path.stem != 'test_prism']
    commands = [(['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-q'], target),
                (['python3', '-m', 'unittest', *modules, '-q'], repo),
                (['python3', 'tests/acceptance/run_acceptance.py'], repo)]
    logs = ['Full root discovery was attempted separately: 194 tests ran; PRISM setUpClass could not bind its localhost HTTP test server because sandbox networking disallows socket binding. Remaining root modules and acceptance are checked below.']
    for command, cwd in commands:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=60)
        log = 'COMMAND: '+' '.join(command)+'\nDIRECTORY: '+('applicant_engine' if cwd == target else 'repository root')+'\n'+result.stdout+result.stderr
        logs.append(log)
        print(log[-1900:])
        if result.returncode:
            raise RuntimeError(log)
    (transfer/'yihao-validation.txt').write_text('\n\n'.join(logs))
    git('add', 'applicant_engine')
    (transfer/'yihao-applicant-engine.patch').write_text(git('diff', '--cached', '--binary')+'\n')
    git('-c','user.name=Codex','-c','user.email=codex@local','commit','-m','Add unified applicant retrieval and evidence pipeline')
    git('bundle', 'create', str(transfer/'yihao.bundle'), 'yihao', '^yuri')
    git('bundle', 'verify', str(transfer/'yihao.bundle'))
    (transfer/'yihao-commit.txt').write_text(git('rev-parse', 'HEAD')+'\n')
    print('Prepared yihao commit:', git('rev-parse', '--short', 'HEAD'))
