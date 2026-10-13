"""Recover all-month tables for saved reports from available report-listed exports.

Does not change report-period calculations, source records or member evidence.
"""
import hashlib
import io
import json
import sys
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.data import Dataset
from engine.build import DEEP, SHALLOW
from engine.monthly import capture, saved_history

runs = [p for p in (ROOT / 'runs').iterdir() if (p / 'manifest.json').is_file()]
cache = {}
for run in runs:
    mf = json.loads((run / 'manifest.json').read_text())
    paths = []
    for name in mf.get('sources', []):
        options = [ROOT / 'data/uploaded' / name, ROOT.parent / 'uploads' / name, ROOT.parent / 'google_drive' / name]
        path = next((p for p in options if p.is_file()), None)
        if path:
            paths.append(path)
    signature = (mf['studio'], tuple(str(p) for p in paths))
    if signature not in cache:
        D = Dataset([str(p) for p in paths], log=lambda *args: None)
        print(f'Calculating full history: {mf["studio"]} ({len(paths)} source exports)', flush=True)
        with redirect_stderr(io.StringIO()):
            data = capture(D, mf['studio'], mf['year'], mf['month'], mf['chapters'], DEEP, SHALLOW,
                           lambda line: print(line, flush=True))
        data['source_hashes'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        data['missing_sources'] = [n for n in mf['sources'] if n not in data['source_hashes']]
        data['provenance'] = ('All available source months from available copies of report-listed exports; '
                              'independent of report date filters. Chapters without source exports use saved-report KPIs only. '
                              'Latest source month may be partial.')
        cache[signature] = data
    data = json.loads(json.dumps(cache[signature]))
    history = saved_history(run)
    for cid, ch in history['chapters'].items():
        if cid in data['chapters'] and not data['chapters'][cid]['months']:
            data['chapters'][cid]['months'] = ch['months']
    (run / 'monthly.json').write_text(json.dumps(data, ensure_ascii=False))
    print(f'Saved {run.name}: {len(data["periods"])} months', flush=True)
