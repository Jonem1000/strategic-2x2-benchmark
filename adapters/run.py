"""Portable optional inference; dry-run by default. Never loads answer keys."""
import argparse,hashlib,json,os,random,sys,time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import exam
INSTRUCTION='Answer every question in the supplied JSON using its stated mathematical conventions. Return only a JSON object mapping each question ID to its answer: a JSON boolean for type noul, or one of the strings first, second, equal for type choice. Do not return probabilities or explanations in the final JSON. The state and questions follow:\n'
def labels(content,questions):
 a=json.loads(content)
 if not isinstance(a,dict) or set(a)!=set(questions):raise ValueError('Answer IDs mismatch')
 for k,q in questions.items():
  if q['type']=='noul':
   if type(a[k]) is not bool:raise ValueError('Expected boolean')
  elif type(a[k]) is not str or a[k] not in ('first','second','equal'):raise ValueError('Expected choice')
 return a

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['groq','native'],required=True);ap.add_argument('--model',required=True);ap.add_argument('--endpoint');ap.add_argument('--key-env');ap.add_argument('--effort');ap.add_argument('--full',action='store_true');ap.add_argument('--execute',action='store_true');ap.add_argument('--out',type=Path);ap.add_argument('--max-completion-tokens',type=int,default=8192);args=ap.parse_args()
 f=ROOT/'data/questions/requests.jsonl';manifest=json.loads((ROOT/'data/manifest.json').read_text())
 assert hashlib.sha256(f.read_bytes()).hexdigest()==manifest['files']['questions/requests.jsonl']
 records=exam.rows(f);ids=set(json.loads((ROOT/'data/questions/pilot.json').read_text()))
 if not args.full:records=[r for r in records if r['case_id'] in ids]
 random.Random(20261016).shuffle(records)
 endpoint=args.endpoint or ('https://api.groq.com/openai/v1/chat/completions' if args.mode=='groq' else 'http://127.0.0.1:8000/v1/systemone')
 parsed=urlparse(endpoint)
 if parsed.scheme!='https' and not (parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost','::1')):ap.error('Use HTTPS or a loopback server')
 if parsed.username or parsed.password:ap.error('Credentials must not be embedded in endpoint URLs')
 config={'model':args.model}
 if args.mode=='groq':config.update(reasoning_effort=args.effort or 'high',reasoning_format='parsed',temperature=.6,top_p=.95,seed=20261016,max_completion_tokens=args.max_completion_tokens,response_format={'type':'json_object'})
 elif args.effort:config['effort']=args.effort
 def body(r):return dict(config,messages=[{'role':'user','content':INSTRUCTION+json.dumps(r['payload'],separators=(',',':'))}]) if args.mode=='groq' else dict(r['payload'],**config)
 if not args.execute:
  print(json.dumps({'dry_run':True,'requests':len(records),'configuration':config,'first_request':body(records[0])},indent=2));return
 if not args.out:ap.error('--out is required for execution')
 key_env=args.key_env or ('GROQ_API_KEY' if args.mode=='groq' else None);key=os.environ.get(key_env,'') if key_env else ''
 if key_env and not key:ap.error('Required credential environment variable is missing')
 args.out.mkdir(parents=True,exist_ok=False)
 (args.out/'manifest.json').write_text(json.dumps({'configuration':config,'mode':args.mode,'requests':len(records),'request_sha256':manifest['files']['questions/requests.jsonl'],'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'retry_policy':'none; stop on first error','timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2))
 with (args.out/'predictions.jsonl').open('w') as output:
  for record in records:
   start=time.perf_counter();payload=body(record);result={'case_id':record['case_id'],'request':payload}
   try:
    headers={'Content-Type':'application/json','User-Agent':'strategic-2x2-benchmark'}
    if key:headers['Authorization']='Bearer '+key
    with urlopen(Request(endpoint,json.dumps(payload).encode(),headers),timeout=180) as response:raw=response.read().decode()
    result['raw_response']=raw;v=json.loads(raw);result['response']=v
    if v.get('model')!=args.model:raise ValueError('Response model mismatch')
    if args.mode=='native':result['answers'],result['probabilities']=exam.parse(v,payload)
    else:
     if v['choices'][0]['finish_reason']!='stop':raise ValueError('Incomplete output')
     result['answers']=labels(v['choices'][0]['message']['content'],record['payload']['questions'])
    result['status']='ok'
   except HTTPError as e:result.update(status='error',http_status=e.code,error_type='HTTPError')
   except Exception as e:result.update(status='error',error_type=type(e).__name__)
   result['elapsed_seconds']=time.perf_counter()-start;output.write(json.dumps(result)+'\n');output.flush()
   if result['status']!='ok':break
   time.sleep(2.1)
if __name__=='__main__':main()
