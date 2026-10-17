# SPDX-License-Identifier: Apache-2.0
"""Offline verification, answer-free export, and run-and-score entry point."""
import argparse, hashlib, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def export(destination):
    destination.mkdir(parents=True,exist_ok=False)
    files=['LICENSE','LICENSE.md','contracts.py','adapters/run.py','adapters/README.md','data/questions/requests.jsonl','data/questions/pilot.json']
    files += [str(p.relative_to(ROOT)) for p in (ROOT/'schemas').glob('*.json') if p.name in ('request.schema.json','prediction.schema.json','native-response.schema.json','execution.schema.json','run-manifest.schema.json')]
    for name in files:
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    manifest=json.loads((ROOT/'data/manifest.json').read_text())
    manifest={'version':manifest['version'],'files':{k:v for k,v in manifest['files'].items() if k.startswith('questions/')}}
    (destination/'data/manifest.json').write_text(json.dumps(manifest,indent=2))
    (destination/'README.md').write_text('# Questions-only administration package\n\nPython 3.10+, macOS/Linux. See adapters/README.md. Dry run:\n\n```sh\npython3 adapters/run.py --mode native --model YOUR_MODEL\n```\n\nNo answer key, oracle, scores, or catalogue crosswalk is included. Return the run directory to the administrator for offline grading. Public availability of answers elsewhere means this is operational separation, not a contamination guarantee.\n')
    hashes={str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.rglob('*') if p.is_file()}
    (destination/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2))

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('verify');exp=sub.add_parser('export');exp.add_argument('--out',type=Path,required=True)
    sub.add_parser('run',help='Pass adapter arguments after run')
    args,extra=ap.parse_known_args()
    if args.command=='run':
        manifest=json.loads((ROOT/'data/manifest.json').read_text())
        for name,expected in manifest['files'].items():
            if hashlib.sha256((ROOT/'data'/name).read_bytes()).hexdigest()!=expected:
                raise ValueError('Frozen data hash mismatch: '+name)
        result=subprocess.run([sys.executable,str(ROOT/'adapters/run.py'),*extra])
        if '--execute' in extra and '--out' in extra:
            out=Path(extra[extra.index('--out')+1]);execution=out/'execution.json'
            if execution.exists():
                cmd=[sys.executable,str(ROOT/'score.py'),str(out/'predictions.jsonl'),'--out',str(out/'scores.json')]
                if '--full' not in extra:cmd.append('--pilot')
                scored=subprocess.run(cmd)
                if scored.returncode:return scored.returncode
        return result.returncode
    if extra:ap.error('Unexpected arguments')
    if args.command=='export':export(args.out);return 0
    return subprocess.run([sys.executable,str(ROOT/'reproduce.py')]).returncode
if __name__=='__main__':sys.exit(main())
