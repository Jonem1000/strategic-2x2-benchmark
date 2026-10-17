"""Verify release data, regenerate answers, and reproduce scores without network access."""
from pathlib import Path
import hashlib,json
import exam,score
P=Path(__file__).resolve().parent
manifest=json.loads((P/'data/manifest.json').read_text())
for name,digest in manifest['files'].items():
 assert hashlib.sha256((P/'data'/name).read_bytes()).hexdigest()==digest,name
cases=exam.rows(P/'data/metadata/cases.jsonl');answers=exam.rows(P/'data/answers/answers.jsonl');key={r['case_id']:r['answers'] for r in answers}
assert len(cases)==len(key)==5184
for c in cases:assert exam.reference(c)==exam.independent_reference(c)==key[c['case_id']],c['case_id']
requests=exam.rows(P/'data/questions/requests.jsonl');assert len(requests)==5184
assert {r['case_id']:r['payload'] for r in requests}=={c['case_id']:exam.payload(c) for c in cases}
print('All data hashes and 29,952 reference answers verified.')
for f in sorted((P/'results/predictions').glob('*.jsonl')):
 rows=exam.rows(f);assert len(rows)==len({r['case_id'] for r in rows})==5184
 result=score.score(cases,key,rows);expected=json.loads((P/'results/scores'/f'{f.stem}.json').read_text());assert result==expected,f.stem
 print(f.stem,': exact saved scores reproduced')
