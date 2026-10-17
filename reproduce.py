# SPDX-License-Identifier: Apache-2.0
"""Verify release data, regenerate answers, and reproduce scores without network access."""
from pathlib import Path
import hashlib, json
import exam, score
P = Path(__file__).resolve().parent
manifest = json.loads((P / 'data/manifest.json').read_text())
for name, digest in manifest['files'].items():
    if not hashlib.sha256((P / 'data' / name).read_bytes()).hexdigest() == digest:
        raise ValueError(name)
cases = exam.rows(P / 'data/metadata/cases.jsonl')
answers = exam.rows(P / 'data/answers/answers.jsonl')
key = {r['case_id']: r['answers'] for r in answers}
if not len(cases) == len(key) == 5184:
    raise ValueError('Reproduction check failed')
for c in cases:
    if not exam.reference(c) == exam.independent_reference(c) == key[c['case_id']]:
        raise ValueError(c['case_id'])
requests = exam.rows(P / 'data/questions/requests.jsonl')
if not len(requests) == 5184:
    raise ValueError('Reproduction check failed')
if not {r['case_id']: r['payload'] for r in requests} == {c['case_id']: exam.payload(c) for c in cases}:
    raise ValueError('Reproduction check failed')
print('All data hashes and 29,952 reference answers verified.')
for f in sorted((P / 'results/predictions').glob('*.jsonl')):
    rows = exam.rows(f)
    if not len(rows) == len({r['case_id'] for r in rows}) == 5184:
        raise ValueError('Reproduction check failed')
    result = score.score(cases, key, rows)
    expected = json.loads((P / 'results/scores' / f'{f.stem}.json').read_text())
    if not result == expected:
        raise ValueError(f.stem)
    print(f.stem, ': exact saved scores reproduced')
