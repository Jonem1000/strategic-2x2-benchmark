"""Answer-free parsing contract; no oracle or answer-key dependencies."""
import json, math
LABELS=('first','second','equal')
def loads(text):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    def invalid(value): raise ValueError('Nonfinite JSON number')
    return json.loads(text,object_pairs_hook=pairs,parse_constant=invalid)
def labels(content,questions):
 a=loads(content)
 if not isinstance(a,dict) or set(a)!=set(questions):raise ValueError('Answer IDs mismatch')
 for k,q in questions.items():
  if q['type']=='noul':
   if type(a[k]) is not bool:raise ValueError('Expected boolean')
  elif type(a[k]) is not str or a[k] not in ('first','second','equal'):raise ValueError('Expected choice')
 return a


def parse(response,body):
    a=response['answers'];q=body['questions']
    if set(a)!=set(q):raise ValueError('Missing or extra answer IDs')
    labels={};probabilities={}
    for key,question in q.items():
        answer=a[key]
        if answer.get('type')!=question['type']:raise ValueError('Wrong answer type')
        if question['type']=='noul':
            v=answer['noul']
            if type(v) not in (float,int) or not math.isfinite(v) or not 0<=v<=1:raise ValueError('Invalid Noul')
            labels[key]=v>0.5;probabilities[key]={'true':v,'false':1-v}
        else:
            d=answer['probabilities'];chosen=answer['choice']
            if set(d)!=set(LABELS) or chosen not in d:raise ValueError('Invalid choice keys')
            if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in d.values()) or abs(sum(d.values())-1)>.0150001:raise ValueError('Invalid choice distribution')
            if d[chosen]<max(d.values())-1e-8:raise ValueError('Choice does not maximize probability')
            labels[key]=chosen;probabilities[key]={k:v/sum(d.values()) for k,v in d.items()}
    return labels,probabilities
