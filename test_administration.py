# SPDX-License-Identifier: Apache-2.0
"""Cold-start tests: isolated packages and real local HTTP, no paid inference."""
import hashlib,json,subprocess,sys,tempfile,threading,unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import administer,contracts
ROOT=Path(__file__).resolve().parent

class AdministrationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)/'export';administer.export(self.root)
  rows=[json.loads(x) for x in (self.root/'data/questions/requests.jsonl').read_text().splitlines()][:3]
  self.rows=rows
  (self.root/'data/questions/requests.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
  (self.root/'data/questions/pilot.json').write_text(json.dumps([r['case_id'] for r in rows]))
  mf=self.root/'data/manifest.json';m=json.loads(mf.read_text())
  for name in m['files']:m['files'][name]=hashlib.sha256((self.root/'data'/name).read_bytes()).hexdigest()
  mf.write_text(json.dumps(m));self.calls=[];self.fail=False;owner=self
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_POST(self):
    body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));owner.calls.append(body)
    if owner.fail:response={'model':'wrong'}
    elif 'messages' in body:
     payload=json.loads(body['messages'][0]['content'].split('follow:\n')[1]);response={'model':'test','choices':[{'finish_reason':'stop','message':{'content':json.dumps({k:False for k in payload['questions']})}}]}
    else:response={'model':'test','answers':{k:({'type':'noul','noul':.2} if q['type']=='noul' else {'type':'choice','choice':'first','probabilities':{'first':1,'second':0,'equal':0}}) for k,q in body['questions'].items()}}
    self.send_response(200);self.end_headers();self.wfile.write(json.dumps(response).encode())
  self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
  threading.Thread(target=self.server.serve_forever,daemon=True).start()
  self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
 def run_adapter(self,*extra,mode='native',execute=True):
  cmd=[sys.executable,str(self.root/'adapters/run.py'),'--mode',mode,'--model','test','--endpoint',f'http://127.0.0.1:{self.server.server_port}','--interval','0','--out',str(self.root/'run')]
  if execute:cmd.append('--execute')
  import os
  return subprocess.run(cmd+list(extra),capture_output=True,text=True,env={**os.environ,'GROQ_API_KEY':'local-test-only'})
 def test_export_is_answer_free(self):
  self.assertFalse((self.root/'exam.py').exists());self.assertFalse((self.root/'data/answers').exists());self.assertFalse((self.root/'data/metadata').exists())
  result=self.run_adapter(execute=False);self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(self.calls,[])
 def test_success_and_idempotent_resume(self):
  result=self.run_adapter();self.assertEqual(result.returncode,0,result.stderr)
  self.assertEqual(len(self.calls),3)
  result=self.run_adapter('--resume');self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(len(self.calls),3)
  report=json.loads((self.root/'run/execution.json').read_text());self.assertEqual(report['valid'],3)
 def test_failed_case_is_never_retried(self):
  self.fail=True;result=self.run_adapter();self.assertEqual(result.returncode,1,result.stderr);self.assertEqual(len(self.calls),1)
  self.fail=False;result=self.run_adapter('--resume');self.assertEqual(result.returncode,1,result.stderr);self.assertEqual(len(self.calls),3)
  report=json.loads((self.root/'run/execution.json').read_text());self.assertEqual(report['status'],'complete_with_errors');self.assertEqual(report['failed'],1)
 def test_indeterminate_attempt_is_not_resent(self):
  self.fail=True;self.run_adapter();path=next((self.root/'run/records').glob('*.json'));value=json.loads(path.read_text());value['status']='dispatching';path.write_text(json.dumps(value))
  self.fail=False;result=self.run_adapter('--resume');self.assertEqual(result.returncode,1,result.stderr);self.assertEqual(len(self.calls),3)
  self.assertEqual(json.loads(path.read_text())['error_type'],'IndeterminateInterruptedRequest')
 def test_changed_config_rejected(self):
  self.run_adapter();result=self.run_adapter('--resume','--effort','none');self.assertNotEqual(result.returncode,0);self.assertEqual(len(self.calls),3)
 def test_corrupt_pilot_rejected(self):
  (self.root/'data/questions/pilot.json').write_text('[]');result=self.run_adapter();self.assertNotEqual(result.returncode,0);self.assertEqual(self.calls,[])
 def test_generative_response(self):
  result=self.run_adapter(mode='groq');self.assertEqual(result.returncode,0,result.stderr)
  rows=[json.loads(x) for x in (self.root/'run/predictions.jsonl').read_text().splitlines()];self.assertTrue(all('probabilities' not in r for r in rows))
 def test_run_and_score_full_pilot(self):
  out=Path(self.temp.name)/'graded'
  result=subprocess.run([sys.executable,str(ROOT/'administer.py'),'run','--mode','native','--model','test','--endpoint',f'http://127.0.0.1:{self.server.server_port}','--execute','--interval','0','--out',str(out)],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(len(self.calls),108)
  self.assertTrue((out/'scores.json').is_file())
  self.assertEqual(json.loads((out/'execution.json').read_text())['expected'],108)
 def test_exclusive_lock(self):
  import fcntl
  self.run_adapter()
  with (self.root/'run/lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   result=self.run_adapter('--resume');self.assertNotEqual(result.returncode,0)
  self.assertEqual(len(self.calls),3)
 def test_raw_reparse_detects_tampering(self):
  self.run_adapter();path=next((self.root/'run/records').glob('*.json'));value=json.loads(path.read_text());key=next(iter(value['answers']));value['answers'][key]=True;path.write_text(json.dumps(value))
  result=self.run_adapter('--resume');self.assertNotEqual(result.returncode,0);self.assertEqual(len(self.calls),3)
 def test_strict_json(self):
  for text in ['{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}']:
   with self.assertRaises(ValueError):contracts.loads(text)
if __name__=='__main__':unittest.main()
