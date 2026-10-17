# SPDX-License-Identifier: Apache-2.0
"""Portable optional inference; dry-run by default. Never loads answer keys."""
import argparse,hashlib,json,os,random,sys,time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import contracts as exam
import fcntl
from contracts import labels, loads
INSTRUCTION='Answer every question in the supplied JSON using its stated mathematical conventions. Return only a JSON object mapping each question ID to its answer: a JSON boolean for type noul, or one of the strings first, second, equal for type choice. Do not return probabilities or explanations in the final JSON. The state and questions follow:\n'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['groq','native'],required=True);ap.add_argument('--model',required=True);ap.add_argument('--endpoint');ap.add_argument('--key-env');ap.add_argument('--effort');ap.add_argument('--full',action='store_true');ap.add_argument('--execute',action='store_true');ap.add_argument('--out',type=Path);ap.add_argument('--max-completion-tokens',type=int,default=8192);ap.add_argument('--resume',action='store_true');ap.add_argument('--interval',type=float,default=2.1);args=ap.parse_args()
 f=ROOT/'data/questions/requests.jsonl';manifest=json.loads((ROOT/'data/manifest.json').read_text())
 for name in ('questions/requests.jsonl','questions/pilot.json'):
  if hashlib.sha256((ROOT/'data'/name).read_bytes()).hexdigest()!=manifest['files'][name]:raise ValueError('Frozen data hash mismatch: '+name)
 records=[loads(line) for line in f.read_text().splitlines()];pilot=loads((ROOT/'data/questions/pilot.json').read_text());ids=set(pilot)
 all_ids=[r['case_id'] for r in records]
 if len(set(all_ids))!=len(all_ids) or len(ids)!=len(pilot) or not ids<=set(all_ids):raise ValueError('Invalid case selection')
 for r in records:
  if set(r)!= {'case_id','payload'} or not isinstance(r['payload']['questions'],dict):raise ValueError('Invalid request record')
  for q in r['payload']['questions'].values():
   if q.get('type') not in ('noul','choice'):raise ValueError('Unsupported question type')
 if not args.full:records=[r for r in records if r['case_id'] in ids]
 random.Random(20261016).shuffle(records)
 endpoint=args.endpoint or ('https://api.groq.com/openai/v1/chat/completions' if args.mode=='groq' else 'http://127.0.0.1:8000/v1/systemone')
 parsed=urlparse(endpoint)
 if parsed.scheme!='https' and not (parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost','::1')):ap.error('Use HTTPS or a loopback server')
 if parsed.username or parsed.password or parsed.query or parsed.fragment:ap.error('Credentials must not be embedded in endpoint URLs')
 config={'model':args.model}
 if args.mode=='groq':config.update(reasoning_effort=args.effort or 'high',reasoning_format='parsed',temperature=.6,top_p=.95,seed=20261016,max_completion_tokens=args.max_completion_tokens,response_format={'type':'json_object'})
 elif args.effort:config['effort']=args.effort
 def body(r):return dict(config,messages=[{'role':'user','content':INSTRUCTION+json.dumps(r['payload'],separators=(',',':'))}]) if args.mode=='groq' else dict(r['payload'],**config)
 if args.interval<0:ap.error('Interval must be nonnegative')
 if not args.execute:
  print(json.dumps({'dry_run':True,'requests':len(records),'configuration':config,'first_request':body(records[0])},indent=2));return 0
 if not args.out:ap.error('--out is required for execution')
 key_env=args.key_env or ('GROQ_API_KEY' if args.mode=='groq' else None);key=os.environ.get(key_env,'') if key_env else ''
 if key_env and not key:ap.error('Required credential environment variable is missing')
 identity={'configuration':config,'mode':args.mode,'endpoint':endpoint,'case_ids':[r['case_id'] for r in records],'data_hashes':{k:manifest['files'][k] for k in ('questions/requests.jsonl','questions/pilot.json')},'runner_sha256':digest(Path(__file__)),'contracts_sha256':digest(ROOT/'contracts.py')}
 args.out.mkdir(parents=True,exist_ok=args.resume)
 with (args.out/'lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  mf=args.out/'manifest.json'
  if args.resume:
   if loads(mf.read_text())!=identity:raise ValueError('Resume configuration/data/code mismatch')
  else:atomic(mf,identity)
  ledger=args.out/'records';ledger.mkdir(exist_ok=True)
  saved={}
  for path in ledger.glob('*.json'):
   value=loads(path.read_text());cid=value['case_id']
   if cid in saved or cid not in identity['case_ids']:raise ValueError('Unexpected or duplicate ledger ID')
   if path.name!=record_name(cid):raise ValueError('Ledger filename mismatch')
   saved[cid]=value
  for record in records:
   cid=record['case_id']
   if cid in saved and saved[cid]['request']!=body(record):raise ValueError('Stored payload mismatch')
   if cid in saved:
    value=saved[cid]
    if value.get('status') not in ('ok','error','dispatching'):raise ValueError('Invalid stored status')
    if value['status']=='ok':
     response=loads(value['raw_response'])
     if response.get('model')!=args.model:raise ValueError('Stored model mismatch')
     if args.mode=='native':
      answers,probabilities=exam.parse(response,body(record))
      if probabilities!=value.get('probabilities'):raise ValueError('Stored probabilities mismatch')
     else:
      if response['choices'][0]['finish_reason']!='stop':raise ValueError('Stored output incomplete')
      answers=labels(response['choices'][0]['message']['content'],record['payload']['questions'])
     if answers!=value.get('answers'):raise ValueError('Stored answers mismatch')
   if cid in saved and saved[cid]['status']=='dispatching':
    saved[cid].update(status='error',error_type='IndeterminateInterruptedRequest')
    atomic(ledger/record_name(cid),saved[cid])
  def summarize():
   ordered=[saved[r['case_id']] for r in records if r['case_id'] in saved]
   atomic_text(args.out/'predictions.jsonl',''.join(json.dumps(r,allow_nan=False)+'\n' for r in ordered))
   valid=sum(r['status']=='ok' for r in ordered);remaining=len(records)-len(ordered)
   report={'expected':len(records),'attempted':len(ordered),'valid':valid,'failed':len(ordered)-valid,'remaining':remaining,'status':'partial' if remaining else ('complete' if valid==len(records) else 'complete_with_errors'),'retry_policy':'never retry attempted or indeterminate cases','sha256_predictions':digest(args.out/'predictions.jsonl')}
   atomic(args.out/'execution.json',report)
   return report
  summarize()
  try:
   for record in records:
    cid=record['case_id']
    if cid in saved:continue
    start=time.perf_counter();payload=body(record)
    result={'case_id':cid,'request':payload,'status':'dispatching'}
    atomic(ledger/record_name(cid),result);saved[cid]=result
    try:
     headers={'Content-Type':'application/json','User-Agent':'strategic-2x2-benchmark'}
     if key:headers['Authorization']='Bearer '+key
     with urlopen(Request(endpoint,json.dumps(payload).encode(),headers),timeout=180) as response:raw=response.read().decode()
     result['raw_response']=raw;v=loads(raw);result['response']=v
     if v.get('model')!=args.model:raise ValueError('Response model mismatch')
     if args.mode=='native':result['answers'],result['probabilities']=exam.parse(v,payload)
     else:
      if v['choices'][0]['finish_reason']!='stop':raise ValueError('Incomplete output')
      result['answers']=labels(v['choices'][0]['message']['content'],record['payload']['questions'])
     result['status']='ok'
    except HTTPError as e:result.update(status='error',http_status=e.code,error_type='HTTPError')
    except Exception as e:result.update(status='error',error_type=type(e).__name__)
    result['elapsed_seconds']=time.perf_counter()-start
    atomic(ledger/record_name(cid),result);summarize()
    if result['status']!='ok':break
    time.sleep(args.interval)
  finally:report=summarize()
  print(json.dumps(report,indent=2))
  return 0 if report['status']=='complete' else 1

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def record_name(cid):return hashlib.sha256(cid.encode()).hexdigest()+'.json'
def atomic_text(path,text):
 temporary=path.with_suffix(path.suffix+'.tmp')
 with temporary.open('w') as f:f.write(text);f.flush();os.fsync(f.fileno())
 os.replace(temporary,path)
 directory=os.open(path.parent,os.O_RDONLY)
 try:os.fsync(directory)
 finally:os.close(directory)
def atomic(path,value):atomic_text(path,json.dumps(value,indent=2,allow_nan=False))
if __name__=='__main__':sys.exit(main())
